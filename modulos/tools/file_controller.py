# modulos/tools/file_controller.py
"""
Gestión completa de archivos y carpetas.
Requiere: send2trash (opcional)
"""
import os
import shutil
import platform
from pathlib import Path
from datetime import datetime
from modulos.logger import log

try:
    import send2trash
    _TRASH = True
except ImportError:
    _TRASH = False

_OS = platform.system()

_SAFE_ROOTS = [Path.home()]


def _is_safe(target: Path) -> bool:
    try:
        resolved = target.resolve()
        return any(
            resolved == r.resolve() or resolved.is_relative_to(r.resolve())
            for r in _SAFE_ROOTS
        )
    except Exception:
        return False


def _resolve_path(path_str: str) -> Path:
    """Convierte atajos como 'desktop', 'downloads', etc. a rutas reales."""
    atajos = {
        "desktop":   Path.home() / "Desktop",
        "downloads": Path.home() / "Downloads",
        "documents": Path.home() / "Documents",
        "documents": Path.home() / "Documentos",
        "pictures":  Path.home() / "Pictures",
        "music":     Path.home() / "Music",
        "videos":    Path.home() / "Videos",
        "home":      Path.home(),
    }
    lower = path_str.lower().strip()
    for atajo, ruta in atajos.items():
        if lower == atajo:
            return ruta
    p = Path(path_str)
    return p if p.is_absolute() else Path.home() / "Desktop" / path_str


def file_controller(parameters: dict) -> str:
    action = parameters.get("action", "").lower()

    if action == "list":
        return _list(parameters.get("path", "desktop"))
    elif action in ("write", "create_file"):
        return _write(parameters.get("path", "desktop"),
                      parameters.get("name", "archivo.txt"),
                      parameters.get("content", ""))
    elif action == "create_folder":
        return _create_folder(parameters.get("path", "desktop"),
                              parameters.get("name", "nueva_carpeta"))
    elif action == "read":
        return _read(parameters.get("path", ""))
    elif action == "delete":
        return _delete(parameters.get("path", ""))
    elif action == "move":
        return _move(parameters.get("path", ""), parameters.get("destination", ""))
    elif action == "copy":
        return _copy(parameters.get("path", ""), parameters.get("destination", ""))
    elif action == "rename":
        return _rename(parameters.get("path", ""), parameters.get("new_name", ""))
    elif action == "find":
        return _find(parameters.get("path", "desktop"),
                     parameters.get("name", ""),
                     parameters.get("extension", ""))
    elif action == "largest":
        return _largest(parameters.get("path", "desktop"),
                        parameters.get("count", 5))
    elif action == "disk_usage":
        return _disk_usage(parameters.get("path", "desktop"))
    elif action == "info":
        return _info(parameters.get("path", ""))
    elif action == "organize_desktop":
        return _organize_desktop()
    else:
        return f"Acción desconocida: {action}"


def _list(path_str: str) -> str:
    path = _resolve_path(path_str)
    if not path.exists():
        return f"La carpeta no existe: {path}"
    items = sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
    if not items:
        return f"La carpeta '{path.name}' está vacía."
    lineas = [f"📁 {path.name} ({len(items)} elementos):"]
    for item in items[:30]:
        icono = "📄" if item.is_file() else "📁"
        size = ""
        if item.is_file():
            s = item.stat().st_size
            size = f" ({s // 1024}KB)" if s > 1024 else f" ({s}B)"
        lineas.append(f"  {icono} {item.name}{size}")
    if len(items) > 30:
        lineas.append(f"  ... y {len(items) - 30} más")
    return "\n".join(lineas)


def _write(path_str: str, name: str, content: str) -> str:
    folder = _resolve_path(path_str)
    folder.mkdir(parents=True, exist_ok=True)
    filepath = folder / name
    if not _is_safe(filepath):
        return "Ruta no permitida por seguridad."
    try:
        filepath.write_text(content, encoding="utf-8")
        return f"Archivo guardado: {filepath}"
    except Exception as e:
        log.error(f"file write error: {e}")
        return f"Error guardando archivo: {e}"


def _create_folder(path_str: str, name: str) -> str:
    base = _resolve_path(path_str)
    nueva = base / name
    if not _is_safe(nueva):
        return "Ruta no permitida."
    nueva.mkdir(parents=True, exist_ok=True)
    return f"Carpeta creada: {nueva}"


def _read(path_str: str) -> str:
    path = _resolve_path(path_str)
    if not path.exists():
        return f"Archivo no encontrado: {path}"
    if not path.is_file():
        return f"No es un archivo: {path}"
    try:
        texto = path.read_text(encoding="utf-8", errors="replace")
        if len(texto) > 2000:
            return texto[:2000] + f"\n\n[... {len(texto) - 2000} caracteres más]"
        return texto
    except Exception as e:
        return f"Error leyendo archivo: {e}"


def _delete(path_str: str) -> str:
    path = _resolve_path(path_str)
    if not path.exists():
        return f"No existe: {path}"
    if not _is_safe(path):
        return "Ruta no permitida por seguridad."
    try:
        if _TRASH:
            send2trash.send2trash(str(path))
            return f"Movido a papelera: {path.name}"
        else:
            if path.is_file():
                path.unlink()
            else:
                shutil.rmtree(path)
            return f"Eliminado: {path.name}"
    except Exception as e:
        return f"Error eliminando: {e}"


