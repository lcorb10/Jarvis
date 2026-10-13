# modulos/agent/executor.py
import threading
import time
import os
from typing import Callable
from modulos.logger import log
from modulos.agent.planner import create_plan, replan
from modulos.agent.error_handler import analyze_error, ErrorDecision


def _call_tool(tool: str, parameters: dict, speak: Callable | None) -> str:
    """Despacha al tool correcto."""

    if tool == "computer_control":
        from modulos.tools.computer_control import computer_control
        return computer_control(parameters) or "Hecho."

    elif tool == "file_controller":
        from modulos.tools.file_controller import file_controller
        return file_controller(parameters) or "Hecho."

    elif tool == "send_message":
        from modulos.tools.send_message import send_message
        return send_message(parameters) or "Hecho."

    elif tool == "screen_process":
        from modulos.tools.screen_processor import screen_process
        return screen_process(parameters, speak=speak) or "Análisis de pantalla completado."

    elif tool == "code_helper":
        from modulos.tools.code_helper import code_helper
        return code_helper(parameters, speak=speak) or "Hecho."

    elif tool == "game_updater":
        from modulos.tools.game_updater import game_updater
        return game_updater(parameters, speak=speak) or "Hecho."

    elif tool == "web_search":
        from modulos.tools.web_search import web_search
        return web_search(parameters, speak=speak) or "Sin resultados."

    elif tool == "openclaw":
        from modulos.tools.openclaw import openclaw
        return openclaw(parameters, speak=speak) or "Hecho."

    else:
        # Tool desconocido — intentar con code_helper como fallback
        log.warning(f"[Executor] Tool desconocido '{tool}' — fallback a code_helper")
        from modulos.tools.code_helper import code_helper
        desc = parameters.get("description", str(parameters))
        return code_helper({"action": "build", "description": desc}, speak=speak) or "Hecho."


class AgentExecutor:
    MAX_REPLAN_ATTEMPTS = 2

    def execute(
        self,
        goal: str,
        speak: Callable | None = None,
        cancel_flag: threading.Event | None = None,
    ) -> str:
        log.info(f"[Executor] 🎯 Objetivo: {goal}")

        replan_attempts = 0
        completed_steps = []
        step_results = {}
        plan = create_plan(goal)

        while True:
            steps = plan.get("steps", [])

            if not steps:
                msg = "No pude crear un plan válido para esta tarea, señor."
                if speak:
                    speak(msg)
                return msg

            success = True
            failed_step = None
            failed_error = ""

            for step in steps:
                if cancel_flag and cancel_flag.is_set():
                    if speak:
                        speak("Tarea cancelada, señor.")
                    return "Tarea cancelada."

                step_num = step.get("step", "?")
                tool = step.get("tool", "code_helper")
                desc = step.get("description", "")
                params = dict(step.get("parameters", {}))

                log.info(f"[Executor] ▶️ Paso {step_num}: [{tool}] {desc}")

                attempt = 1
                step_ok = False

                while attempt <= 3:
                    if cancel_flag and cancel_flag.is_set():
                        break
                    try:
                        result = _call_tool(tool, params, speak)
                        step_results[step_num] = result
                        completed_steps.append(step)
                        log.info(f"[Executor] ✅ Paso {step_num}: {str(result)[:80]}")
                        step_ok = True
                        break

                    except Exception as e:
                        error_msg = str(e)
                        log.error(f"[Executor] ❌ Paso {step_num} intento {attempt}: {error_msg}")

                        recovery = analyze_error(step, error_msg, attempt=attempt)
                        decision = recovery["decision"]
                        user_msg = recovery.get("user_message", "")

                        if speak and user_msg:
                            speak(user_msg)

                        if decision == ErrorDecision.RETRY:
                            attempt += 1
                            time.sleep(2)
                            continue

                        elif decision == ErrorDecision.SKIP:
                            log.info(f"[Executor] ⏭️ Saltando paso {step_num}")
                            completed_steps.append(step)
                            step_ok = True
                            break

                        elif decision == ErrorDecision.ABORT:
                            msg = f"Tarea abortada, señor. {recovery.get('reason', '')}"
                            if speak:
                                speak(msg)
                            return msg

                        else:  # REPLAN
                            failed_step = step
                            failed_error = error_msg
                            success = False
                            break

                if not step_ok:
                    if not failed_step:
                        failed_step = step
                        failed_error = "Máximo de reintentos alcanzado"
                    success = False
                    break

            if success:
                return self._summarize(goal, completed_steps, step_results, speak)

            if replan_attempts >= self.MAX_REPLAN_ATTEMPTS:
                msg = f"Tarea fallida tras {replan_attempts} replanes, señor."
                if speak:
                    speak(msg)
                return msg

            if speak:
                speak("Ajustando mi enfoque, señor.")
            replan_attempts += 1
            plan = replan(goal, completed_steps, failed_step, failed_error)

    def _summarize(self, goal: str, completed_steps: list, step_results: dict, speak: Callable | None) -> str:
        from modulos.gemini_manager import gemini as _gm_acc
        gm = _gm_acc()
        fallback = f"Completé {len(completed_steps)} pasos para: {goal[:60]}."
        try:
            if not gm.api_key:
                if speak:
                    speak(fallback)
                return fallback
            puede, _motivo = gm.puede_llamar("chat")
            if not puede:
                if speak:
                    speak(fallback)
                return fallback

            from google import genai as _genai
            client = _genai.Client(api_key=gm.api_key)
            steps_str = "\n".join(f"- {s.get('description', '')}" for s in completed_steps)
            results_str = "\n".join(f"- {r}" for r in list(step_results.values())[:3])
            prompt = (
                f'Objetivo del usuario: "{goal}"\n'
                f"Pasos completados:\n{steps_str}\n"
                f"Resultados:\n{results_str}\n\n"
                "Escribe UNA oración natural en español resumiendo qué se logró. "
                "Llama al usuario 'señor'. Sé directo y positivo."
            )
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            summary = response.text.strip()
            gm.registrar_llamada("chat", exito=True)
            if speak:
                speak(summary)
            return summary
        except Exception as e:
            gm.registrar_llamada("chat", exito=False, error=str(e))
            if speak:
                speak(fallback)
            return fallback
