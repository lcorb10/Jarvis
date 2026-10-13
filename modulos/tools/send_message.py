# modulos/tools/send_message.py
"""
Envía mensajes por WhatsApp Web o Telegram Web usando el navegador.
Requiere: pyautogui, pyperclip
"""
import subprocess
import time
import urllib.parse
from modulos.logger import log

try:
    import pyautogui
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.1
    _PYAUTOGUI = True
except ImportError:
    _PYAUTOGUI = False

try:
    import pyperclip
    _PYPERCLIP = True
except ImportError:
    _PYPERCLIP = False

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"


def send_message(parameters: dict) -> str:
    receiver = parameters.get("receiver", "").strip()
    message = parameters.get("message_text", "").strip()
    platform = parameters.get("platform", "whatsapp").lower().strip()

    if not receiver:
        return "Receptor requerido."
    if not message:
        return "Mensaje requerido."

    if platform in ("whatsapp", "wa"):
        return _send_whatsapp(receiver, message)
    elif platform in ("telegram", "tg"):
        return _send_telegram(receiver, message)
    else:
        return f"Plataforma no soportada: {platform}. Usa 'whatsapp' o 'telegram'."


def _send_whatsapp(receiver: str, message: str) -> str:
    """Abre WhatsApp Web con el mensaje prellenado via URL scheme"""
    if not _PYAUTOGUI:
        return "PyAutoGUI no instalado. Abre WhatsApp manualmente."

    # Método 1: URL directa con número (si el receptor es número)
    if receiver.replace("+", "").replace(" ", "").isdigit():
        numero = receiver.replace("+", "").replace(" ", "").replace("-", "")
        msg_encoded = urllib.parse.quote(message)
        url = f"https://wa.me/{numero}?text={msg_encoded}"
        try:
            subprocess.Popen([CHROME, url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(3)
            log.info(f"WhatsApp abierto para número {numero}")
            return f"WhatsApp abierto para {receiver}. Confirme el envío manualmente si es la primera vez."
        except Exception as e:
            import webbrowser
            webbrowser.open(url)
            return f"WhatsApp abierto en el navegador."

    # Método 2: WhatsApp Web búsqueda por nombre
    try:
        url = "https://web.whatsapp.com"
        subprocess.Popen([CHROME, url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(4)

        # Buscar contacto
        pyautogui.hotkey("ctrl", "f")
        time.sleep(0.5)
        if _PYPERCLIP:
            pyperclip.copy(receiver)
            pyautogui.hotkey("ctrl", "v")
        else:
            pyautogui.write(receiver, interval=0.05)
        time.sleep(1.5)

        # Click en el primer resultado
        pyautogui.press("enter")
        time.sleep(1)

        # Escribir mensaje
        if _PYPERCLIP:
            pyperclip.copy(message)
            pyautogui.hotkey("ctrl", "v")
        else:
            pyautogui.write(message, interval=0.03)
        time.sleep(0.3)
        pyautogui.press("enter")

        return f"Mensaje enviado a {receiver} por WhatsApp."
    except Exception as e:
        log.error(f"WhatsApp send error: {e}")
        return f"No pude enviar el mensaje: {e}"


def _send_telegram(receiver: str, message: str) -> str:
    """Abre Telegram Web y envía mensaje"""
    if not _PYAUTOGUI:
        return "PyAutoGUI no instalado."
    try:
        url = f"https://web.telegram.org"
        subprocess.Popen([CHROME, url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(4)

        # Buscar contacto con Ctrl+F o barra de búsqueda
        pyautogui.hotkey("ctrl", "f")
        time.sleep(0.5)
        if _PYPERCLIP:
            pyperclip.copy(receiver)
            pyautogui.hotkey("ctrl", "v")
        else:
            pyautogui.write(receiver, interval=0.05)
        time.sleep(1.5)
        pyautogui.press("enter")
        time.sleep(1)

        if _PYPERCLIP:
            pyperclip.copy(message)
            pyautogui.hotkey("ctrl", "v")
        else:
            pyautogui.write(message, interval=0.03)
        time.sleep(0.3)
        pyautogui.press("enter")

        return f"Mensaje enviado a {receiver} por Telegram."
    except Exception as e:
        log.error(f"Telegram send error: {e}")
        return f"No pude enviar el mensaje: {e}"
