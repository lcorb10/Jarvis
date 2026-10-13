# modulos/ia_local.py
import json
import re
import requests
import time
from datetime import datetime
from modulos.logger import log
from modulos.memoria import Memoria
from modulos.gemini_manager import gemini as gemini_mgr


class IALocal:
    """
    Motor de IA de Jarvis.
    - Default: Gemini 2.5 Flash (rápido, ~1s, sin RAM local)
    - Fallback: Ollama/mistral (offline, si Gemini no disponible o sin internet)
    """

    def __init__(self, modelo="mistral", memoria: Memoria = None):
        self.modelo_ollama = modelo
        self.url_ollama = "http://localhost:11434/api/chat"
        self.historial = []
        self.memoria = memoria or Memoria()
        self.max_reintentos = 1
        self.tools_desc = ""
        self._tool_names: set = set()
        self._motor = "gemini"  # default: Gemini

        self._gm = gemini_mgr()
        self.gemini_key = self._gm.api_key

        try:
            from modulos.config_manager import get as cfg_get
            self.modelo_gemini = cfg_get("gemini", "modelo_chat") or "gemini-2.5-flash"
        except Exception:
            self.modelo_gemini = "gemini-2.5-flash"

        self.gemini_ok = bool(self.gemini_key)
        if self.gemini_ok:
            log.info(f"✅ Motor IA: Gemini ({self.modelo_gemini}) — Ollama como fallback")
        else:
            self._motor = "ollama"
            log.warning("Sin GEMINI_API_KEY — usando Ollama como motor principal")

    # ── Motor ──────────────────────────────────────────────────────────────────
    @property
    def motor(self):
        return self._motor

    @motor.setter
    def motor(self, valor):
        if valor == "gemini" and not self.gemini_ok:
            log.warning("Gemini no disponible — manteniendo Ollama")
            return
        self._motor = valor
        log.info(f"Motor IA → {valor}")

    # ── Tools registry ─────────────────────────────────────────────────────────
    def set_tools_registry(self, registry):
        self.tools_desc = registry.list_for_prompt()
        self._tool_names = set(registry.names())
        log.info(f"[IALocal] {len(self._tool_names)} tools en prompt")

    # ── System prompt ──────────────────────────────────────────────────────────
    def _construir_sistema(self) -> str:
        hora = datetime.now().strftime("%H:%M")
        ctx = self.memoria.datos.get("contexto", {})
        prefs = self.memoria.obtener_preferencias_texto()

        ctx_txt = ""
        if ctx.get("ultima_app"):
            ctx_txt = f"Última app: {ctx['ultima_app']}."

        tools_block = f"\nTOOLS:\n{self.tools_desc}\n" if self.tools_desc else ""

        return (
            f"Eres Jarvis, asistente IA personal tipo Iron Man. Hora: {hora}.\n"
            "IDIOMA: español latinoamericano. Jamás uses 'vosotros', 'estáis', 'tenéis'. Usa: 'están', 'tienen', 'ustedes'.\n"
            "PERSONALIDAD: inteligente, servicial, directo. Trata al usuario de 'señor'. "
            "Para comandos de acción: respuestas breves (1-2 oraciones). "
            "Para preguntas, conversación o contenido creativo (poemas, historias, explicaciones): responde completo y natural, sin límite artificial de longitud.\n"
            "IMPORTANTE: NUNCA digas que no puedes hacer algo que sí puedes. Puedes recitar poemas, contar chistes, hablar de cualquier tema, explicar conceptos, escribir textos creativos, etc.\n"
            "NO INVENTES estado del sistema: si no sabes si una app está abierta, di que ejecutaste la acción.\n"
            f"{prefs}{ctx_txt}"
            f"{tools_block}"
            "ANÁLISIS: lee TODO el comando antes de actuar. Si hay varias acciones, usa multi-tool.\n"
            "REGLA create_file: argumento = 'nombre.txt|contenido'. Usa \\n para saltos de línea.\n"
            "EJEMPLOS:\n"
            '"abre discord" → {"tools":["open_app:discord"],"respuesta":"Abriendo Discord, señor."}\n'
            '"coloca musica relajante en youtube" → {"tools":["youtube_search:musica relajante"],"respuesta":"Reproduciendo música relajante en YouTube, señor."}\n'
            '"pon bad bunny en spotify" → {"tools":["spotify_play:bad bunny"],"respuesta":"Buscando Bad Bunny en Spotify, señor."}\n'
            '"reproduce una canción" → {"tools":[],"respuesta":"¿Qué canción o artista quiere reproducir, señor?"}\n'
            '"pon música" → {"tools":[],"respuesta":"¿Qué música quiere escuchar, señor? Puede decirme el artista o canción."}\n'
            '"abre google y busca algo" → {"tools":["google_search:algo"],"respuesta":"Buscando en Google, señor."}\n'
            '"sube el volumen" → {"tools":["volume:subir"],"respuesta":"Subiendo el volumen, señor."}\n'
            '"recita un poema" → {"tools":[],"respuesta":"Claro, señor:\\n\\nRoses are red...\\n..."}\n'
            '"hola" → {"tools":[],"respuesta":"Hola señor, ¿en qué puedo ayudarle?"}\n'
            "REGLA CRÍTICA: NUNCA llames spotify_play o youtube_search con argumento vacío. Si el usuario no especificó qué reproducir, pregúntale primero.\n"
            "FORMATO ESTRICTO — siempre JSON válido y completo: {\"tools\":[...],\"respuesta\":\"...\"}\n"
            "Usa SOLO tools de la lista. Nunca inventes nombres de tools."
        )

    # ── Consulta principal ─────────────────────────────────────────────────────
    def consultar(self, mensaje: str) -> str:
        self.memoria.incrementar_conversaciones()
        self.historial.append({"role": "user", "content": mensaje})
        raw = self._consultar_con_fallback(mensaje)
        if not raw.startswith("ERROR"):
            self.historial.append({"role": "assistant", "content": raw})
        return self._parsear_respuesta(raw)

    def consultar_con_tools(self, mensaje: str) -> dict:
        try:
            self.memoria.incrementar_conversaciones()
            self.historial.append({"role": "user", "content": mensaje})
            raw = self._consultar_con_fallback(mensaje)
            if not raw.startswith("ERROR"):
                self.historial.append({"role": "assistant", "content": raw})
            return self._parsear_json_completo(raw)
        except Exception as e:
            log.error(f"[IA] Error: {e}")
            return {"tools": [], "respuesta": "Error interno, señor."}

    # ── Lógica de fallback ─────────────────────────────────────────────────────
    def _consultar_con_fallback(self, mensaje: str) -> str:
        """Gemini primero, Ollama si Gemini falla o está sin cuota."""
        usar_gemini = self._motor == "gemini" and self.gemini_ok and self._gm.disponible

        if usar_gemini:
            puede, motivo = self._gm.puede_llamar("chat")
            if puede:
                resultado = self._consultar_gemini(mensaje)
                if not resultado.startswith("ERROR"):
                    return resultado
                log.warning(f"[IA] Gemini falló → fallback Ollama: {resultado[:60]}")
            else:
                log.warning(f"[IA] Gemini no disponible ({motivo}) → Ollama")

        return self._consultar_ollama()

    # ── Parsers ────────────────────────────────────────────────────────────────
    def _parsear_respuesta(self, raw: str) -> str:
        return self._parsear_json_completo(raw).get("respuesta", raw)

    def _parsear_json_completo(self, raw: str) -> dict:
        try:
            text = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
            data = json.loads(text)
            if isinstance(data, dict) and "respuesta" in data:
                tools_validas = [
                    t for t in data.get("tools", [])
                    if isinstance(t, str) and t.split(":")[0].strip() in self._tool_names
                ] if self._tool_names else data.get("tools", [])
                data["tools"] = tools_validas
                return data
        except Exception:
            pass

        match = re.search(r'\{[^{}]*"respuesta"\s*:[^{}]*\}', raw, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(0))
                if isinstance(data, dict) and "respuesta" in data:
                    tools_validas = [
                        t for t in data.get("tools", [])
                        if isinstance(t, str) and t.split(":")[0].strip() in self._tool_names
                    ] if self._tool_names else data.get("tools", [])
                    data["tools"] = tools_validas
                    return data
            except Exception:
                pass

        if raw.strip().startswith("{"):
            log.warning(f"[IA] JSON inválido descartado: {raw[:80]}")
            return {"tools": [], "respuesta": "Entendido, señor."}

        return {"tools": [], "respuesta": raw}

    # ── Gemini ─────────────────────────────────────────────────────────────────
    def _consultar_gemini(self, mensaje: str) -> str:
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.gemini_key)

            contents = []
            for msg in self.historial[-7:-1]:
                role = "user" if msg["role"] == "user" else "model"
                contents.append(types.Content(role=role, parts=[types.Part(text=msg["content"])]))
            contents.append(types.Content(role="user", parts=[types.Part(text=mensaje)]))

            response = client.models.generate_content(
                model=self.modelo_gemini,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=self._construir_sistema(),
                    temperature=0.5,
                    max_output_tokens=800,
                ),
            )
            texto = response.text.strip()
            self._gm.registrar_llamada("chat", exito=True)
            log.info(f"[Gemini] {texto[:60]}...")
            return texto
        except Exception as e:
            err = str(e)
            self._gm.registrar_llamada("chat", exito=False, error=err)
            log.error(f"[Gemini] Error: {err[:80]}")
            return f"ERROR_GEMINI: {err[:80]}"

    # ── Ollama (fallback offline) ───────────────────────────────────────────────
    def _consultar_ollama(self) -> str:
        payload = {
            "model": self.modelo_ollama,
            "messages": [
                {"role": "system", "content": self._construir_sistema()},
                *self.historial[-6:],
            ],
            "stream": False,
            "options": {
                "temperature": 0.5,
                "top_p": 0.9,
                "num_predict": 150,
            },
        }
        for intento in range(self.max_reintentos + 1):
            try:
                resp = requests.post(self.url_ollama, json=payload, timeout=30)
                if resp.status_code == 500:
                    if intento < self.max_reintentos:
                        time.sleep(1)
                        continue
                    return "ERROR_OLLAMA: error 500"
                resp.raise_for_status()
                texto = resp.json()["message"]["content"].strip()
                log.info(f"[Ollama-fallback] {texto[:60]}...")
                return texto
            except requests.exceptions.ConnectionError:
                return "ERROR_OLLAMA: Ollama no activo"
            except requests.exceptions.Timeout:
                if intento < self.max_reintentos:
                    continue
                return "ERROR_OLLAMA: timeout"
            except Exception as e:
                return f"ERROR_OLLAMA: {e}"
        return "ERROR_OLLAMA: reintentos agotados"

    # ── Gemini directo (agente/planner) ───────────────────────────────────────
    def consultar_gemini_directo(self, prompt: str, sistema: str = "") -> str:
        if not self.gemini_ok:
            return "Gemini no configurado."
        puede, motivo = self._gm.puede_llamar("chat")
        if not puede:
            return f"Gemini no disponible: {motivo}"
        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=self.gemini_key)
            response = client.models.generate_content(
                model=self.modelo_gemini,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=sistema or self._construir_sistema(),
                    temperature=0.5,
                    max_output_tokens=800,
                ),
            )
            self._gm.registrar_llamada("chat", exito=True)
            return response.text.strip()
        except Exception as e:
            err = str(e)
            self._gm.registrar_llamada("chat", exito=False, error=err)
            log.error(f"[Gemini directo] Error: {err[:80]}")
            return f"Error Gemini: {err[:80]}"

    def limpiar_historial(self):
        self.historial = []
        log.info("Historial limpiado")
