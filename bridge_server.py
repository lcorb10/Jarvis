# bridge_server.py - HTTP bridge para que el bot de Telegram (WSL2) use Jarvis MK2
"""
Endpoints (todos JSON salvo /file):
  GET  /health              -> {"status":"ok","gui_active":bool}
  POST /command             -> {"response":"texto","ok":true}
       Body: {"text":"...", "speak": true|false}
  GET  /file?path=<abs>     -> stream binario del archivo

Bind: 0.0.0.0:18790  (alcanzable desde WSL2 via 172.28.144.1:18790)
Sin auth; loopback + LAN del host. Suficiente para uso single-user.
"""
import glob
import json
import os
import shutil
import tempfile
import threading
import urllib.parse
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

TELEGRAM_MAX_BYTES = 50 * 1024 * 1024  # 50 MB límite de Telegram

_SEARCH_DIRS = [
    Path.home() / "Desktop",
    Path.home() / "Downloads",
    Path.home() / "Documents",
    Path.home() / "Pictures",
    Path.home() / "Videos",
    Path.home() / "Music",
]
# Home se busca solo un nivel (no recursivo) para evitar timeout
_SEARCH_HOME_SHALLOW = Path.home()


def _find_files(query: str, limit: int = 8) -> list[Path]:
    """Busca archivos que contengan `query` en nombre, ordenados por similitud.
    Primero busca en directorios específicos (recursivo), luego en home (un nivel).
    """
    import time as _time
    query_lower = query.lower().strip()
    # Quitar extensión del query para búsqueda más flexible
    query_stem = query_lower.rsplit(".", 1)[0] if "." in query_lower else query_lower

    seen: set[Path] = set()
    matches: list[tuple[int, Path]] = []
    deadline = _time.time() + 8.0  # máximo 8 segundos de búsqueda total

    def _add(p: Path):
        if p in seen:
            return
        seen.add(p)
        name_lower = p.name.lower()
        name_stem = name_lower.rsplit(".", 1)[0] if "." in name_lower else name_lower
        # Coincidencia por nombre completo o por stem (sin extensión)
        if query_lower in name_lower or query_stem in name_stem:
            score = len(name_lower) - len(query_lower)
            matches.append((score, p))

    for base in _SEARCH_DIRS:
        if not base.exists():
            continue
        try:
            for p in base.rglob("*"):
                if _time.time() > deadline:
                    break
                if p.is_file():
                    _add(p)
        except (PermissionError, OSError):
            continue

    # Home: solo un nivel (iterdir) para evitar recorrer todo el sistema
    if _SEARCH_HOME_SHALLOW.exists() and _time.time() < deadline:
        try:
            for p in _SEARCH_HOME_SHALLOW.iterdir():
                if p.is_file():
                    _add(p)
        except (PermissionError, OSError):
            pass

    matches.sort(key=lambda x: x[0])
    return [p for _, p in matches[:limit]]


def _compress_file(path: Path) -> tuple[Path, bool]:
    """
    Comprime el archivo en un zip temporal.
    Devuelve (ruta_zip, True) si el zip cabe en Telegram, (ruta_zip, False) si es muy grande.
    El zip queda en tempdir — el caller debe borrarlo.
    """
    tmp = tempfile.mkdtemp(prefix="jarvis_zip_")
    zip_base = os.path.join(tmp, path.stem)
    zip_path = Path(shutil.make_archive(zip_base, "zip", path.parent, path.name))
    size_ok = zip_path.stat().st_size <= TELEGRAM_MAX_BYTES
    return zip_path, size_ok

PORT = 18790


