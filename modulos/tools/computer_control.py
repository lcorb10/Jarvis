# modulos/tools/computer_control.py
"""
Control directo del PC: mouse, teclado, screenshots, búsqueda visual en pantalla.
Requiere: pyautogui, pyperclip, Pillow, mss
"""
import subprocess
import sys
import time
import json
import re
import os
from pathlib import Path
from modulos.logger import log

try:
    import pyautogui
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.05
    _PYAUTOGUI = True
except ImportError:
    _PYAUTOGUI = False
    log.warning("pyautogui no instalado — computer_control limitado")

try:
    import pyperclip
    _PYPERCLIP = True
except ImportError:
    _PYPERCLIP = False


def _req_pyautogui():
    if not _PYAUTOGUI:
        raise RuntimeError("PyAutoGUI no instalado. Ejecuta: pip install pyautogui")


def computer_control(parameters: dict) -> str:
    action = parameters.get("action", "").lower()

    if action == "type":
        return _type(parameters.get("text", ""), parameters.get("clear_first", False))
    elif action == "click":
        return _click(parameters.get("x"), parameters.get("y"))
    elif action == "double_click":
        return _double_click(parameters.get("x"), parameters.get("y"))
    elif action == "right_click":
        return _right_click(parameters.get("x"), parameters.get("y"))
    elif action == "hotkey":
        return _hotkey(parameters.get("keys", ""))
    elif action == "press":
        return _press(parameters.get("key", ""))
    elif action == "scroll":
        return _scroll(parameters.get("direction", "down"), parameters.get("amount", 3))
    elif action == "move":
        return _move(parameters.get("x"), parameters.get("y"))
    elif action == "screenshot":
        return _screenshot(parameters.get("path"))
    elif action == "copy":
        return _copy()
    elif action == "paste":
        return _paste(parameters.get("text"))
    elif action == "clear_field":
        return _clear_field()
    elif action == "focus_window":
        return _focus_window(parameters.get("title", ""))
    elif action == "screen_find":
        return _screen_find(parameters.get("description", ""))
    elif action == "screen_click":
        return _screen_click(parameters.get("description", ""))
    elif action == "wait":
        return _wait(parameters.get("seconds", 1))
    elif action == "get_mouse_pos":
        return _get_mouse_pos()
    elif action == "write_clipboard":
        return _write_clipboard(parameters.get("text", ""))
    else:
        return f"Acción desconocida: {action}"


# ── Implementaciones ───────────────────────────────────────────────────────────

def _type(text: str, clear_first: bool = False) -> str:
    _req_pyautogui()
    if not text:
        return "No hay texto que escribir."
    if clear_first:
        pyautogui.hotkey("ctrl", "a")
        time.sleep(0.1)
    if _PYPERCLIP:
        pyperclip.copy(text)
        time.sleep(0.1)
        pyautogui.hotkey("ctrl", "v")
    else:
        pyautogui.write(text, interval=0.03)
    return f"Escribí: {text[:50]}"


def _click(x, y) -> str:
    _req_pyautogui()
    if x is None or y is None:
        return "Coordenadas requeridas para click."
    pyautogui.click(int(x), int(y))
    return f"Click en ({x}, {y})."


def _double_click(x, y) -> str:
    _req_pyautogui()
    if x is None or y is None:
        return "Coordenadas requeridas."
    pyautogui.doubleClick(int(x), int(y))
    return f"Doble click en ({x}, {y})."


def _right_click(x, y) -> str:
    _req_pyautogui()
    if x is None or y is None:
        return "Coordenadas requeridas."
    pyautogui.rightClick(int(x), int(y))
    return f"Click derecho en ({x}, {y})."


def _hotkey(keys: str) -> str:
    _req_pyautogui()
    if not keys:
        return "Teclas requeridas."
    partes = [k.strip() for k in keys.replace("+", " ").split()]
    pyautogui.hotkey(*partes)
    return f"Atajo: {keys}"


def _press(key: str) -> str:
    _req_pyautogui()
    if not key:
        return "Tecla requerida."
    pyautogui.press(key)
    return f"Tecla presionada: {key}"


def _scroll(direction: str, amount: int = 3) -> str:
    _req_pyautogui()
    clicks = int(amount) if direction == "down" else -int(amount)
    pyautogui.scroll(clicks)
    return f"Scroll {direction} {amount} unidades."


def _move(x, y) -> str:
    _req_pyautogui()
    if x is None or y is None:
        return "Coordenadas requeridas."
    pyautogui.moveTo(int(x), int(y), duration=0.3)
    return f"Mouse movido a ({x}, {y})."


