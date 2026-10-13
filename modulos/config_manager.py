# modulos/config_manager.py
import json
import os
import hashlib
import threading
from modulos.logger import log

_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config.json")
_listeners: list = []
_lock = threading.Lock()
_cfg: dict = {}
_last_hash: str = ""


def _load() -> dict:
    try:
        with open(_CONFIG_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log.error(f"[Config] Error cargando config.json: {e}")
        return {}


def _file_hash() -> str:
    try:
        with open(_CONFIG_PATH, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception:
        return ""


def get(section: str = None, key: str = None, default=None):
    with _lock:
        if not _cfg:
            _cfg.update(_load())
        if section is None:
            return dict(_cfg)
        sec = _cfg.get(section, {})
        if key is None:
            return sec
        return sec.get(key, default)


def reload():
    global _cfg, _last_hash
    nuevo_hash = _file_hash()
    with _lock:
        if nuevo_hash == _last_hash:
            return  # contenido idéntico — ignorar evento duplicado
        _last_hash = nuevo_hash
        nuevo = _load()
        _cfg.clear()
        _cfg.update(nuevo)
    log.info("[Config] config.json recargado")
    for fn in list(_listeners):
        try:
            fn(_cfg)
        except Exception as e:
            log.error(f"[Config] Listener error: {e}")


def on_change(fn):
    """Registra callback que se llama cuando config.json cambia."""
    _listeners.append(fn)


def start_watcher():
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler

        _debounce_timer = [None]
        _abs_cfg = os.path.abspath(_CONFIG_PATH)

        class _Handler(FileSystemEventHandler):
            def on_modified(self, event):
                if os.path.abspath(event.src_path) != _abs_cfg:
                    return
                # Debounce 500ms — Windows puede emitir múltiples eventos por un solo guardado
                if _debounce_timer[0]:
                    _debounce_timer[0].cancel()
                t = threading.Timer(0.5, reload)
                _debounce_timer[0] = t
                t.daemon = True
                t.start()

        observer = Observer()
        observer.schedule(_Handler(), path=os.path.dirname(_abs_cfg), recursive=False)
        observer.daemon = True
        observer.start()
        log.info("[Config] Watcher activo — cambios en config.json se aplican en tiempo real")
    except Exception as e:
        log.warning(f"[Config] Watcher no disponible: {e}")


# Carga inicial
_cfg.update(_load())
_last_hash = _file_hash()
