# modulos/reconocimiento_voz.py
import sounddevice as sd
import numpy as np
import json
import time
from vosk import Model, KaldiRecognizer
from modulos.sintesis_voz import jarvis_hablando

class ReconocimientoVoz:
    def __init__(self, ruta_modelo="modelos/vosk-es"):
        print("⏳ Cargando modelo de reconocimiento de voz...")
        self.modelo = Model(ruta_modelo)
        self.samplerate = 16000
        print("✅ Modelo de voz listo.")

    def _nuevo_recognizer(self):
        return KaldiRecognizer(self.modelo, self.samplerate)

    def escuchar_comando(self, timeout=10):
        print("🎤 Escuchando...")
        audio_buffer = []
        recognizer = self._nuevo_recognizer()
        silencio_count = 0

        def callback(indata, frames, time_info, status):
            if jarvis_hablando:
                return
            audio_int16 = (indata[:, 0] * 32767).astype(np.int16)
            audio_buffer.append(audio_int16.tobytes())

        with sd.InputStream(
            samplerate=self.samplerate,
            channels=1,
            dtype='float32',
            callback=callback,
            blocksize=8000  # Bloques más grandes = mejor reconocimiento
        ):
            inicio = time.time()
            texto_parcial = ""

            while time.time() - inicio < timeout:
                time.sleep(0.1)
                if audio_buffer:
                    chunk = audio_buffer.pop(0)
                    if recognizer.AcceptWaveform(chunk):
                        resultado = json.loads(recognizer.Result())
                        texto = resultado.get("text", "").strip()
                        if texto:
                            print(f"📝 Escuché: '{texto}'")
                            return texto
                    else:
                        # Mostrar texto parcial en tiempo real
                        parcial = json.loads(recognizer.PartialResult())
                        texto_parcial = parcial.get("partial", "")
                        if texto_parcial:
                            print(f"🔄 '{texto_parcial}'", end='\r')

        # Capturar lo último aunque no haya pausa
        resultado = json.loads(recognizer.FinalResult())
        texto = resultado.get("text", "").strip()
        if texto:
            print(f"📝 Escuché (final): '{texto}'")
        return texto