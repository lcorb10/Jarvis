# modulos/tools/code_helper.py
"""
Escribe, edita, explica y ejecuta código usando Gemini.
"""
import subprocess
import sys
import os
import re
import time
import tempfile
from pathlib import Path
from modulos.logger import log

DESKTOP = Path.home() / "Desktop"
MAX_FIX_ATTEMPTS = 3
GEMINI_MODEL = "gemini-2.5-flash"

EXT_MAP = {
    "python": ".py", "py": ".py",
    "javascript": ".js", "js": ".js",
    "typescript": ".ts", "html": ".html",
    "css": ".css", "java": ".java",
    "cpp": ".cpp", "c": ".c",
    "bash": ".sh", "powershell": ".ps1",
    "sql": ".sql", "json": ".json",
}


class _GeminiWrapper:
    """Wrapper mínimo para usar el nuevo SDK con la misma interfaz que el viejo."""
    def __init__(self, client, model_name):
        self._client = client
        self._model = model_name

    def generate_content(self, prompt):
        return self._client.models.generate_content(model=self._model, contents=prompt)


def _get_gemini():
    from google import genai as _genai
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY no configurada.")
    client = _genai.Client(api_key=api_key)
    return _GeminiWrapper(client, GEMINI_MODEL)


def _clean_code(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
    text = re.sub(r"\n?```$", "", text)
    return text.strip()


def _resolve_output(output_path: str, language: str) -> Path:
    ext = EXT_MAP.get((language or "python").lower(), ".py")
    if output_path:
        p = Path(output_path)
        return p if p.is_absolute() else DESKTOP / p
    return DESKTOP / f"jarvis_code{ext}"


def code_helper(parameters: dict, speak=None) -> str:
    action = parameters.get("action", "auto").lower()
    description = parameters.get("description", "")
    language = parameters.get("language", "python")
    output_path = parameters.get("output_path", "")
    file_path = parameters.get("file_path", "")
    code = parameters.get("code", "")
    timeout = int(parameters.get("timeout", 30))

    if action in ("write", "auto") and description:
        return _write_code(description, language, output_path, speak)
    elif action == "run":
        target = file_path or output_path
        return _run_code(target, language, timeout, speak)
    elif action == "explain":
        src = code or (Path(file_path).read_text(encoding="utf-8") if file_path else "")
        return _explain_code(src, speak)
    elif action == "edit":
        return _edit_code(file_path, description, speak)
    elif action == "build":
        return _build_and_run(description, language, output_path, timeout, speak)
    else:
        return f"Acción desconocida: {action}"


def _write_code(description: str, language: str, output_path: str, speak=None) -> str:
    if speak:
        speak("Escribiendo el código, señor.")
    try:
        model = _get_gemini()
        prompt = (
            f"Escribe código {language} completo y funcional para:\n{description}\n\n"
            "Reglas:\n"
            "- Código limpio y bien comentado en español\n"
            "- Incluye manejo de errores\n"
            "- Solo el código, sin explicaciones, sin markdown\n"
        )
        resp = model.generate_content(prompt)
        codigo = _clean_code(resp.text)
        save_path = _resolve_output(output_path, language)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        save_path.write_text(codigo, encoding="utf-8")
        log.info(f"Código guardado: {save_path}")
        return f"Código guardado en: {save_path}"
    except Exception as e:
        log.error(f"code write error: {e}")
        return f"Error escribiendo código: {e}"


def _run_code(file_path: str, language: str, timeout: int, speak=None) -> str:
    if not file_path:
        return "Ruta de archivo requerida."
    path = Path(file_path)
    if not path.exists():
        path = DESKTOP / file_path
    if not path.exists():
        return f"Archivo no encontrado: {file_path}"

    if speak:
        speak("Ejecutando el código, señor.")
    try:
        result = subprocess.run(
            [sys.executable, str(path)],
            capture_output=True, text=True,
            timeout=timeout, cwd=str(DESKTOP)
        )
        if result.returncode == 0:
            output = result.stdout.strip()
            return f"Ejecutado correctamente.\n{output[:500]}" if output else "Ejecutado sin errores."
        else:
            error = result.stderr.strip()
            return f"Error de ejecución:\n{error[:300]}"
    except subprocess.TimeoutExpired:
        return f"Tiempo de ejecución agotado ({timeout}s)."
    except Exception as e:
        return f"Error ejecutando: {e}"


def _explain_code(code: str, speak=None) -> str:
    if not code:
        return "No hay código que explicar."
    try:
        model = _get_gemini()
        prompt = (
            f"Explica este código de forma clara y concisa en español:\n\n{code[:3000]}"
        )
        resp = model.generate_content(prompt)
        return resp.text.strip()
    except Exception as e:
        return f"Error explicando código: {e}"


def _edit_code(file_path: str, description: str, speak=None) -> str:
    if not file_path:
        return "Ruta de archivo requerida."
    path = Path(file_path)
    if not path.exists():
        path = DESKTOP / file_path
    if not path.exists():
        return f"Archivo no encontrado: {file_path}"

    original = path.read_text(encoding="utf-8")
    try:
        model = _get_gemini()
        prompt = (
            f"Modifica este código para: {description}\n\n"
            f"Código original:\n{original[:3000]}\n\n"
            "Devuelve solo el código modificado completo, sin explicaciones."
        )
        resp = model.generate_content(prompt)
        nuevo_codigo = _clean_code(resp.text)
        path.write_text(nuevo_codigo, encoding="utf-8")
        return f"Código editado: {path.name}"
    except Exception as e:
        return f"Error editando código: {e}"


def _build_and_run(description: str, language: str, output_path: str, timeout: int, speak=None) -> str:
    """Escribe código, lo guarda y lo ejecuta automáticamente."""
    write_result = _write_code(description, language, output_path, speak)
    if "Error" in write_result:
        return write_result
    # Extraer ruta guardada
    save_path = write_result.replace("Código guardado en: ", "").strip()
    if speak:
        speak("Ejecutando el código generado.")
    return _run_code(save_path, language, timeout, speak)