def _move(src_str: str, dst_str: str) -> str:
    src = _resolve_path(src_str)
    dst = _resolve_path(dst_str)
    if not src.exists():
        return f"Origen no existe: {src}"
    if not _is_safe(src) or not _is_safe(dst):
        return "Ruta no permitida."
    try:
        destino = dst / src.name if dst.is_dir() else dst
        shutil.move(str(src), str(destino))
        return f"Movido: {src.name} → {destino.parent.name}"
    except Exception as e:
        return f"Error moviendo: {e}"


def _copy(src_str: str, dst_str: str) -> str:
    src = _resolve_path(src_str)
    dst = _resolve_path(dst_str)
    if not src.exists():
        return f"Origen no existe: {src}"
    if not _is_safe(src) or not _is_safe(dst):
        return "Ruta no permitida."
    try:
        dst.mkdir(parents=True, exist_ok=True)
        if src.is_file():
            shutil.copy2(str(src), str(dst / src.name))
        else:
            shutil.copytree(str(src), str(dst / src.name))
        return f"Copiado: {src.name} → {dst.name}"
    except Exception as e:
        return f"Error copiando: {e}"


def _rename(path_str: str, new_name: str) -> str:
    path = _resolve_path(path_str)
    if not path.exists():
        return f"No existe: {path}"
    if not _is_safe(path):
        return "Ruta no permitida."
    nuevo = path.parent / new_name
    try:
        path.rename(nuevo)
        return f"Renombrado: {path.name} → {new_name}"
    except Exception as e:
        return f"Error renombrando: {e}"


def _find(path_str: str, name: str = "", extension: str = "") -> str:
    base = _resolve_path(path_str)
    if not base.exists():
        return f"Carpeta no existe: {base}"
    resultados = []
    patron = f"*{name}*" if name else f"*{extension}" if extension else "*"
    try:
        for p in base.rglob(patron):
            if (not name or name.lower() in p.name.lower()) and \
               (not extension or p.suffix.lower() == extension.lower()):
                resultados.append(str(p))
            if len(resultados) >= 20:
                break
    except Exception:
        pass
    if not resultados:
        return f"No encontré archivos con '{name or extension}'"
    return "Encontré:\n" + "\n".join(resultados[:20])


def _largest(path_str: str, count=5) -> str:
    base = _resolve_path(path_str)
    if not base.exists():
        return f"No existe: {base}"
    archivos = []
    try:
        for p in base.rglob("*"):
            if p.is_file():
                try:
                    archivos.append((p.stat().st_size, p))
                except Exception:
                    pass
    except Exception:
        pass
    archivos.sort(reverse=True)
    if not archivos:
        return "No encontré archivos."
    lineas = [f"Top {min(count, len(archivos))} archivos más grandes:"]
    for size, p in archivos[:int(count)]:
        mb = size / (1024 * 1024)
        lineas.append(f"  {mb:.2f}MB — {p.name}")
    return "\n".join(lineas)


def _disk_usage(path_str: str) -> str:
    path = _resolve_path(path_str)
    try:
        usage = shutil.disk_usage(str(path))
        total = usage.total / (1024 ** 3)
        used = usage.used / (1024 ** 3)
        free = usage.free / (1024 ** 3)
        pct = (usage.used / usage.total) * 100
        return f"Disco: {used:.1f}GB usados de {total:.1f}GB ({pct:.0f}%). Libre: {free:.1f}GB."
    except Exception as e:
        return f"Error obteniendo uso de disco: {e}"


def _info(path_str: str) -> str:
    path = _resolve_path(path_str)
    if not path.exists():
        return f"No existe: {path}"
    stat = path.stat()
    size = stat.st_size
    mod = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
    tipo = "Archivo" if path.is_file() else "Carpeta"
    return f"{tipo}: {path.name}\nTamaño: {size // 1024}KB\nModificado: {mod}\nRuta: {path}"


def _organize_desktop() -> str:
    desktop = Path.home() / "Desktop"
    categorias = {
        "Imágenes":    [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg"],
        "Documentos":  [".pdf", ".docx", ".doc", ".txt", ".xlsx", ".pptx", ".csv"],
        "Videos":      [".mp4", ".mkv", ".avi", ".mov", ".wmv"],
        "Música":      [".mp3", ".wav", ".flac", ".aac", ".ogg"],
        "Código":      [".py", ".js", ".ts", ".html", ".css", ".json", ".xml", ".java", ".cpp"],
        "Comprimidos": [".zip", ".rar", ".7z", ".tar", ".gz"],
        "Ejecutables": [".exe", ".msi", ".bat", ".cmd"],
    }
    movidos = 0
    errores = 0
    for archivo in desktop.iterdir():
        if archivo.is_dir() or archivo.suffix == ".lnk":
            continue
        destino_cat = None
        for cat, exts in categorias.items():
            if archivo.suffix.lower() in exts:
                destino_cat = cat
                break
        if not destino_cat:
            destino_cat = "Otros"
        carpeta_destino = desktop / destino_cat
        carpeta_destino.mkdir(exist_ok=True)
        try:
            shutil.move(str(archivo), str(carpeta_destino / archivo.name))
            movidos += 1
        except Exception:
            errores += 1
    return f"Desktop organizado: {movidos} archivos movidos, {errores} errores."
