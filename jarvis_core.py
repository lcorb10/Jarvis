# jarvis_core.py
import threading
import random
from modulos.logger import log
from modulos.memoria import Memoria
from modulos.intenciones import DetectorIntenciones, MODOS, RESPUESTAS_EMOCION
from modulos.detector_aplausos import DetectorAplausos
from modulos.reconocimiento_voz import ReconocimientoVoz
from modulos.ia_local import IALocal
from modulos.sintesis_voz import SintesisVoz
from modulos.control_sistema import ControlSistema
from modulos.detector_rutas import DetectorRutas

class Jarvis:
    def __init__(self):
        log.info("⚙️ Inicializando Jarvis...")

        # Detectar rutas si es primera vez
        self.detector_rutas = DetectorRutas()
        if not self.detector_rutas.config["paths"].get("chrome"):
            log.info("Primera ejecución — detectando aplicaciones...")
            self.detector_rutas.detectar_todas_las_rutas()

        # Verificar Ollama
        ollama_ok = self.detector_rutas.verificar_ollama()
        if not ollama_ok:
            log.warning("Ollama no activo. Ejecuta: ollama serve && ollama pull mistral")

        # Módulos principales
        self.memoria       = Memoria()
        self.tts           = SintesisVoz()
        self.stt           = ReconocimientoVoz()
        self.ia            = IALocal(modelo="mistral", memoria=self.memoria)
        self.control       = ControlSistema()
        self.intenciones   = DetectorIntenciones(self.memoria)
        self.detector      = DetectorAplausos(callback_activacion=self.activar)

        # Estado con lock para evitar condiciones de carrera
        self._lock = threading.Lock()
        self._en_conversacion = False

        log.info("✅ Jarvis listo")

    @property
    def en_conversacion(self):
        with self._lock:
            return self._en_conversacion

    @en_conversacion.setter
    def en_conversacion(self, valor):
        with self._lock:
            self._en_conversacion = valor

    def activar(self):
        if self.en_conversacion:
            return
        self.en_conversacion = True
        log.info("✅ JARVIS ACTIVADO")
        self.tts.hablar("Sí, estoy aquí. ¿En qué puedo ayudarte?")
        self._ciclo_conversacion()

    def _ciclo_conversacion(self):
        intentos_vacios = 0

        while True:
            texto = self.stt.escuchar_comando(timeout=10)

            if not texto:
                intentos_vacios += 1
                if intentos_vacios == 1:
                    self.tts.hablar("¿Sigues ahí?")
                elif intentos_vacios >= 2:
                    self.tts.hablar("Volviendo al modo espera.")
                    break
                continue

            intentos_vacios = 0
            texto_lower = texto.lower().strip()
            log.info(f"Usuario dijo: '{texto}'")

            # Guardar preferencia automáticamente si aplica
            self.memoria.detectar_y_guardar_preferencia(texto)

            # Salir de la conversación
            if any(p in texto_lower for p in [
                "descansa", "hasta luego", "adiós", "adios", "bye", "para"
            ]):
                self.tts.hablar("Descansando. Aplaude dos veces cuando me necesites.")
                break

            # Limpiar historial
            if "limpia el historial" in texto_lower:
                self.ia.limpiar_historial()
                self.tts.hablar("Historial limpiado.")
                continue

            # Detectar intención especial
            intencion = self.intenciones.detectar_intencion(texto)

            if intencion:
                resultado = self._manejar_intencion(intencion, texto)
                if resultado:
                    continue

            # Multi-comando — ya manejado en intenciones
            # Control del sistema
            respuesta_sistema = self.control.interpretar_comando(texto)
            if respuesta_sistema:
                # Actualizar contexto
                if "abriendo" in respuesta_sistema.lower():
                    app = respuesta_sistema.replace("Abriendo", "").replace(".", "").strip()
                    self.memoria.actualizar_contexto("ultima_app", app)
                    self.memoria.actualizar_contexto("ultima_accion", f"abrir {app}")
                self.tts.hablar(respuesta_sistema)
                continue

            # Consultar IA
            log.info("Consultando IA...")
            respuesta = self.ia.consultar(texto)
            if respuesta.startswith("BUSCAR_GOOGLE:"):
                termino = respuesta.replace("BUSCAR_GOOGLE:", "").strip()
                respuesta = self.control.buscar_google(termino)
            self.tts.hablar(respuesta)

        self.en_conversacion = False
        log.info("😴 Jarvis en modo espera")

    def _manejar_intencion(self, intencion, texto_original):
        tipo = intencion["tipo"]

        if tipo == "modo_silencioso":
            if intencion["activar"]:
                self.tts.activar_silencioso()
                self.tts.hablar("Modo silencioso activado.")
            else:
                self.tts.desactivar_silencioso()
                self.tts.hablar("Modo silencioso desactivado.")
            return True

        if tipo == "confirmacion_requerida":
            accion = intencion["accion"]
            self.tts.hablar(f"¿Confirmas que quieres {accion}? Di sí para proceder.")
            return True

        if tipo == "confirmacion_requerida_de_nuevo":
            self.tts.hablar("No entendí. ¿Confirmas la acción? Di sí o no.")
            return True

        if tipo == "confirmado":
            accion = intencion["accion"]
            respuesta = self.control.interpretar_comando(accion)
            self.tts.hablar(respuesta or "Acción ejecutada.")
            return True

        if tipo == "cancelado":
            self.tts.hablar("Acción cancelada.")
            return True

        if tipo == "guardar_memoria":
            guardado = self.memoria.detectar_y_guardar_preferencia(texto_original)
            if guardado:
                self.tts.hablar("Lo recordaré.")
            else:
                self.tts.hablar("Entendido.")
            return True

        if tipo == "consultar_memoria":
            prefs = self.memoria.obtener_preferencias_texto()
            if prefs:
                self.tts.hablar(prefs[:200])
            else:
                self.tts.hablar("Aún no tengo información guardada sobre ti.")
            return True

        if tipo == "emocion":
            emocion = intencion["emocion"]
            respuestas = RESPUESTAS_EMOCION.get(emocion, ["Entiendo."])
            self.tts.hablar(random.choice(respuestas))
            return True

        if tipo == "modo":
            modo = intencion["modo"]
            config_modo = MODOS[modo]
            self.tts.hablar(config_modo["mensaje"])
            for app in config_modo.get("cerrar", []):
                self.control.cerrar_app(app)
            for app in config_modo.get("abrir", []):
                resp = self.control.abrir_app(app)
                log.info(resp)
            return True

        if tipo == "multi_comando":
            comandos = intencion["comandos"]
            for cmd in comandos:
                log.info(f"Ejecutando sub-comando: {cmd}")
                # Primero intentar control del sistema
                resp = self.control.interpretar_comando(cmd)
                if resp:
                    self.tts.hablar(resp)
                else:
                    # Si no es comando del sistema, consultar IA
                    resp = self.ia.consultar(cmd)
                    self.tts.hablar(resp)
            return True

        if tipo == "definir_comando":
            trigger = intencion["trigger"]
            acciones = intencion["acciones"]
            self.memoria.guardar_comando_personalizado(trigger, acciones)
            self.tts.hablar(f"Entendido. Cuando digas {trigger} lo haré.")
            return True

        if tipo == "comando_personalizado":
            acciones = intencion["acciones"]
            for accion in acciones:
                resp = self.control.interpretar_comando(accion)
                if resp:
                    self.tts.hablar(resp)
            return True

        return False

    def iniciar(self):
        self.tts.hablar("Jarvis iniciado. Esperando tu señal.")
        self.detector.escuchar()

if __name__ == "__main__":
    jarvis = Jarvis()
    jarvis.iniciar()