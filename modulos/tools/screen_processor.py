# modulos/tools/screen_processor.py
"""
Captura y analiza pantalla o cámara usando Gemini Vision.
Requiere: mss, Pillow, google-generativeai
"""
import os
import io
import base64
import time
from pathlib import Path
from modulos.logger import log

try:
    import mss
    import mss.tools
    _MSS = True
except ImportError:
    _MSS = False

try:
    from PIL import Image
    _PIL = True
except ImportError:
    _PIL = False

try:
    import cv2
    _CV2 = True
except ImportError:
    _CV2 = False


def screen_process(parameters: dict, speak=None) -> str:
    from modulos.gemini_manager import gemini as _gm_acc
    gm = _gm_acc()

    question = parameters.get("text", "¿Qué ves en pantalla?")
    angle = parameters.get("angle", "screen").lower()

    if not gm.api_key:
        return "Gemini API key no configurada para visión."

    puede, motivo = gm.puede_llamar("vision")
    if not puede:
        return f"Visión Gemini no disponible: {motivo}"

    if angle == "camera":
        img_data = _capture_camera()
    else:
        img_data = _capture_screen()

    if not img_data:
        return "No pude capturar imagen."

    return _analyze_with_gemini(img_data, question, gm.api_key, speak)


def _capture_screen() -> bytes | None:
    if not _MSS or not _PIL:
        log.error("mss o Pillow no instalados para screen capture")
        return None
    try:
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            sct_img = sct.grab(monitor)
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            # Reducir resolución para Gemini (max 1280px)
            img.thumbnail((1280, 720), Image.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, format="PNG", optimize=True)
            return buf.getvalue()
    except Exception as e:
        log.error(f"Screen capture error: {e}")
        return None


def _capture_camera() -> bytes | None:
    if not _CV2 or not _PIL:
        log.error("cv2 o Pillow no instalados para camera capture")
        return None
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return None
        time.sleep(0.5)  # Warm up
        ret, frame = cap.read()
        cap.release()
        if not ret:
            return None
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        img.thumbnail((1280, 720), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except Exception as e:
        log.error(f"Camera capture error: {e}")
        return None


def _analyze_with_gemini(img_data: bytes, question: str, api_key: str, speak=None) -> str:
    from modulos.gemini_manager import gemini as _gm_acc
    gm = _gm_acc()
    try:
        from google import genai as _genai
        from google.genai import types as _types

        client = _genai.Client(api_key=api_key)
        prompt = (
            f"Eres Jarvis, el asistente de IA de Iron Man. "
            f"El usuario te pregunta: '{question}'. "
            f"Analiza la imagen y responde en español, de forma concisa y directa, "
            f"máximo 3 oraciones, como lo haría Jarvis."
        )
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                _types.Part(text=prompt),
                _types.Part(inline_data=_types.Blob(mime_type="image/png", data=img_data)),
            ],
        )
        resultado = response.text.strip()
        gm.registrar_llamada("vision", exito=True)
        log.info(f"[Vision] {resultado[:80]}...")

        if speak:
            speak(resultado)

        return resultado
    except Exception as e:
        err = str(e)
        gm.registrar_llamada("vision", exito=False, error=err)
        log.error(f"Gemini Vision error: {err[:80]}")
        return f"No pude analizar la imagen: {err[:80]}"
