# jarvis_core.py — Jarvis MK2
import threading
import queue
import random
from datetime import datetime
from modulos.logger import log
from modulos.memoria import Memoria
from modulos.intenciones import DetectorIntenciones, MODOS, RESPUESTAS_EMOCION
from modulos.limpiador_texto import limpiar, separar_comandos
from modulos.detector_aplausos import DetectorAplausos
from modulos.reconocimiento_voz import ReconocimientoVoz
from modulos.ia_local import IALocal
from modulos.sintesis_voz import SintesisVoz
from modulos.control_sistema import ControlSistema
from modulos.detector_rutas import DetectorRutas
from modulos.apis.gestor_apis import GestorAPIs
from modulos import aprendizaje

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from modulos.config_manager import get as cfg_get, on_change as cfg_on_change, start_watcher as cfg_start_watcher
from modulos.gemini_manager import gemini as gemini_mgr
from modulos.tools.registry import init_tools, get_registry

# ── Palabras clave que disparan el agente multi-paso ──────────────────────────
_AGENTE_KEYWORDS = [
    "investiga", "investiga y guarda", "busca y guarda",
    "crea un archivo con", "escribe un script", "escribe un programa",
    "organiza", "busca en internet y", "descarga",
    "envía un mensaje", "manda un mensaje",
    "toma una foto de la pantalla", "qué hay en mi pantalla",
    "qué ves en", "analiza la pantalla", "mira la pantalla",
    "actualiza mis juegos", "instala el juego", "instala steam",
    "escribe código", "crea código", "programa", "ejecuta el código",
]

# Palabras de herramientas que la IA puede solicitar en su respuesta JSON
_TOOL_WEB_SEARCH = "web_search"
_TOOL_SCREEN = "screen_process"


