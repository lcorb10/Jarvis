# modulos/sintesis_voz.py
import asyncio
import io
import os
import tempfile
import threading
import time
from modulos.logger import log

jarvis_hablando = False
_lock_hablando = threading.Lock()


# Catálogo de voces disponibles. El usuario elige una sola en la GUI/config.
# Cada entrada define: motor real + identificador de voz para ese motor.
VOCES_DISPONIBLES = [
    # ── Edge TTS (rápido, sin cuota, español neutral) ─────────────────────────
    {"id": "edge_gonzalo",  "label": "Gonzalo (Edge, masculina CO)", "motor": "edge",    "voz": "es-CO-GonzaloNeural"},
    {"id": "edge_salome",   "label": "Salomé (Edge, femenina CO)",  "motor": "edge",    "voz": "es-CO-SalomeNeural"},
    {"id": "edge_jorge",    "label": "Jorge (Edge, masculina MX)",  "motor": "edge",    "voz": "es-MX-JorgeNeural"},
    {"id": "edge_dalia",    "label": "Dalia (Edge, femenina MX)",   "motor": "edge",    "voz": "es-MX-DaliaNeural"},
    {"id": "edge_alvaro",   "label": "Álvaro (Edge, masculina ES)", "motor": "edge",    "voz": "es-ES-AlvaroNeural"},
    # ── Gemini TTS (cuota API, mayor calidad) ────────────────────────────────
    {"id": "gemini_charon", "label": "Charon (Gemini)",             "motor": "gemini",  "voz": "Charon"},
    {"id": "gemini_aoede",  "label": "Aoede (Gemini)",              "motor": "gemini",  "voz": "Aoede"},
    {"id": "gemini_kore",   "label": "Kore (Gemini)",               "motor": "gemini",  "voz": "Kore"},
    {"id": "gemini_fenrir", "label": "Fenrir (Gemini)",             "motor": "gemini",  "voz": "Fenrir"},
    {"id": "gemini_puck",   "label": "Puck (Gemini)",               "motor": "gemini",  "voz": "Puck"},
    # ── pyttsx3 (offline, voces de Windows) ──────────────────────────────────
    {"id": "pyttsx3_helena", "label": "Helena (pyttsx3, offline)",  "motor": "pyttsx3", "voz": "helena"},
    {"id": "pyttsx3_pablo",  "label": "Pablo (pyttsx3, offline)",   "motor": "pyttsx3", "voz": "pablo"},
    {"id": "pyttsx3_sabina", "label": "Sabina (pyttsx3, offline)",  "motor": "pyttsx3", "voz": "sabina"},
]


def voz_por_id(voz_id: str) -> dict | None:
    for v in VOCES_DISPONIBLES:
        if v["id"] == voz_id:
            return v
    return None


