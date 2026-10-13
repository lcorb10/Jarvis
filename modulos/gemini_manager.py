# modulos/gemini_manager.py
import os
import time
import threading
from collections import deque
from modulos.logger import log

_MODELO_VERIFICACION = "gemini-2.5-flash"


class GeminiManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._init()
        return cls._instance

    def _init(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self._key_valida = None
        self._bloqueado_sesion = False
        self._motivo_bloqueo = ""
        self._llamadas: deque = deque()
        self._max_calls_por_min = 55  # límite gratuito ~60/min, dejamos margen
        self._stats = {k: {"ok": 0, "error": 0} for k in ("chat", "tts", "stt", "vision", "planner")}
        self._errores_consecutivos = {}
        self._categorias_bloqueadas = set()

        if self.api_key:
            log.info(f"[GeminiManager] Inicializado (key={self.api_key[:8]}...)")
        else:
            log.warning("[GeminiManager] Sin GEMINI_API_KEY — Gemini deshabilitado")
            self._bloqueado_sesion = True
            self._motivo_bloqueo = "Sin API key"

    def verificar_key(self) -> bool:
        if self._key_valida is not None:
            return self._key_valida
        if not self.api_key:
            self._key_valida = False
            return False
        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            client.models.generate_content(
                model=_MODELO_VERIFICACION,
                contents="ok",
            )
            self._key_valida = True
            log.info("[GeminiManager] ✅ API key válida")
            return True
        except Exception as e:
            err = str(e)
            err_low = err.lower()
            self._key_valida = False

            if "api_key_invalid" in err_low or "api key not valid" in err_low:
                motivo = "API key inválida — revisa GEMINI_API_KEY en .env"
                self._bloqueado_sesion = True  # key inválida → bloquear todo
            elif "permission_denied" in err_low or "service_disabled" in err_low or "has not been used" in err_low:
                motivo = "API 'Generative Language' deshabilitada — actívala en console.cloud.google.com"
                self._bloqueado_sesion = True
            elif "quota" in err_low or "429" in err:
                motivo = "Cuota/rate limit (429) — espera unos minutos o verifica que la API esté habilitada"
                self._bloqueado_sesion = True
            elif "not found" in err_low or "404" in err:
                # Modelo de verificación no disponible — NO bloquear TTS/otros modelos
                motivo = f"Modelo no disponible — usa {_MODELO_VERIFICACION}"
                self._categorias_bloqueadas.add("chat")  # solo chat bloqueado
            elif "401" in err or "unauthorized" in err_low:
                motivo = "401 Unauthorized — key incorrecta"
                self._bloqueado_sesion = True
            elif "403" in err or "forbidden" in err_low:
                motivo = "403 Forbidden — proyecto sin acceso"
                self._bloqueado_sesion = True
            else:
                motivo = f"Error: {err[:80]}"
                self._categorias_bloqueadas.add("chat")

            self._motivo_bloqueo = motivo
            log.warning(f"[GeminiManager] ❌ {motivo}")
            return False

    def puede_llamar(self, categoria: str = "chat") -> tuple[bool, str]:
        if self._bloqueado_sesion:
            return False, self._motivo_bloqueo
        if categoria in self._categorias_bloqueadas:
            return False, f"Categoría '{categoria}' bloqueada"
        ahora = time.time()
        with self._lock:
            while self._llamadas and ahora - self._llamadas[0] > 60:
                self._llamadas.popleft()
            if len(self._llamadas) >= self._max_calls_por_min:
                return False, f"Rate limit: {self._max_calls_por_min}/min"
        return True, "ok"

    def registrar_llamada(self, categoria: str, exito: bool, error: str = ""):
        with self._lock:
            self._llamadas.append(time.time())
            if categoria not in self._stats:
                self._stats[categoria] = {"ok": 0, "error": 0}
            if exito:
                self._stats[categoria]["ok"] += 1
                self._errores_consecutivos[categoria] = 0
            else:
                self._stats[categoria]["error"] += 1
                cnt = self._errores_consecutivos.get(categoria, 0) + 1
                self._errores_consecutivos[categoria] = cnt
                err_low = error.lower()
                if "api_key_invalid" in err_low or "401" in error or "403" in error:
                    self._bloqueado_sesion = True
                    self._motivo_bloqueo = "API key inválida (detectada en uso)"
                    log.warning(f"[GeminiManager] 🔒 {self._motivo_bloqueo}")
                elif "quota" in err_low or "429" in error:
                    # No bloqueamos sesión completa por 429 — solo pausamos
                    log.warning("[GeminiManager] ⚠️ Rate limit 429 detectado")
                elif cnt >= 3:
                    self._categorias_bloqueadas.add(categoria)
                    log.warning(f"[GeminiManager] 🔒 Categoría '{categoria}' bloqueada (3 errores)")

    @property
    def disponible(self) -> bool:
        return not self._bloqueado_sesion

    def stats(self) -> dict:
        return {
            "key_valida": self._key_valida,
            "bloqueado": self._bloqueado_sesion,
            "motivo": self._motivo_bloqueo,
            "categorias_bloqueadas": list(self._categorias_bloqueadas),
            "calls_ultimo_min": len(self._llamadas),
            "stats": dict(self._stats),
        }

    def resetear(self):
        with self._lock:
            self._bloqueado_sesion = False
            self._key_valida = None
            self._motivo_bloqueo = ""
            self._categorias_bloqueadas.clear()
            self._errores_consecutivos.clear()
            self.api_key = os.getenv("GEMINI_API_KEY", "").strip()
        log.info("[GeminiManager] Reset completado")


_gm = None


def gemini() -> GeminiManager:
    global _gm
    if _gm is None:
        _gm = GeminiManager()
    return _gm
