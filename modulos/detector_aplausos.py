# modulos/detector_aplausos.py
import sounddevice as sd
import numpy as np
import time

class DetectorAplausos:
    def __init__(self, callback_activacion):
        self.callback = callback_activacion

        # Configuración de audio
        self.samplerate = 44100
        self.block_size = 1024

        # Triple filtro anti-voz
        self.umbral_energia = 0.05    # Energía mínima general
        self.umbral_pico = 0.2        # Pico máximo del bloque
        self.umbral_cambio = 0.15     # Cambio brusco (elimina voz continua)

        # Lógica de detección
        self.ventana_aplausos = 1.5   # Segundos entre los dos aplausos
        self.cooldown = 3             # Segundos mínimos entre activaciones

        # Estado interno
        self.timestamps_aplausos = []
        self.ultimo_activado = 0
        self.energia_anterior = 0
        self.activo = True

    def _callback(self, indata, frames, time_info, status):
        ahora = time.time()

        # --- Triple filtro ---
        energia = np.sqrt(np.mean(indata**2))
        pico = np.max(np.abs(indata))
        cambio = abs(energia - self.energia_anterior)
        self.energia_anterior = energia

        # ¿Es un aplauso real?
        es_aplauso = (
            energia > self.umbral_energia and
            pico > self.umbral_pico and
            cambio > self.umbral_cambio
        )

        if es_aplauso:
            # Evitar doble detección del mismo aplauso
            if not self.timestamps_aplausos or (ahora - self.timestamps_aplausos[-1]) > 0.3:
                self.timestamps_aplausos.append(ahora)
                print(f"👏 Aplauso | E={energia:.3f} P={pico:.3f} Δ={cambio:.3f}")

                # Limpiar aplausos viejos
                self.timestamps_aplausos = [
                    t for t in self.timestamps_aplausos
                    if ahora - t < self.ventana_aplausos
                ]

                # ¿Doble aplauso detectado?
                if len(self.timestamps_aplausos) >= 2:
                    if ahora - self.ultimo_activado > self.cooldown:
                        print("🚀 Doble aplauso confirmado — activando Jarvis...")
                        self.ultimo_activado = ahora
                        self.timestamps_aplausos = []
                        # Llamar al callback en hilo separado para no bloquear el audio
                        import threading
                        threading.Thread(
                            target=self.callback,
                            daemon=True
                        ).start()

    def escuchar(self):
        print("🎙️ Jarvis en espera... (doble aplauso para activar | anti-voz ON)")
        with sd.InputStream(
            callback=self._callback,
            samplerate=self.samplerate,
            channels=1,
            blocksize=self.block_size
        ):
            while self.activo:
                sd.sleep(100)

    def detener(self):
        self.activo = False