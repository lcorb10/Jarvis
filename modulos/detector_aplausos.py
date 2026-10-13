# modulos/detector_aplausos.py
import sounddevice as sd
import numpy as np
import time
import threading


class DetectorAplausos:
    def __init__(self, callback_activacion, debug: bool = False):
        self.callback = callback_activacion
        self.samplerate = 8000   # 44100 era innecesario para detectar aplausos
        self.block_size = 512
        # Umbrales rebajados — el setting anterior era muy estricto para mics típicos
        self.umbral_energia = 0.02
        self.umbral_pico = 0.10
        self.umbral_cambio = 0.05
        self.ventana_aplausos = 1.8
        self.cooldown = 3
        self.timestamps_aplausos = []
        self.ultimo_activado = 0
        self.energia_anterior = 0
        self.activo = True
        self.en_pausa = False  # True mientras Jarvis está en conversación activa
        self.debug = debug  # set True para ver energia/pico/cambio en tiempo real

    def _callback(self, indata, frames, time_info, status):
        if self.en_pausa:
            return
        ahora = time.time()
        energia = float(np.sqrt(np.mean(indata**2)))
        pico = float(np.max(np.abs(indata)))
        cambio = abs(energia - self.energia_anterior)
        self.energia_anterior = energia

        es_aplauso = (
            energia > self.umbral_energia and
            pico > self.umbral_pico and
            cambio > self.umbral_cambio
        )

        if self.debug and (energia > 0.005 or pico > 0.03):
            print(f"[clap dbg] e={energia:.3f} p={pico:.3f} c={cambio:.3f} aplauso={es_aplauso}")

        if es_aplauso:
            if not self.timestamps_aplausos or (ahora - self.timestamps_aplausos[-1]) > 0.2:
                self.timestamps_aplausos.append(ahora)
                self.timestamps_aplausos = [
                    t for t in self.timestamps_aplausos
                    if ahora - t < self.ventana_aplausos
                ]
                if self.debug:
                    print(f"[clap] {len(self.timestamps_aplausos)}/2")
                if len(self.timestamps_aplausos) >= 2:
                    if ahora - self.ultimo_activado > self.cooldown:
                        self.ultimo_activado = ahora
                        self.timestamps_aplausos = []
                        print("👏👏 Doble aplauso detectado — activando Jarvis")
                        threading.Thread(target=self.callback, daemon=True).start()

    def escuchar(self):
        print("🎙️ Jarvis en espera... (doble aplauso para activar)")
        with sd.InputStream(
            callback=self._callback,
            samplerate=self.samplerate,
            channels=1,
            blocksize=self.block_size,
        ):
            while self.activo:
                sd.sleep(100)

    def pausar(self):
        """Pausa la detección mientras Jarvis está en conversación activa (el mic lo usa STT)."""
        self.en_pausa = True
        self.timestamps_aplausos = []
        self.energia_anterior = 0

    def reanudar(self):
        """Reactiva la detección tras terminar la conversación."""
        self.en_pausa = False

    def detener(self):
        self.activo = False
