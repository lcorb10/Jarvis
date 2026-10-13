# modulos/agent/planner.py
"""
Convierte un goal en lenguaje natural a un plan JSON de pasos usando Gemini.
"""
import json
import os
import re
from modulos.logger import log

PLANNER_PROMPT = """Eres el módulo de planificación de Jarvis, asistente personal de IA.
Tu trabajo: convertir cualquier objetivo del usuario en una secuencia de pasos usando SOLO las herramientas disponibles.

REGLAS ABSOLUTAS:
- Máximo 5 pasos. Usa el mínimo necesario.
- Si el objetivo es simple (abrir app, buscar algo), usa 1 solo paso.
- Usa web_search para cualquier información actual o investigación.
- Usa file_controller para guardar resultados a disco.
- NUNCA inventes herramientas que no están en la lista.

HERRAMIENTAS DISPONIBLES:

computer_control
  action: type|click|double_click|hotkey|press|scroll|screenshot|copy|paste|clear_field|focus_window|screen_find|screen_click|wait
  text, x, y, keys, key, direction, amount, seconds, path, description

file_controller
  action: list|write|create_file|create_folder|read|delete|move|copy|rename|find|largest|disk_usage|organize_desktop|info
  path: "desktop"|"downloads"|"documents"|ruta_absoluta
  name: nombre_archivo
  content: contenido

send_message
  receiver: nombre_o_número
  message_text: texto_del_mensaje
  platform: whatsapp|telegram

screen_process
  text: pregunta_sobre_la_pantalla
  angle: screen|camera

code_helper
  action: write|edit|run|explain|build
  description: qué_debe_hacer
  language: python|javascript|html|etc
  output_path: ruta_opcional
  file_path: ruta_existente

game_updater
  action: update|install|list|launch|download_status
  platform: steam|epic|both
  game_name: nombre_del_juego
  app_id: steam_app_id

web_search
  query: término_de_búsqueda
  max_results: número_de_resultados (default 3)

openclaw
  action: search|execute|list
  query: búsqueda_de_tools (para search)
  tool_id: id_de_la_tool (para execute)
  params: parámetros_de_la_tool (para execute)
  category: categoría_opcional (para list)

FORMATO DE SALIDA — solo JSON válido, sin markdown, sin explicaciones:
{
  "goal": "...",
  "steps": [
    {
      "step": 1,
      "tool": "nombre_herramienta",
      "description": "qué hace este paso",
      "parameters": {},
      "critical": true
    }
  ]
}
"""


def create_plan(goal: str) -> dict:
    from modulos.gemini_manager import gemini as _gm_acc
    gm = _gm_acc()

    if not gm.api_key:
        return _fallback_plan(goal)
    puede, motivo = gm.puede_llamar("planner")
    if not puede:
        log.warning(f"[Planner] Gemini bloqueado: {motivo}")
        return _fallback_plan(goal)

    try:
        from google import genai as _genai
        from google.genai import types as _types
        client = _genai.Client(api_key=gm.api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"Objetivo: {goal}",
            config=_types.GenerateContentConfig(system_instruction=PLANNER_PROMPT),
        )
        text = response.text.strip()
        text = re.sub(r"```(?:json)?", "", text).strip().rstrip("`").strip()
        plan = json.loads(text)

        if "steps" not in plan or not isinstance(plan["steps"], list):
            raise ValueError("Plan inválido")

        gm.registrar_llamada("planner", exito=True)
        log.info(f"[Planner] Plan: {len(plan['steps'])} pasos")
        for s in plan["steps"]:
            log.info(f"  Paso {s['step']}: [{s['tool']}] {s['description']}")

        return plan

    except json.JSONDecodeError as e:
        gm.registrar_llamada("planner", exito=False, error=str(e))
        log.warning(f"[Planner] JSON inválido: {e}")
        return _fallback_plan(goal)
    except Exception as e:
        gm.registrar_llamada("planner", exito=False, error=str(e))
        log.error(f"[Planner] Error: {str(e)[:80]}")
        return _fallback_plan(goal)


def replan(goal: str, completed_steps: list, failed_step: dict, error: str) -> dict:
    from modulos.gemini_manager import gemini as _gm_acc
    gm = _gm_acc()
    if not gm.api_key:
        return _fallback_plan(goal)
    puede, motivo = gm.puede_llamar("planner")
    if not puede:
        log.warning(f"[Replan] Gemini bloqueado: {motivo}")
        return _fallback_plan(goal)

    completados_str = "\n".join(
        f"  - Paso {s['step']} ({s['tool']}): COMPLETADO" for s in completed_steps
    )
    prompt = (
        f"Objetivo: {goal}\n\n"
        f"Completados:\n{completados_str or '  (ninguno)'}\n\n"
        f"Paso fallido: [{failed_step.get('tool')}] {failed_step.get('description')}\n"
        f"Error: {error}\n\n"
        "Crea un plan REVISADO solo para el trabajo restante. "
        "No repitas los pasos ya completados."
    )

    try:
        from google import genai as _genai
        from google.genai import types as _types
        client = _genai.Client(api_key=gm.api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=_types.GenerateContentConfig(system_instruction=PLANNER_PROMPT),
        )
        text = response.text.strip()
        text = re.sub(r"```(?:json)?", "", text).strip().rstrip("`").strip()
        plan = json.loads(text)
        gm.registrar_llamada("planner", exito=True)
        log.info(f"[Planner] Replan: {len(plan.get('steps', []))} pasos")
        return plan
    except Exception as e:
        gm.registrar_llamada("planner", exito=False, error=str(e))
        log.error(f"[Planner] Replan error: {str(e)[:80]}")
        return _fallback_plan(goal)


def _fallback_plan(goal: str) -> dict:
    log.info("[Planner] Usando plan de fallback")
    return {
        "goal": goal,
        "steps": [
            {
                "step": 1,
                "tool": "code_helper",
                "description": f"Ejecutar tarea: {goal}",
                "parameters": {"action": "build", "description": goal, "language": "python"},
                "critical": True,
            }
        ],
    }
