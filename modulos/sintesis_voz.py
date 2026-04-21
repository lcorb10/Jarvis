# modulos/sintesis_voz.py
import subprocess
import sys
import time
import os
import tempfile
import threading
from modulos.logger import log

jarvis_hablando = False

class SintesisVoz:
    def __init__(self):
        self.modo_silencioso = False
        self.python = sys.executable
        self.usar_coqui = self._inicializar_coqui()

    def _inicializar_coqui(self):
        try:
            from TTS.api import TTS
            log.info("⏳ Cargando modelo Coqui TTS...")
            self.tts_engine = TTS(
                model_name="tts_models/es/css10/vits",
                progress_bar=False,
                gpu=False
            )
            log.info("✅ Coqui TTS listo con voz natural en español")
            return True
        except ImportError:
            log.warning("Coqui TTS no instalado. Usando pyttsx3 como fallback.")
            return False
        except Exception as e:
            log.warning(f"Coqui TTS falló al cargar: {e}. Usando pyttsx3.")
            return False

    def hablar(self, texto):
        global jarvis_hablando
        if self.modo_silencioso:
            log.info(f"[SILENCIOSO] Jarvis: {texto}")
            return

        log.info(f"🔊 Jarvis: {texto}")
        jarvis_hablando = True

        try:
            if self.usar_coqui:
                self._hablar_coqui(texto)
            else:
                self._hablar_pyttsx3(texto)
        except Exception as e:
            log.error(f"Error en síntesis de voz: {e}")
            try:
                self._hablar_pyttsx3(texto)
            except Exception as e2:
                log.error(f"Fallback también falló: {e2}")
        finally:
            time.sleep(0.5)
            jarvis_hablando = False

    def _hablar_coqui(self, texto):
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            ruta_audio = f.name
        try:
            self.tts_engine.tts_to_file(text=texto, file_path=ruta_audio)
            if sys.platform == "win32":
                subprocess.run(
                    ["powershell", "-c",
                     f'(New-Object Media.SoundPlayer "{ruta_audio}").PlaySync()'],
                    timeout=30
                )
            else:
                subprocess.run(["aplay", ruta_audio], timeout=30)
        finally:
            try:
                os.unlink(ruta_audio)
            except:
                pass

    def _hablar_pyttsx3(self, texto):
        codigo = f"""
import pyttsx3
e = pyttsx3.init()
e.setProperty('rate', 135)
e.setProperty('volume', 0.95)
voces = e.getProperty('voices')
for v in voces:
    if 'helena' in v.name.lower():
        e.setProperty('voice', v.id)
        break
e.say({repr(texto)})
e.runAndWait()
"""
        subprocess.run(
            [self.python, "-c", codigo],
            timeout=30
        )

    def hablar_async(self, texto):
        self.hablar(texto)

    def activar_silencioso(self):
        self.modo_silencioso = True
        log.info("Modo silencioso activado")

    def desactivar_silencioso(self):
        self.modo_silencioso = False
        log.info("Modo silencioso desactivado")