class _Handler(BaseHTTPRequestHandler):
    jarvis = None  # set by start_bridge

    def log_message(self, *args, **kwargs):
        pass  # silenciar

    # ---------- helpers ----------
    def _json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        n = int(self.headers.get("Content-Length", 0))
        if n <= 0:
            return {}
        try:
            return json.loads(self.rfile.read(n).decode("utf-8"))
        except Exception:
            return {}

    # ---------- routes ----------
    def do_GET(self):
        u = urllib.parse.urlparse(self.path)

        if u.path == "/health":
            j = _Handler.jarvis
            gui_visible = bool(j and getattr(j, "gui_visible", False))
            self._json({
                "status": "ok",
                "gui_active": j is not None,
                "gui_visible": gui_visible,
            })
            return

        if u.path == "/file":
            qs = urllib.parse.parse_qs(u.query)
            path = qs.get("path", [""])[0]
            if not path or not os.path.isfile(path):
                self.send_response(404)
                self.end_headers()
                return
            try:
                size = os.path.getsize(path)
                self.send_response(200)
                self.send_header("Content-Type", "application/octet-stream")
                self.send_header("Content-Length", str(size))
                self.send_header(
                    "Content-Disposition",
                    f'attachment; filename="{os.path.basename(path)}"',
                )
                self.end_headers()
                with open(path, "rb") as f:
                    while True:
                        chunk = f.read(64 * 1024)
                        if not chunk:
                            break
                        self.wfile.write(chunk)
            except Exception:
                try:
                    self.send_response(500)
                    self.end_headers()
                except Exception:
                    pass
            return

        if u.path == "/find_file":
            # GET /find_file?q=nombre → JSON con lista de coincidencias
            qs = urllib.parse.parse_qs(u.query)
            query = qs.get("q", [""])[0].strip()
            if not query:
                self._json({"ok": False, "error": "q requerido"}, status=400)
                return
            found = _find_files(query)
            self._json({
                "ok": True,
                "files": [
                    {
                        "name": p.name,
                        "path": str(p),
                        "size_mb": round(p.stat().st_size / (1024 * 1024), 2),
                    }
                    for p in found
                ],
            })
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        u = urllib.parse.urlparse(self.path)

        if u.path == "/show":
            # Llamado por el segundo lanzamiento o por scripts: trae la GUI al frente
            j = _Handler.jarvis
            if j and hasattr(j, "_gui") and j._gui:
                fn = j._gui.get("on_show_window")
                if fn:
                    try:
                        fn()
                        self._json({"ok": True})
                        return
                    except Exception as e:
                        self._json({"ok": False, "error": str(e)}, status=500)
                        return
            self._json({"ok": False, "error": "GUI no disponible"}, status=503)
            return

        if u.path == "/compress_and_send":
            # POST {"path": "C:\\ruta\\al\\archivo.txt"}
            # Comprime y sirve el zip — responde con la ruta del zip temporal
            data = self._read_json()
            file_path = data.get("path", "").strip()
            if not file_path or not os.path.isfile(file_path):
                self._json({"ok": False, "error": "archivo no encontrado"}, status=404)
                return
            try:
                p = Path(file_path)
                zip_path, size_ok = _compress_file(p)
                if not size_ok:
                    size_mb = zip_path.stat().st_size / (1024 * 1024)
                    # Limpiar zip temporal
                    try:
                        shutil.rmtree(zip_path.parent)
                    except Exception:
                        pass
                    self._json({
                        "ok": False,
                        "error": "too_large",
                        "size_mb": round(size_mb, 1),
                        "original": p.name,
                    })
                    return
                self._json({
                    "ok": True,
                    "zip_path": str(zip_path),
                    "zip_name": zip_path.name,
                    "original": p.name,
                    "size_mb": round(zip_path.stat().st_size / (1024 * 1024), 2),
                })
            except Exception as e:
                self._json({"ok": False, "error": str(e)}, status=500)
            return

        if u.path == "/command":
            data = self._read_json()
            text = (data.get("text") or "").strip()
            speak = bool(data.get("speak", False))

            if not text:
                self._json({"ok": False, "error": "empty text"}, status=400)
                return

            if _Handler.jarvis is None:
                self._json({"ok": False, "error": "jarvis not initialized"}, status=503)
                return

            try:
                response = _Handler.jarvis.ejecutar_para_telegram(text, speak=speak)
                self._json({"ok": True, "response": response or ""})
            except Exception as e:
                self._json({"ok": False, "error": str(e)}, status=500)
            return

        self.send_response(404)
        self.end_headers()


def start_bridge(jarvis_instance, port: int = PORT):
    """Arranca el servidor HTTP en un hilo daemon."""
    _Handler.jarvis = jarvis_instance
    server = ThreadingHTTPServer(("0.0.0.0", port), _Handler)
    t = threading.Thread(target=server.serve_forever, daemon=True, name="bridge-server")
    t.start()
    try:
        from modulos.logger import log
        log.info(f"[Bridge] Servidor HTTP en :{port}")
    except Exception:
        print(f"[Bridge] Servidor HTTP en :{port}")
    return server