def _screenshot(path: str = None) -> str:
    _req_pyautogui()
    if not path:
        path = str(Path.home() / "Desktop" / "jarvis_screenshot.png")
    screenshot = pyautogui.screenshot()
    screenshot.save(path)
    return f"Screenshot guardado en: {path}"


def _copy() -> str:
    _req_pyautogui()
    pyautogui.hotkey("ctrl", "c")
    time.sleep(0.2)
    if _PYPERCLIP:
        texto = pyperclip.paste()
        return f"Copiado: {texto[:100]}"
    return "Copiado al portapapeles."


def _paste(text: str = None) -> str:
    _req_pyautogui()
    if text and _PYPERCLIP:
        pyperclip.copy(text)
        time.sleep(0.1)
    pyautogui.hotkey("ctrl", "v")
    return "Pegado."


def _clear_field() -> str:
    _req_pyautogui()
    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.05)
    pyautogui.press("delete")
    return "Campo limpiado."


def _focus_window(title: str) -> str:
    if not title:
        return "Título de ventana requerido."
    try:
        result = subprocess.run(
            ["powershell", "-c",
             f'(Get-Process | Where-Object {{$_.MainWindowTitle -like "*{title}*"}} | Select-Object -First 1).MainWindowHandle'],
            capture_output=True, text=True, timeout=5
        )
        handle = result.stdout.strip()
        if handle and handle.isdigit():
            subprocess.run(
                ["powershell", "-c",
                 f'Add-Type -Name W -MemberDefinition "[DllImport(\'user32.dll\')] public static extern bool SetForegroundWindow(int h);" -Namespace F; [F.W]::SetForegroundWindow({handle})'],
                capture_output=True, timeout=5
            )
            return f"Ventana '{title}' enfocada."
    except Exception as e:
        log.error(f"focus_window error: {e}")
    return f"No encontré ventana: {title}"


def _screen_find(description: str) -> str:
    """Busca un elemento en pantalla usando Gemini Vision"""
    if not description:
        return "Descripción requerida."
    try:
        import mss
        import mss.tools
        from PIL import Image
        import base64
        import io

        with mss.mss() as sct:
            monitor = sct.monitors[1]
            sct_img = sct.grab(monitor)
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            img = img.resize((1280, 720))
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            img_b64 = base64.b64encode(buf.getvalue()).decode()

        gemini_key = os.getenv("GEMINI_API_KEY", "")
        if not gemini_key:
            return "Gemini no configurado para búsqueda visual."

        from google import genai as _genai
        from google.genai import types as _types
        import base64 as _b64
        client = _genai.Client(api_key=gemini_key)
        prompt = (
            f"Encuentra '{description}' en la pantalla. "
            "Responde SOLO con las coordenadas X,Y del centro del elemento "
            f"en una pantalla de {img.width}x{img.height} píxeles. "
            "Formato: X,Y — solo números, sin texto extra."
        )
        img_bytes = buf.getvalue()
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                _types.Part(text=prompt),
                _types.Part(inline_data=_types.Blob(mime_type="image/png", data=img_bytes)),
            ],
        )
        coords_text = response.text.strip()
        match = re.search(r'(\d+)[,\s]+(\d+)', coords_text)
        if match:
            x, y = int(match.group(1)), int(match.group(2))
            # Escalar de 1280x720 a resolución real
            scale_x = sct_img.width / 1280
            scale_y = sct_img.height / 720
            real_x, real_y = int(x * scale_x), int(y * scale_y)
            return f"Elemento encontrado en ({real_x}, {real_y})."
        return "No encontré el elemento en pantalla."
    except Exception as e:
        log.error(f"screen_find error: {e}")
        return f"Error buscando en pantalla: {e}"


def _screen_click(description: str) -> str:
    """Encuentra y hace click en un elemento descrito en lenguaje natural"""
    resultado = _screen_find(description)
    match = re.search(r'\((\d+),\s*(\d+)\)', resultado)
    if match:
        x, y = int(match.group(1)), int(match.group(2))
        return _click(x, y)
    return resultado


def _wait(seconds) -> str:
    time.sleep(float(seconds))
    return f"Esperé {seconds} segundos."


def _get_mouse_pos() -> str:
    _req_pyautogui()
    x, y = pyautogui.position()
    return f"Mouse en ({x}, {y})."


def _write_clipboard(text: str) -> str:
    if not text:
        return "Texto requerido."
    if _PYPERCLIP:
        pyperclip.copy(text)
        return f"Portapapeles actualizado: {text[:50]}"
    return "pyperclip no disponible."
