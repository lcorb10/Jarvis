# modulos/agent/error_handler.py
import json
import os
import re
from enum import Enum
from modulos.logger import log


class ErrorDecision(Enum):
    RETRY  = "retry"
    SKIP   = "skip"
    REPLAN = "replan"
    ABORT  = "abort"


ERROR_PROMPT = """Eres el módulo de recuperación de errores de Jarvis.
Un paso ha fallado. Analiza el error y decide qué hacer.

DECISIONES:
- retry  : Error transitorio (timeout, red, bloqueo temporal). Mismo paso puede funcionar al reintentarlo.
- skip   : Este paso no es crítico, la tarea puede completarse sin él.
- replan : El enfoque estaba mal. Se necesita un método diferente.
- abort  : La tarea es fundamentalmente imposible o insegura.

Responde SOLO JSON válido:
{
  "decision": "retry|skip|replan|abort",
  "reason": "por qué falló (1 oración)",
  "fix_suggestion": "qué intentar en su lugar (para replan)",
  "max_retries": 1,
  "user_message": "Mensaje corto para el usuario (máx 10 palabras)"
}"""


def analyze_error(step: dict, error: str, attempt: int = 1, max_attempts: int = 2) -> dict:
    if attempt >= max_attempts:
        log.warning(f"[ErrorHandler] Max intentos alcanzados para paso {step.get('step')} — forzando replan")
        return {
            "decision": ErrorDecision.REPLAN,
            "reason": f"Fallé {attempt} veces: {error[:100]}",
            "fix_suggestion": "Intenta un enfoque diferente",
            "max_retries": 0,
            "user_message": "Ajustando el enfoque, señor.",
        }

    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        return _default_recovery(error)

    try:
        from google import genai as _genai
        from google.genai import types as _types
        client = _genai.Client(api_key=api_key)
        prompt = (
            f"Paso fallido:\n"
            f"Herramienta: {step.get('tool')}\n"
            f"Descripción: {step.get('description')}\n"
            f"Parámetros: {json.dumps(step.get('parameters', {}))}\n"
            f"Crítico: {step.get('critical', False)}\n\n"
            f"Error:\n{error[:400]}\n\n"
            f"Intento número: {attempt}"
        )
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=_types.GenerateContentConfig(system_instruction=ERROR_PROMPT),
        )
        text = response.text.strip()
        text = re.sub(r"```(?:json)?", "", text).strip().rstrip("`").strip()
        result = json.loads(text)

        decision_map = {
            "retry":  ErrorDecision.RETRY,
            "skip":   ErrorDecision.SKIP,
            "replan": ErrorDecision.REPLAN,
            "abort":  ErrorDecision.ABORT,
        }
        result["decision"] = decision_map.get(
            result.get("decision", "replan").lower(),
            ErrorDecision.REPLAN
        )

        # No saltar pasos críticos
        if step.get("critical") and result["decision"] == ErrorDecision.SKIP:
            result["decision"] = ErrorDecision.REPLAN
            result["user_message"] = "Paso crítico — buscando alternativa, señor."

        log.info(f"[ErrorHandler] Decisión: {result['decision'].value} — {result.get('reason', '')}")
        return result

    except Exception as e:
        log.error(f"[ErrorHandler] Análisis falló: {e}")
        return _default_recovery(error)


def _default_recovery(error: str) -> dict:
    is_network = any(k in error.lower() for k in ["timeout", "connection", "network", "refused"])
    decision = ErrorDecision.RETRY if is_network else ErrorDecision.REPLAN
    return {
        "decision": decision,
        "reason": error[:100],
        "fix_suggestion": "Intentar un método alternativo",
        "max_retries": 1,
        "user_message": "Encontré un problema, ajustando, señor.",
    }