class SintesisVoz:
    """
    TTS con voz unificada — el usuario elige UNA voz (de Edge, Gemini o pyttsx3)
    y siempre usa esa. Si el motor de esa voz falla, cae a Edge → pyttsx3.
    """

    def __init__(self, voz_id: str = "edge_gonzalo"):
        self.modo_silencioso = False
        self._voz_actual = voz_por_id(voz_id) or VOCES_DISPONIBLES[0]
        self._gemini_tts_pausado_hasta = 0.0
        self.modelo_gemini_tts = "gemini-2.5-flash-preview-tts"

        from modulos.gemini_manager import gemini
        self._gm = gemini()

        self.usar_edge = self._verificar_edge()
        self.pygame_ok = self._verificar_pygame()

        # Event loop persistente para Edge TTS (evita asyncio.run cada vez)
        self._loop = asyncio.new_event_loop()
        threading.Thread(target=self._loop.run_forever, daemon=True).start()

        # pyttsx3 engine reutilizable
        self._pyttsx3_engine = None

        log.info(f"✅ TTS: voz seleccionada = {self._voz_actual['label']}")

    def _verificar_edge(self) -> bool:
        try:
            import edge_tts  # noqa
            return True
        except ImportError:
            log.warning("edge-tts no instalado: pip install edge-tts")
            return False

    def _verificar_pygame(self) -> bool:
        try:
            import pygame
            pygame.mixer.init(frequency=24000, buffer=512)  # buffer chico = menos latencia
            return True
        except Exception as e:
            log.warning(f"Pygame no disponible: {e}")
            return False

    # ── Entrada pública ────────────────────────────────────────────────────────
    def hablar(self, texto: str):
        global jarvis_hablando
        if not texto or not texto.strip():
            return
        if self.modo_silencioso:
            log.info(f"[SILENCIOSO] {texto}")
            return

        log.info(f"🔊 Jarvis: {texto}")
        with _lock_hablando:
            jarvis_hablando = True
        try:
            motor = self._voz_actual["motor"]
            voz = self._voz_actual["voz"]

            # Intentar el motor de la voz elegida
            ok = False
            if motor == "gemini" and time.time() >= self._gemini_tts_pausado_hasta:
                puede, _ = self._gm.puede_llamar("tts")
                if puede:
                    ok = self._hablar_gemini(texto, voz)
            elif motor == "edge" and self.usar_edge:
                ok = self._hablar_edge(texto, voz)
            elif motor == "pyttsx3":
                ok = self._hablar_pyttsx3(texto, voz)

            # Fallbacks si el motor preferido falla
            if not ok and motor != "edge" and self.usar_edge:
                ok = self._hablar_edge(texto, "es-CO-GonzaloNeural")
            if not ok and motor != "pyttsx3":
                self._hablar_pyttsx3(texto, "helena")
        except Exception as e:
            log.error(f"Error TTS: {e}")
        finally:
            with _lock_hablando:
                jarvis_hablando = False

    # ── Edge directo con voz específica (para mensajes Telegram, etc.) ────────
    def hablar_edge(self, texto: str, voz_edge: str = "es-MX-JorgeNeural"):
        """Habla con Edge ignorando la voz configurada. Útil para distinguir
        un 'narrador' (mensajes entrantes) del Jarvis principal."""
        global jarvis_hablando
        if not texto or not texto.strip() or self.modo_silencioso:
            return
        if not self.usar_edge:
            log.warning("[TTS] Edge no disponible, fallback a hablar() normal")
            self.hablar(texto)
            return
        log.info(f"🔊 (Edge {voz_edge}) {texto}")
        with _lock_hablando:
            jarvis_hablando = True
        try:
            ok = self._hablar_edge(texto, voz_edge)
            if not ok:
                self._hablar_pyttsx3(texto, "helena")
        finally:
            with _lock_hablando:
                jarvis_hablando = False

    # ── Edge TTS (streaming a memoria) ────────────────────────────────────────
    def _hablar_edge(self, texto: str, voz: str) -> bool:
        try:
            future = asyncio.run_coroutine_threadsafe(
                self._stream_edge(texto, voz), self._loop
            )
            audio_bytes = future.result(timeout=10)
            if not audio_bytes:
                return False
            self._reproducir_bytes(audio_bytes, ".mp3")
            return True
        except Exception as e:
            log.error(f"Edge TTS error: {e}")
            return False

    async def _stream_edge(self, texto: str, voz: str) -> bytes:
        import edge_tts
        c = edge_tts.Communicate(texto, voz)
        buf = io.BytesIO()
        async for chunk in c.stream():
            if chunk["type"] == "audio":
                buf.write(chunk["data"])
        return buf.getvalue()

    # ── Gemini TTS ────────────────────────────────────────────────────────────
    def _hablar_gemini(self, texto: str, voz: str) -> bool:
        import wave
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self._gm.api_key)
            response = client.models.generate_content(
                model=self.modelo_gemini_tts,
                contents=texto,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voz)
                        )
                    ),
                ),
            )
            cands = response.candidates
            if not cands or not cands[0].content or not cands[0].content.parts:
                raise RuntimeError("Respuesta Gemini TTS vacía")
            audio_bytes = cands[0].content.parts[0].inline_data.data
            # Envolver PCM en WAV en memoria
            buf = io.BytesIO()
            with wave.open(buf, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(24000)
                wf.writeframes(audio_bytes)
            self._gm.registrar_llamada("tts", exito=True)
            self._reproducir_bytes(buf.getvalue(), ".wav")
            return True
        except Exception as e:
            err = str(e)
            self._gm.registrar_llamada("tts", exito=False, error=err)
            log.warning(f"Gemini TTS error: {err[:80]}")
            if "429" in err or "quota" in err.lower():
                self._gemini_tts_pausado_hasta = time.time() + 600
                log.info("[TTS] Gemini TTS pausado 10 min por cuota agotada")
            return False

    # ── pyttsx3 (engine reutilizable) ─────────────────────────────────────────
    def _hablar_pyttsx3(self, texto: str, voz_buscar: str) -> bool:
        try:
            import pyttsx3
            if self._pyttsx3_engine is None:
                self._pyttsx3_engine = pyttsx3.init()
                self._pyttsx3_engine.setProperty("rate", 175)
                self._pyttsx3_engine.setProperty("volume", 0.95)
            e = self._pyttsx3_engine
            for v in e.getProperty("voices"):
                if voz_buscar.lower() in v.name.lower():
                    e.setProperty("voice", v.id)
                    break
            e.say(texto)
            e.runAndWait()
            return True
        except Exception as ex:
            log.error(f"pyttsx3 error: {ex}")
            self._pyttsx3_engine = None
            return False

    # ── Reproducción desde bytes (sin archivo temporal en disco) ──────────────
    def _reproducir_bytes(self, audio_bytes: bytes, suffix: str):
        if self.pygame_ok:
            try:
                import pygame
                buf = io.BytesIO(audio_bytes)
                pygame.mixer.music.load(buf)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    time.sleep(0.03)
                return
            except Exception as e:
                log.warning(f"Pygame playback error: {e} — fallback a archivo temp")

        # Fallback: archivo temporal + PowerShell
        ruta = None
        try:
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
                f.write(audio_bytes)
                ruta = f.name
            self._reproducir_powershell(ruta)
        finally:
            if ruta and os.path.exists(ruta):
                try: os.unlink(ruta)
                except Exception: pass

    def _reproducir_powershell(self, ruta: str):
        import subprocess
        try:
            subprocess.run(
                ["powershell", "-c",
                 f'(New-Object Media.SoundPlayer "{ruta}").PlaySync()'],
                timeout=60, capture_output=True,
            )
        except Exception as e:
            log.error(f"PowerShell audio error: {e}")

    # ── Control ───────────────────────────────────────────────────────────────
    def activar_silencioso(self):
        self.modo_silencioso = True

    def desactivar_silencioso(self):
        self.modo_silencioso = False

    def set_voz(self, voz_id: str) -> bool:
        v = voz_por_id(voz_id)
        if not v:
            log.warning(f"[TTS] voz_id desconocido: {voz_id}")
            return False
        self._voz_actual = v
        log.info(f"[TTS] Voz cambiada → {v['label']}")
        return True

    def voz_actual_id(self) -> str:
        return self._voz_actual["id"]

    # ── Compatibilidad con código viejo ──────────────────────────────────────
    @property
    def voz_edge(self) -> str:
        if self._voz_actual["motor"] == "edge":
            return self._voz_actual["voz"]
        return "es-CO-GonzaloNeural"

    @voz_edge.setter
    def voz_edge(self, valor: str):
        for v in VOCES_DISPONIBLES:
            if v["motor"] == "edge" and v["voz"] == valor:
                self._voz_actual = v
                return

    def cambiar_voz(self, voz: str):
        self.voz_edge = voz

    def cambiar_voz_gemini(self, voz: str):
        for v in VOCES_DISPONIBLES:
            if v["motor"] == "gemini" and v["voz"] == voz:
                self._voz_actual = v
                return