class Jarvis:
    def __init__(self, gui_callbacks: dict = None):
        log.info("⚙️ Inicializando Jarvis MK2...")
        self._gui = gui_callbacks or {}

        cfg_start_watcher()

        # Resetear GeminiManager para que relea la API key actual del .env
        # (evita que el singleton quede cacheado con estado de sesión anterior)
        gm = gemini_mgr()
        gm.resetear()
        if gm.api_key:
            gm.verificar_key()

        self.detector_rutas = DetectorRutas()
        if not self.detector_rutas.config["paths"].get("chrome"):
            log.info("Primera ejecución — detectando aplicaciones...")
            self.detector_rutas.detectar_todas_las_rutas()

        ollama_ok = self.detector_rutas.verificar_ollama()
        if not ollama_ok:
            log.warning("Ollama no activo. Ejecuta: ollama serve && ollama pull mistral")

        self.memoria     = Memoria()
        _voz_id = cfg_get("voz", "voz_id") or "edge_gonzalo"
        self.tts         = SintesisVoz(voz_id=_voz_id)
        self.stt         = ReconocimientoVoz()
        # Streaming: parciales de STT van a la GUI mientras el usuario habla
        self.stt.set_callbacks(
            on_partial=lambda t: self._notificar("user_partial", t),
            on_final=lambda t: None,  # final ya se loguea/emite en _ciclo_conversacion
        )
        _modelo_ollama   = cfg_get("ollama", "modelo") or "mistral"
        self.ia          = IALocal(modelo=_modelo_ollama, memoria=self.memoria)
        self.control     = ControlSistema()
        self.intenciones = DetectorIntenciones(self.memoria)
        self.apis        = GestorAPIs()
        self.detector    = DetectorAplausos(callback_activacion=self.activar)

        from modulos.agent.task_queue import get_queue
        self.task_queue = get_queue()

        # Tool registry: la IA decide qué tools invocar
        self.tools = init_tools(self.control, self.apis)
        self.ia.set_tools_registry(self.tools)

        self._lock = threading.Lock()
        self._en_conversacion = False
        self._forzar_descanso = False  # Telegram puede interrumpir conversación activa
        self._timer_liberar_vosk: threading.Timer | None = None
        self._timer_liberar_ollama: threading.Timer | None = None

        # Visibilidad de la GUI: si está oculta, NO hay TTS (solo Telegram texto)
        self.gui_visible = True

        # Cola TTS — habla en segundo plano sin bloquear bridge/telegram
        self._tts_queue: queue.Queue = queue.Queue()
        self._tts_thread = threading.Thread(target=self._tts_worker, daemon=True, name="tts-queue")
        self._tts_thread.start()

        # Vosk emite estados (loading/ready/listening/off) → GUI
        self.stt.set_state_callback(lambda s: self._notificar("vosk_state", s))

        # Reaccionar a cambios en config.json en tiempo real
        cfg_on_change(self._aplicar_config)

        # Aprendizaje automático desde logs
        if cfg_get("aprendizaje", "activo"):
            intervalo = cfg_get("aprendizaje", "intervalo_horas") or 24
            aprendizaje.iniciar_loop(memoria=self.memoria, intervalo_horas=intervalo)

        # Cargar Vosk al inicio para tenerlo listo
        threading.Thread(target=self.stt.precargar, daemon=True).start()
        # Si no hay actividad de voz en 35s tras arranque, Vosk se libera
        self._programar_liberacion_vosk()

        log.info("✅ Jarvis MK2 listo")
        self._notificar("sistema", "Jarvis MK2 inicializado.")

    # ── Cola TTS (habla en background, serializa para no solapar audio) ──────
    def _tts_worker(self):
        while True:
            try:
                item = self._tts_queue.get()
                if item is None:
                    break
                # Verificar gui_visible en el momento de reproducir, no solo al encolar
                if not self.gui_visible:
                    continue
                texto, voz_edge = item
                try:
                    if voz_edge:
                        self.tts.hablar_edge(texto, voz_edge=voz_edge)
                    else:
                        self.tts.hablar(texto)
                except Exception as e:
                    log.warning(f"[TTS worker] error hablando: {e}")
            except Exception as e:
                log.error(f"[TTS worker] {e}")

    def _speak_async(self, texto: str, voz_edge: str | None = None):
        """Encola texto para TTS en background. No bloquea al caller."""
        if not texto or not texto.strip():
            return
        if not self.gui_visible:
            return
        try:
            self._tts_queue.put_nowait((texto, voz_edge))
        except Exception:
            pass

    # ── Visibilidad GUI (controla TTS y persistencia de Vosk) ────────────────
    _timer_gui_debounce: "threading.Timer | None" = None

    def set_gui_visible(self, visible: bool):
        """Llamado por la GUI cuando la ventana se muestra/oculta.
        Debounced: ignora cambios rápidos (Qt emite show/hide múltiples en restaurar).
        - Si visible=True: cancela cualquier liberación de Vosk pendiente y lo recarga
        - Si visible=False: rearma timer normal de Vosk (35s sin voz → libera)
        - TTS solo habla cuando visible=True
        """
        # Cancelar el debounce anterior si llega otro cambio antes de 300ms
        if self._timer_gui_debounce is not None:
            self._timer_gui_debounce.cancel()

        def _aplicar():
            prev = self.gui_visible
            if prev == visible:
                return  # sin cambio real, ignorar
            self.gui_visible = visible
            log.info(f"[GUI] visible={visible} (antes={prev})")
            if visible:
                self._cancelar_liberacion_vosk()
                if not self.stt.esta_cargado():
                    threading.Thread(target=self.stt.precargar, daemon=True).start()
            else:
                self._programar_liberacion_vosk()

        self._timer_gui_debounce = threading.Timer(0.3, _aplicar)
        self._timer_gui_debounce.daemon = True
        self._timer_gui_debounce.start()

    # ── Gestión de Vosk (carga/liberación diferida, SOLO con actividad de voz)
    def _programar_liberacion_vosk(self, delay: int = 35):
        """Libera SOLO Vosk de RAM tras `delay`s sin actividad de voz.
        Si la GUI está visible, NO libera (Vosk debe estar siempre listo)."""
        if self._timer_liberar_vosk:
            self._timer_liberar_vosk.cancel()
        def _liberar():
            if self.gui_visible:
                # GUI visible: re-postergar; usuario podría hablar en cualquier momento
                self._programar_liberacion_vosk(delay)
                return
            try:
                self.stt._liberar_modelo()
                log.info(f"[Vosk] Modelo liberado por inactividad de voz ({delay}s)")
            except Exception:
                pass
        self._timer_liberar_vosk = threading.Timer(delay, _liberar)
        self._timer_liberar_vosk.daemon = True
        self._timer_liberar_vosk.start()

    def _cancelar_liberacion_vosk(self):
        if self._timer_liberar_vosk:
            self._timer_liberar_vosk.cancel()
            self._timer_liberar_vosk = None

    # ── Gestión de Ollama (timer independiente — cualquier actividad la activa)
    def _programar_liberacion_ollama(self, delay: int = 35):
        """Libera SOLO Ollama de RAM tras `delay`s sin actividad (voz O texto)."""
        if self._timer_liberar_ollama:
            self._timer_liberar_ollama.cancel()
        def _liberar():
            try:
                self._descargar_ollama()
            except Exception:
                pass
        self._timer_liberar_ollama = threading.Timer(delay, _liberar)
        self._timer_liberar_ollama.daemon = True
        self._timer_liberar_ollama.start()

    def _cancelar_liberacion_ollama(self):
        if self._timer_liberar_ollama:
            self._timer_liberar_ollama.cancel()
            self._timer_liberar_ollama = None

    # ── Gestión de memoria Ollama ─────────────────────────────────────────────
    def _descargar_ollama(self):
        """Envía keep_alive=0 a Ollama para que libere el modelo de RAM."""
        try:
            import requests as _req
            modelo = cfg_get("ollama", "modelo") or "mistral"
            _req.post(
                "http://localhost:11434/api/chat",
                json={"model": modelo, "messages": [], "keep_alive": 0},
                timeout=5,
            )
            log.info(f"[Ollama] Modelo '{modelo}' descargado de RAM")
        except Exception:
            pass

    # ── Hot-reload config ─────────────────────────────────────────────────────
    def _aplicar_config(self, cfg: dict):
        try:
            modelo = cfg.get("ollama", {}).get("modelo", "llama3")
            if modelo and modelo != self.ia.modelo_ollama:
                self.ia.modelo_ollama = modelo
                log.info(f"[Config] Modelo Ollama → {modelo}")

            motor_default = cfg.get("orquestador", {}).get("default", "ollama")
            self.ia.motor = motor_default

            umbral = cfg.get("orquestador", {}).get("umbral_complejidad", 6)
            self.ia.UMBRAL_COMPLEJIDAD = umbral

            voz_id = cfg.get("voz", {}).get("voz_id", "")
            if voz_id and voz_id != self.tts.voz_actual_id():
                self.tts.set_voz(voz_id)

            silencioso = cfg.get("voz", {}).get("modo_silencioso", False)
            if silencioso:
                self.tts.activar_silencioso()
            else:
                self.tts.desactivar_silencioso()

            log.info("[Config] Configuración aplicada en tiempo real")
        except Exception as e:
            log.error(f"[Config] Error aplicando config: {e}")

    # ── GUI callbacks ──────────────────────────────────────────────────────────
    def _notificar(self, tipo: str, texto: str):
        fn = self._gui.get(f"on_{tipo}")
        if fn:
            try:
                fn(texto)
            except Exception:
                pass

    # ── Estado ────────────────────────────────────────────────────────────────
    @property
    def en_conversacion(self):
        with self._lock:
            return self._en_conversacion

    @en_conversacion.setter
    def en_conversacion(self, valor):
        with self._lock:
            self._en_conversacion = valor

    # ── TTS con GUI ───────────────────────────────────────────────────────────
    def hablar(self, texto: str):
        if not texto:
            return
        self._notificar("jarvis_response", texto)
        self._notificar("state_change", "hablando")
        self.tts.hablar(texto)
        self._notificar("state_change", "esperando")

    # ── Bienvenida personalizada ──────────────────────────────────────────────
    def _generar_bienvenida(self) -> str:
        hora = datetime.now().hour
        if hora < 12:
            saludo = "Buenos días"
        elif hora < 19:
            saludo = "Buenas tardes"
        else:
            saludo = "Buenas noches"

        # Clima de Barranquilla (no bloqueante, con fallback)
        clima_txt = ""
        try:
            for api in self.apis.apis:
                if api.nombre == "clima":
                    res = api._obtener_clima("barranquilla")
                    # Extraer solo temp y descripción: "En Barranquilla: nublado, 28°C..."
                    partes = res.replace("En Barranquilla: ", "").split(",")
                    if partes:
                        clima_txt = f"El clima en Barranquilla es {partes[0].strip()}"
                        if len(partes) > 1:
                            clima_txt += f", {partes[1].strip()}"
                        clima_txt += "."
                    break
        except Exception:
            pass

        # Contexto de memoria: última app usada, preferencias
        ctx = self.memoria.datos.get("contexto", {})
        ultima_app = ctx.get("ultima_app", "")

        # Pool de preguntas contextuales según última app o hora
        sugerencias_por_app = {
            "spotify":    "¿Quiere continuar con algo de música?",
            "discord":    "¿Abrimos Discord para hablar con alguien?",
            "valorant":   "¿Listo para otra partida de Valorant?",
            "league":     "¿Vamos a League of Legends?",
            "vscode":     "¿Continuamos con el proyecto de programación?",
            "chrome":     "¿Necesita buscar algo en internet?",
            "youtube":    "¿Quiere ver algo en YouTube?",
            "brawlhalla": "¿Otra sesión de Brawlhalla?",
        }

        sugerencias_hora = {
            range(6, 9):   "¿Le preparo el resumen de noticiás de hoy?",
            range(9, 13):  "¿En qué trabajamos esta mañana?",
            range(13, 16): "¿Qué hacemos esta tarde?",
            range(16, 20): "¿Una sesión de juegos o música para la tarde?",
            range(20, 24): "¿Música para relajarse o algo que revisar?",
            range(0, 6):   "Es tarde, señor. ¿Todo bien?",
        }

        pregunta = sugerencias_por_app.get(ultima_app.lower(), "")
        if not pregunta:
            for rango, sug in sugerencias_hora.items():
                if hora in rango:
                    pregunta = sug
                    break

        # Construir mensaje final
        partes = [f"{saludo}, señor."]
        if clima_txt:
            partes.append(clima_txt)
        if pregunta:
            partes.append(pregunta)

        return " ".join(partes)

    # ── Activación ────────────────────────────────────────────────────────────
    def activar(self):
        if self.en_conversacion:
            return
        # Pausar detector de aplausos mientras usamos el mic para STT
        self.detector.pausar()
        # Voz activa: cancelar ambos timers (Vosk + Ollama deben quedarse cargados)
        self._cancelar_liberacion_vosk()
        self._cancelar_liberacion_ollama()
        self.en_conversacion = True
        log.info("✅ JARVIS ACTIVADO")
        bienvenida = self._generar_bienvenida()
        self.hablar(bienvenida)
        self._ciclo_conversacion()

    # ── Procesado de texto ────────────────────────────────────────────────────
    def _procesar_texto(self, texto_raw: str) -> list[str]:
        comandos = separar_comandos(texto_raw)
        return [limpiar(c) for c in comandos if limpiar(c)]

    def _es_tarea_agente(self, texto: str) -> bool:
        texto_lower = texto.lower()
        return any(kw in texto_lower for kw in _AGENTE_KEYWORDS)

    # ── Despacho de tools solicitadas por la IA ───────────────────────────────
    # Tools cuyo resultado se devuelve al usuario tal cual (acciones del sistema)
    _TOOLS_ACCION_DIRECTA = {
        "open_app", "close_app", "youtube_search", "google_search",
        "spotify_play", "volume", "weather", "math", "translate",
        "create_file", "create_folder", "read_file", "list_files",
    }
    # Tools cuyo resultado debe re-consultarse con la IA para resumen natural
    _TOOLS_CONTEXTO_IA = {"web_search", "screen_process", "news"}

    def _ejecutar_tools_ia(self, tools: list) -> tuple[list[str], list[str]]:
        """
        Ejecuta las tools que la IA pidió. Devuelve:
          - resultados_directos: salidas de tools de acción (a leer al usuario)
          - resultados_contexto: salidas que requieren resumen de la IA
        """
        directos, contexto = [], []
        for tool_entry in tools:
            if ":" in tool_entry:
                tool_name, _, tool_param = tool_entry.partition(":")
            else:
                tool_name, tool_param = tool_entry, ""

            tool_name = tool_name.strip()
            tool_param = tool_param.strip()

            if tool_name not in self.tools.names():
                log.warning(f"[Core] Tool IA desconocida: {tool_name}")
                continue

            log.info(f"[Core] ▶ tool: {tool_name}({tool_param!r})")
            result = self.tools.call(tool_name, tool_param)
            if not result:
                continue

            if tool_name in self._TOOLS_CONTEXTO_IA:
                contexto.append(result)
            else:
                directos.append(result)
                # actualizar contexto memoria
                if tool_name == "open_app":
                    self.memoria.actualizar_contexto("ultima_app", tool_param)
                self.memoria.actualizar_contexto("ultima_accion", f"{tool_name}:{tool_param[:30]}")

        return directos, contexto

    # ── Preguntas de hora/fecha — respuesta directa sin IA (evita caché) ────────
    _RE_HORA = None
    _RE_FECHA = None

    def _respuesta_hora_directa(self, texto_lower: str) -> str | None:
        """Devuelve la hora/fecha actual sin pasar por la IA para evitar caché."""
        palabras_hora = ["qué hora", "que hora", "dime la hora", "hora es", "hora actual",
                         "qué horas", "que horas", "hora tienes", "hora son"]
        palabras_fecha = ["qué día", "que dia", "qué fecha", "que fecha", "día de hoy",
                          "fecha de hoy", "qué día es", "que dia es"]
        if any(p in texto_lower for p in palabras_hora):
            return f"Son las {datetime.now().strftime('%H:%M')}, señor."
        if any(p in texto_lower for p in palabras_fecha):
            dias = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
            meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
                     "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
            now = datetime.now()
            return (f"Hoy es {dias[now.weekday()]} {now.day} de "
                    f"{meses[now.month - 1]} de {now.year}, señor.")
        return None

    # ── Comando principal ─────────────────────────────────────────────────────
    def _ejecutar_comando(self, texto: str) -> str:
        self.memoria.detectar_y_guardar_preferencia(texto)

        # 0. Hora/fecha: responder directamente sin IA para evitar respuesta cacheada
        resp_hora = self._respuesta_hora_directa(texto.lower().strip())
        if resp_hora:
            return resp_hora

        # 1. Intenciones especiales (modo silencioso, dormir, cambio de motor, etc)
        #    Estas SÍ se quedan ANTES de la IA porque son meta-comandos del sistema.
        intencion = self.intenciones.detectar_intencion(texto)
        if intencion:
            resultado = self._manejar_intencion(intencion, texto)
            if resultado is not None:
                return resultado

        # 2. Tarea agente (multi-paso largo) — solo keywords muy explícitas
        if self._es_tarea_agente(texto):
            log.info(f"[Core] → Agente: {texto}")
            self.task_queue.submit(goal=texto, speak=self.hablar)
            return "Entendido. Ejecutando la tarea en segundo plano, señor."

        # 3. IA es el cerebro: analiza el comando y decide qué tools usar
        log.info(f"[Core] → IA analiza: {texto!r}")
        self._notificar("state_change", "pensando")
        data = self.ia.consultar_con_tools(texto)

        tools = data.get("tools", [])
        respuesta = data.get("respuesta", "").strip()

        # 4. Despachar tools (puede ser 0, 1, o varias en paralelo conceptual)
        if tools:
            log.info(f"[Core] IA solicitó tools: {tools}")
            directos, contexto = self._ejecutar_tools_ia(tools)

            # Si hubo contexto que necesita resumen, re-consultar IA
            if contexto:
                ctx_text = "\n".join(contexto)[:1500]
                respuesta_final = self.ia.consultar(
                    f"Información obtenida:\n{ctx_text}\n\n"
                    f"Pregunta original del usuario: {texto}\n"
                    f"Responde de forma natural y corta."
                )
                if directos:
                    return f"{respuesta} {respuesta_final}".strip()
                return respuesta_final

            # Solo acciones directas: combinar respuesta IA + resultados
            if directos:
                # Si la IA ya generó una respuesta natural, úsala. Si no, concatena.
                if respuesta and len(respuesta) > 10:
                    return respuesta
                return ". ".join(directos)

        # 5. Sin tools: la IA solo conversó
        return respuesta or "Entendido, señor."

    # ── Ciclo de conversación ─────────────────────────────────────────────────
    def _ciclo_conversacion(self):
        intentos_vacios = 0

        while True:
            # Telegram puede pedir descanso aunque estemos en conversación activa
            if self._forzar_descanso:
                self._forzar_descanso = False
                break

            self._notificar("state_change", "escuchando")
            texto_raw = self.stt.escuchar_comando(timeout=20)

            if self._forzar_descanso:
                self._forzar_descanso = False
                break

            if not texto_raw:
                intentos_vacios += 1
                if intentos_vacios == 2:
                    self.hablar("¿Sigue ahí, señor?")
                if intentos_vacios >= 4:
                    self.hablar("Volviendo al modo espera, señor.")
                    break
                continue

            intentos_vacios = 0
            self._notificar("user_speech", texto_raw)
            self._notificar("state_change", "procesando")
            log.info(f"Usuario: '{texto_raw}'")

            texto_lower = texto_raw.lower().strip()

            _PALABRAS_DESCANSO = [
                "descansa", "descanse", "hasta luego", "adiós", "adios", "bye",
                "puedes descansar", "ya es todo", "apágate", "apagate",
                "modo espera", "ponte en espera", "eso es todo",
                "gracias jarvis", "gracias ya",
            ]
            if any(p in texto_lower for p in _PALABRAS_DESCANSO):
                self.hablar("Descansando, señor. Aplauda dos veces cuando me necesite.")
                break

            if "limpia el historial" in texto_lower or "borra el historial" in texto_lower:
                self.ia.limpiar_historial()
                self.hablar("Historial limpiado.")
                continue

            comandos = self._procesar_texto(texto_raw)
            log.info(f"Comandos: {comandos}")

            if len(comandos) == 1:
                respuesta = self._ejecutar_comando(comandos[0])
                if respuesta:
                    self.hablar(respuesta)
            else:
                self.hablar(f"Ejecutando {len(comandos)} acciones, señor.")
                respuestas = []
                for cmd in comandos:
                    resp = self._ejecutar_comando(cmd)
                    if resp:
                        respuestas.append(resp)
                        if any(k in resp.lower() for k in ["error", "no pude", "no encontré"]):
                            self.hablar(resp)
                exitosos = len([r for r in respuestas if "error" not in r.lower()])
                self.hablar(f"Completé {exitosos} de {len(comandos)} acciones.")

        self.en_conversacion = False
        self._notificar("state_change", "esperando")
        log.info("😴 Jarvis en modo espera")
        # Reactivar detector de aplausos ahora que el mic queda libre
        self.detector.reanudar()
        # Tras voz, ambos liberan tras 35s (Vosk + Ollama)
        self._programar_liberacion_vosk()
        self._programar_liberacion_ollama()

    # ── Envío de archivos por Telegram ───────────────────────────────────────
    _RE_ENVIO = None  # compilado lazy

    _TRIGGERS_ENVIO = [
        "comprime y envíame", "comprime y enviame",
        "comprimir y enviar", "comprime y manda", "comprime y mandame",
        "envíame el archivo", "enviame el archivo",
        "mándame el archivo", "mandame el archivo",
        "envíame", "enviame", "mándame", "mandame",
    ]

    def _es_comando_envio_archivo(self, texto_lower: str) -> bool:
        return any(t in texto_lower for t in self._TRIGGERS_ENVIO)

    def _preparar_envio_archivo(self, texto: str) -> str:
        """
        Extrae el nombre del archivo del texto, lo busca en el PC y devuelve
        un tag especial '__send_file__:ruta' que el bot de Telegram intercepta
        para comprimir y enviar. Si hay múltiples coincidencias pregunta cuál.
        """
        try:
            import re as _re

            texto_lower = texto.lower().strip()

            # Quitar el trigger para quedarnos con el nombre del archivo
            nombre_query = texto_lower
            for trigger in sorted(self._TRIGGERS_ENVIO, key=len, reverse=True):
                if trigger in nombre_query:
                    nombre_query = nombre_query.replace(trigger, "").strip()
                    break
            # Limpiar artículos y preposiciones comunes al inicio
            nombre_query = _re.sub(
                r"^(el|la|los|las|un|una|ese|esa|este|esta|de|del|archivo|fichero)\s+",
                "", nombre_query
            ).strip()
            # Limpiar también al final: "que está en el escritorio", "del escritorio"
            nombre_query = _re.sub(
                r"\s+(que\s+est[aá]|en\s+el|del|de\s+mi)\s+\w+$",
                "", nombre_query
            ).strip()

            # Detectar frases que piden "el más parecido" sin nombre concreto
            _frases_similares = [
                "mas parecido", "más parecido", "el más", "el mas",
                "mas similar", "más similar", "parecido", "similar",
                "busca", "revisa", "escritorio", "desktop",
            ]
            es_query_vago = (
                not nombre_query or
                all(p in nombre_query for p in _frases_similares[:1]) or
                len(nombre_query.split()) <= 1 and nombre_query in
                {"escritorio", "desktop", "busca", "revisa", "archivo"}
            )

            if es_query_vago or not nombre_query:
                # Listar los archivos más recientes del Desktop para que el usuario elija
                from pathlib import Path as _Path
                desktop = _Path.home() / "Desktop"
                archivos = sorted(
                    [p for p in desktop.iterdir() if p.is_file()],
                    key=lambda p: p.stat().st_mtime, reverse=True
                )[:8]
                if not archivos:
                    return "No encontré archivos en el escritorio. ¿Cuál archivo quiere que le envíe?"
                opciones = "\n".join(
                    f"{i+1}. {p.name}  ({p.stat().st_size // 1024} KB)"
                    for i, p in enumerate(archivos)
                )
                return (f"Estos son los archivos más recientes del escritorio. ¿Cuál quiere?\n\n"
                        f"{opciones}\n\nResponda con el número.")

            # Buscar usando la lógica del bridge
            from bridge_server import _find_files
            encontrados = _find_files(nombre_query)

            if not encontrados:
                # Segundo intento: solo la primera palabra como query más amplio
                primera_palabra = nombre_query.split()[0] if nombre_query.split() else ""
                if primera_palabra and primera_palabra != nombre_query:
                    encontrados = _find_files(primera_palabra)

            if not encontrados:
                return (f"No encontré ningún archivo con el nombre '{nombre_query}'. "
                        f"Revise el nombre e intente de nuevo.")

            if len(encontrados) == 1:
                p = encontrados[0]
                log.info(f"[Archivo→Telegram] encontrado: {p}")
                return f"__send_file__:{p}"

            # Múltiples coincidencias — preguntar cuál
            opciones = "\n".join(
                f"{i+1}. {p.name}  ({p.stat().st_size // 1024} KB)  — {p.parent}"
                for i, p in enumerate(encontrados)
            )
            return (f"Encontré varios archivos parecidos. ¿Cuál quiere que le envíe?\n\n"
                    f"{opciones}\n\nResponda con el número.")
        except Exception as e:
            log.error(f"[Archivo→Telegram] error: {e}")
            return f"Tuve un error buscando el archivo: {e}"

    # ── Entrada externa (Telegram bridge) ─────────────────────────────────────
    # Palabras que desde Telegram ponen a Jarvis en modo espera (sin hablar ni procesar IA)
    _PALABRAS_DESCANSO_TELEGRAM = [
        "descansa", "descanse", "hasta luego", "adiós", "adios", "bye",
        "puedes descansar", "ya es todo", "apágate", "apagate",
        "modo espera", "ponte en espera", "eso es todo",
        "gracias jarvis", "gracias ya",
    ]

    def ejecutar_para_telegram(self, texto: str, speak: bool = False) -> str:
        """
        Punto de entrada para el bridge HTTP (Telegram).

        Reglas de TTS:
          - speak=True solo se honra si la GUI está visible (gui_visible)
          - Si GUI cerrada → silencio total en el PC, solo respuesta a Telegram
          - El "mensaje entrante" se lee con voz Edge MASCULINA (Jorge MX)
            para distinguirlo del Jarvis principal
          - La respuesta de Jarvis usa la voz configurada (puede ser Gemini)

        NO toca el timer de Vosk (texto no extiende vida de Vosk).
        Solo extiende vida de Ollama (modelo IA usado para texto).
        """
        try:
            self._cancelar_liberacion_ollama()
        except Exception:
            pass

        log.info(f"[Telegram] solicitud: {texto!r} (speak={speak}, gui_visible={self.gui_visible})")

        # Si Jarvis ya está respondiendo por voz, solo permite comandos de descanso
        if self.en_conversacion:
            if any(p in texto_lower for p in self._PALABRAS_DESCANSO_TELEGRAM):
                log.info("[Telegram] comando de descanso forzando salida de conversación activa")
                self._forzar_descanso = True
                respuesta = "Descansando, señor. Aplauda dos veces cuando me necesite."
                if bool(speak and self.gui_visible):
                    self._speak_async(respuesta)
                return respuesta
            log.info("[Telegram] ignorado — Jarvis en conversación activa por voz")
            return "Jarvis está en conversación activa. Intente en un momento."

        texto_lower = texto.lower().strip()

        # Detectar "comprime y envíame" — responde con tag especial que el bot procesa
        if self._es_comando_envio_archivo(texto_lower):
            return self._preparar_envio_archivo(texto)

        # Detectar comandos de descanso sin pasar por la IA
        if any(p in texto_lower for p in self._PALABRAS_DESCANSO_TELEGRAM):
            log.info("[Telegram] comando de descanso recibido")
            respuesta = "Descansando, señor. Aplauda dos veces cuando me necesite."
            debe_hablar = bool(speak and self.gui_visible)
            if debe_hablar:
                self._speak_async(respuesta)
            try:
                self._programar_liberacion_ollama()
            except Exception:
                pass
            return respuesta

        debe_hablar = bool(speak and self.gui_visible)

        # Encolar el "mensaje entrante" — NO bloquea, voz Edge Jorge MX
        if debe_hablar:
            self._speak_async(f"Mensaje de Sebastian: {texto}", voz_edge="es-MX-JorgeNeural")

        try:
            respuesta = self._ejecutar_comando(texto)
        except Exception as e:
            log.error(f"[Telegram] error en _ejecutar_comando: {e}")
            respuesta = f"Error procesando el comando: {e}"

        # Encolar la respuesta de Jarvis (voz configurada). NO bloquea.
        # Telegram recibe `respuesta` inmediatamente; el TTS se reproduce en background.
        if debe_hablar and respuesta:
            self._speak_async(respuesta)

        try:
            self._programar_liberacion_ollama()
        except Exception:
            pass

        return respuesta or "Hecho."

    # ── Manejador de intenciones ──────────────────────────────────────────────
    def _manejar_intencion(self, intencion: dict, texto_original: str):
        tipo = intencion["tipo"]

        if tipo == "modo_silencioso":
            if intencion["activar"]:
                self.tts.activar_silencioso()
                return "Modo silencioso activado."
            else:
                self.tts.desactivar_silencioso()
                return "Modo silencioso desactivado."

        if tipo == "cambiar_ia":
            ia = intencion["ia"]
            self.ia.motor = ia
            if ia == "gemini":
                return "Cambiando a Gemini. Diga 'ollama' para volver al modo local."
            return "Motor IA cambiado a Ollama, señor."

        if tipo == "cambiar_voz":
            motor = intencion["motor"]
            voz_default = "gemini_charon" if motor == "gemini" else "edge_gonzalo"
            if self.tts.set_voz(voz_default):
                return f"Voz cambiada a {motor}, señor."
            return f"No pude cambiar a la voz de {motor}."

        if tipo == "confirmacion_requerida":
            accion = intencion["accion"]
            self.hablar(f"¿Confirma que quiere {accion}? Diga sí para proceder.")
            return ""

        if tipo == "confirmado":
            return self.control.interpretar_comando(intencion["accion"]) or "Acción ejecutada."

        if tipo == "cancelado":
            return "Acción cancelada."

        if tipo == "limpiar_historial":
            self.ia.limpiar_historial()
            return "Historial limpiado."

        if tipo == "guardar_memoria":
            guardado = self.memoria.detectar_y_guardar_preferencia(texto_original)
            return "Lo recordaré, señor." if guardado else "Entendido."

        if tipo == "consultar_memoria":
            prefs = self.memoria.obtener_preferencias_texto()
            mem = self.memoria.obtener_memoria_larga_texto()
            respuesta = prefs + ("\n" + mem if mem else "")
            return respuesta[:300] if respuesta else "Aún no tengo información guardada sobre usted."

        if tipo == "emocion":
            emocion = intencion["emocion"]
            respuestas = RESPUESTAS_EMOCION.get(emocion, ["Entiendo, señor."])
            return random.choice(respuestas)

        if tipo == "modo":
            modo = intencion["modo"]
            config_modo = MODOS[modo]
            for app in config_modo.get("cerrar", []):
                self.control.cerrar_app(app)
            for app in config_modo.get("abrir", []):
                self.control.abrir_app(app)
            return config_modo["mensaje"]

        if tipo == "multi_comando":
            comandos = intencion["comandos"]
            for cmd in comandos:
                resp = self._ejecutar_comando(cmd)
                if resp:
                    self.hablar(resp)
            return ""

        if tipo == "definir_comando":
            trigger = intencion["trigger"]
            acciones = intencion["acciones"]
            self.memoria.guardar_comando_personalizado(trigger, acciones)
            return f"Entendido. Cuando diga '{trigger}' lo ejecutaré."

        if tipo == "comando_personalizado":
            acciones = intencion["acciones"]
            for accion in acciones:
                resp = self.control.interpretar_comando(accion)
                if resp:
                    self.hablar(resp)
            return ""

        return None

    # ── Inicio ────────────────────────────────────────────────────────────────
    def iniciar(self):
        self.hablar("Jarvis MK2 iniciado. Esperando su señal, señor.")
        # Si en 35s no hay actividad de voz, Vosk libera RAM
        self._programar_liberacion_vosk()
        self.detector.escuchar()
