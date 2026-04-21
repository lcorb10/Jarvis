# modulos/ia_local.py
import requests
from datetime import datetime
from modulos.logger import log
from modulos.memoria import Memoria

class IALocal:
    def __init__(self, modelo="mistral", memoria=None):
        self.modelo = modelo
        self.url = "http://localhost:11434/api/chat"
        self.historial = []
        self.memoria = memoria or Memoria()

    def _construir_sistema(self):
        hora = datetime.now().strftime("%H:%M")
        fecha = datetime.now().strftime("%A %d de %B de %Y")
        preferencias = self.memoria.obtener_preferencias_texto()
        contexto = self.memoria.datos.get("contexto", {})
        contexto_texto = ""
        if contexto:
            ultima_app = contexto.get("ultima_app")
            ultima_accion = contexto.get("ultima_accion")
            if ultima_app:
                contexto_texto = f"Última app abierta: {ultima_app}. "
            if ultima_accion:
                contexto_texto += f"Última acción: {ultima_accion}."

        return f"""Eres Jarvis, un asistente personal de IA inteligente.
REGLAS:
- SIEMPRE responde en español
- Respuestas CORTAS: máximo 2 oraciones para voz
- Eres directo y con personalidad tipo Jarvis de Iron Man
- Hora actual: {hora}, Fecha: {fecha}
{preferencias}
{contexto_texto}"""

    def consultar(self, mensaje):
        self.memoria.incrementar_conversaciones()
        self.historial.append({"role": "user", "content": mensaje})

        payload = {
            "model": self.modelo,
            "messages": [
                {"role": "system", "content": self._construir_sistema()},
                *self.historial[-12:]
            ],
            "stream": False,
            "options": {"temperature": 0.7, "top_p": 0.9}
        }

        try:
            resp = requests.post(self.url, json=payload, timeout=30)
            resp.raise_for_status()
            respuesta = resp.json()["message"]["content"].strip()
            self.historial.append({"role": "assistant", "content": respuesta})
            log.info(f"IA respondió: {respuesta[:60]}...")
            return respuesta
        except requests.exceptions.ConnectionError:
            log.error("Ollama no disponible")
            return "Ollama no está activo."
        except Exception as e:
            log.error(f"Error IA: {e}")
            return f"Error consultando la IA."

    def limpiar_historial(self):
        self.historial = []
        log.info("Historial limpiado")