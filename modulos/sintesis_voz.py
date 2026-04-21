# modulos/sintesis_voz.py
import subprocess
import sys
import time

jarvis_hablando = False

class SintesisVoz:
    def __init__(self):
        self.python = sys.executable
        print("✅ Módulo de voz listo.")

    def hablar(self, texto):
        global jarvis_hablando
        print(f"🔊 Jarvis: {texto}")
        jarvis_hablando = True
        try:
            # Ejecutar pyttsx3 en un proceso completamente separado
            # Esto evita que el engine se congele entre llamadas
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
        except subprocess.TimeoutExpired:
            print("❌ Timeout en síntesis de voz.")
        except Exception as e:
            print(f"❌ Error de voz: {e}")
        finally:
            time.sleep(0.5)
            jarvis_hablando = False

    def hablar_async(self, texto):
        self.hablar(texto)