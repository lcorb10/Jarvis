# modulos/reconocimiento_voz.py
import sounddevice as sd
import numpy as np
import json
import time
from modulos.sintesis_voz import jarvis_hablando


class ReconocimientoVoz:
    """
    STT con Vosk. Estados emitidos vía on_state(state):
      - "loading"    cargando modelo a RAM
      - "ready"      modelo cargado, idle
      - "listening"  escuchando audio activamente
      - "off"        modelo descargado de RAM
    """

    def __init__(self, ruta_modelo="modelos/vosk-es"):
        self._ruta_modelo = ruta_modelo
        self.samplerate = 16000
        self.on_partial = None
        self.on_final = None
        self.on_state = None  # callback para el estado de Vosk
        self._modelo = None  # carga lazy

    def _emit_state(self, state: str):
        if self.on_state:
            try:
                self.on_state(state)
            except Exception:
                pass

    def _cargar_modelo(self):
        if self._modelo is None:
            from vosk import Model
            print("⏳ Cargando modelo de voz...")
            self._emit_state("loading")
            self._modelo = Model(self._ruta_modelo)
            print("✅ Modelo de voz listo.")
            self._emit_state("ready")
        return self._modelo

    def precargar(self):
        """Carga Vosk en background al startup."""
        self._cargar_modelo()

    def _liberar_modelo(self):
        """Libera el modelo Vosk de RAM cuando no se necesita."""
        if self._modelo is not None:
            self._modelo = None
            self._emit_state("off")

    def esta_cargado(self) -> bool:
        return self._modelo is not None

    def _nuevo_recognizer(self):
        from vosk import KaldiRecognizer
        return KaldiRecognizer(self._cargar_modelo(), self.samplerate)

    def set_callbacks(self, on_partial=None, on_final=None):
        self.on_partial = on_partial
        self.on_final = on_final

    def set_state_callback(self, on_state=None):
        self.on_state = on_state

    def escuchar_comando(self, timeout=10):
        print("🎤 Escuchando...")
        audio_buffer = []
        recognizer = self._nuevo_recognizer()
        ultimo_parcial = ""
        self._emit_state("listening")

        def callback(indata, frames, time_info, status):
            if jarvis_hablando:
                return
            audio_int16 = (indata[:, 0] * 32767).astype(np.int16)
            audio_buffer.append(audio_int16.tobytes())

        try:
            with sd.InputStream(
                samplerate=self.samplerate,
                channels=1,
                dtype="float32",
                callback=callback,
                blocksize=4000,
            ):
                inicio = time.time()
                while time.time() - inicio < timeout:
                    time.sleep(0.05)
                    while audio_buffer:
                        chunk = audio_buffer.pop(0)
                        if recognizer.AcceptWaveform(chunk):
                            resultado = json.loads(recognizer.Result())
                            texto = resultado.get("text", "").strip()
                            if texto:
                                print(f"📝 Escuché: '{texto}'")
                                if self.on_final:
                                    try: self.on_final(texto)
                                    except Exception: pass
                                return texto
                        else:
                            parcial = json.loads(recognizer.PartialResult())
                            tp = parcial.get("partial", "").strip()
                            if tp and tp != ultimo_parcial:
                                ultimo_parcial = tp
                                print(f"🔄 '{tp}'", end="\r")
                                if self.on_partial:
                                    try: self.on_partial(tp)
                                    except Exception: pass

            resultado = json.loads(recognizer.FinalResult())
            texto = resultado.get("text", "").strip()
            if texto:
                print(f"📝 Escuché (final): '{texto}'")
                if self.on_final:
                    try: self.on_final(texto)
                    except Exception: pass
            return texto
        finally:
            # Salir de listening — modelo sigue en RAM como "ready"
            if self._modelo is not None:
                self._emit_state("ready")
