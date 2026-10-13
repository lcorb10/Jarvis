# modulos/tools/registry.py
"""
Registro central de tools que la IA puede invocar.

La IA recibe la lista de tools disponibles en el system prompt y emite JSON:
    {"tools": ["open_app:spotify", "youtube_search:musica relajante"], "respuesta": "..."}

El despachador (jarvis_core) ejecuta cada tool y, si hay resultado relevante,
re-consulta la IA para que genere una respuesta natural con el contexto.
"""
from typing import Callable, Optional
from modulos.logger import log


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, dict] = {}

    def register(self, name: str, fn: Callable[[str], str], description: str, ejemplo: str = ""):
        self._tools[name] = {"fn": fn, "desc": description, "ejemplo": ejemplo}

    def call(self, name: str, arg: str) -> Optional[str]:
        tool = self._tools.get(name)
        if not tool:
            log.warning(f"[ToolRegistry] Tool desconocida: {name}")
            return None
        try:
            return tool["fn"](arg)
        except Exception as e:
            log.error(f"[ToolRegistry] Error en '{name}': {e}")
            return f"Error ejecutando {name}: {e}"

    def list_for_prompt(self) -> str:
        """Genera la sección de tools para el system prompt de la IA."""
        lines = []
        for name, t in self._tools.items():
            ej = f" → ej: {t['ejemplo']}" if t["ejemplo"] else ""
            lines.append(f"- {name}: {t['desc']}{ej}")
        return "\n".join(lines)

    def names(self) -> list[str]:
        return list(self._tools.keys())


_registry: Optional[ToolRegistry] = None


def get_registry() -> ToolRegistry:
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry


def init_tools(control, apis):
    """Registra todas las tools usando las instancias del core."""
    reg = get_registry()

    # ── App control ──────────────────────────────────────────────────────────
    def _open_app(arg: str) -> str:
        return control.abrir_app(arg.strip().lower()) or f"No encontré {arg}."

    def _close_app(arg: str) -> str:
        return control.cerrar_app(arg.strip().lower()) or f"No encontré {arg}."

    reg.register(
        "open_app", _open_app,
        "Abre una aplicación instalada. Apps válidas: spotify, chrome, discord, vscode, youtube, netflix, capcut, calculadora, notepad, valorant, league, steam, etc",
        "open_app:spotify",
    )
    reg.register(
        "close_app", _close_app,
        "Cierra una aplicación abierta",
        "close_app:chrome",
    )

    # ── Búsqueda web ─────────────────────────────────────────────────────────
    def _youtube_search(arg: str) -> str:
        term = arg.strip()
        if not term:
            return "¿Qué quiere que reproduzca en YouTube, señor?"
        return control.buscar_youtube(term)

    def _google_search(arg: str) -> str:
        return control.buscar_google(arg.strip())

    def _spotify_play(arg: str) -> str:
        term = arg.strip()
        if not term:
            return "¿Qué canción o artista quiere reproducir en Spotify, señor?"
        return control.reproducir_spotify(term)

    reg.register(
        "youtube_search", _youtube_search,
        "Reproduce el primer video de YouTube que coincida (música, videos, etc). SIEMPRE incluye el nombre exacto del video/canción/artista como argumento. Si el usuario no especificó qué reproducir, pregúntale en lugar de llamar esta tool.",
        "youtube_search:musica relajante lofi",
    )
    reg.register(
        "google_search", _google_search,
        "Abre Google con la búsqueda solicitada",
        "google_search:noticias colombia hoy",
    )
    reg.register(
        "spotify_play", _spotify_play,
        "Busca y reproduce una canción o artista en Spotify. SIEMPRE incluye el nombre de la canción o artista como argumento. Si el usuario no especificó qué reproducir, pregúntale en lugar de llamar esta tool.",
        "spotify_play:bad bunny un verano sin ti",
    )

    # ── Web search (scraping para responder con contexto) ────────────────────
    def _web_search(arg: str) -> str:
        try:
            from modulos.tools.web_search import web_search
            return web_search({"query": arg.strip()}) or ""
        except Exception as e:
            return f"Error web_search: {e}"

    reg.register(
        "web_search", _web_search,
        "Busca información en internet y devuelve un resumen (úsala cuando el usuario pregunta datos que no sabes)",
        "web_search:cuál es la capital de Australia",
    )

    # ── Pantalla ─────────────────────────────────────────────────────────────
    def _screen_process(arg: str) -> str:
        try:
            from modulos.tools.screen_processor import screen_process
            return screen_process({"text": arg.strip() or "¿Qué hay en pantalla?"}) or ""
        except Exception as e:
            return f"Error screen_process: {e}"

    reg.register(
        "screen_process", _screen_process,
        "Captura y analiza la pantalla del usuario (úsala cuando pregunte qué ve, qué hay en pantalla, etc)",
        "screen_process:qué aplicación tengo abierta",
    )

    # ── Sistema ──────────────────────────────────────────────────────────────
    def _volume(arg: str) -> str:
        a = arg.strip().lower()
        if a in ("subir", "up", "+", "más", "mas"):
            return control.cambiar_volumen("subir")
        if a in ("bajar", "down", "-", "menos"):
            return control.cambiar_volumen("bajar")
        if a in ("mute", "silenciar", "quitar"):
            return control.cambiar_volumen("bajar")
        return control.cambiar_volumen(a)

    reg.register(
        "volume", _volume,
        "Sube o baja el volumen del sistema. Argumentos: subir, bajar",
        "volume:subir",
    )

    # ── APIs especializadas ──────────────────────────────────────────────────
    def _weather(arg: str) -> str:
        for api in apis.apis:
            if api.nombre == "clima" and api.activado():
                return api.ejecutar(f"clima en {arg.strip() or 'aquí'}")
        return "Servicio de clima no disponible."

    def _math(arg: str) -> str:
        for api in apis.apis:
            if api.nombre == "matematica" and api.activado():
                return api.ejecutar(arg.strip())
        return "Servicio matemático no disponible."

    def _news(arg: str) -> str:
        for api in apis.apis:
            if api.nombre == "noticias" and api.activado():
                return api.ejecutar(f"noticias de {arg.strip() or 'hoy'}")
        return "Servicio de noticias no disponible."

    def _translate(arg: str) -> str:
        for api in apis.apis:
            if api.nombre == "traductor" and api.activado():
                return api.ejecutar(f"traduce {arg.strip()}")
        return "Servicio de traductor no disponible."

    reg.register("weather", _weather, "Consulta el clima de una ciudad", "weather:Bogotá")
    reg.register("math", _math, "Resuelve operaciones matemáticas", "math:integral de x^2")
    reg.register("news", _news, "Trae titulares de noticias", "news:tecnología")
    reg.register("translate", _translate, "Traduce texto", "translate:hello al español")

    # ── Archivos ─────────────────────────────────────────────────────────────
    def _create_file(arg: str) -> str:
        """
        Formato del argumento: "nombre.txt|contenido del archivo"
        Opcionalmente: "ruta/nombre.txt|contenido"
        Si no hay '|', crea el archivo vacío con ese nombre.
        """
        try:
            from modulos.tools.file_controller import file_controller
            if "|" in arg:
                nombre_parte, contenido = arg.split("|", 1)
            else:
                nombre_parte, contenido = arg.strip(), ""
            nombre_parte = nombre_parte.strip()
            # Separar carpeta destino si viene con /
            if "/" in nombre_parte or "\\" in nombre_parte:
                import os as _os
                carpeta = _os.path.dirname(nombre_parte)
                nombre = _os.path.basename(nombre_parte)
            else:
                carpeta = "desktop"
                nombre = nombre_parte
            return file_controller({
                "action": "create_file",
                "path": carpeta,
                "name": nombre,
                "content": contenido.strip(),
            })
        except Exception as e:
            return f"Error creando archivo: {e}"

    def _create_folder(arg: str) -> str:
        """Formato: "nombre_carpeta" o "ruta/nombre_carpeta"."""
        try:
            from modulos.tools.file_controller import file_controller
            arg = arg.strip()
            import os as _os
            carpeta_base = _os.path.dirname(arg) if ("/" in arg or "\\" in arg) else "desktop"
            nombre = _os.path.basename(arg) if ("/" in arg or "\\" in arg) else arg
            return file_controller({
                "action": "create_folder",
                "path": carpeta_base,
                "name": nombre,
            })
        except Exception as e:
            return f"Error creando carpeta: {e}"

    def _read_file(arg: str) -> str:
        try:
            from modulos.tools.file_controller import file_controller
            return file_controller({"action": "read", "path": arg.strip()})
        except Exception as e:
            return f"Error leyendo archivo: {e}"

    def _list_files(arg: str) -> str:
        try:
            from modulos.tools.file_controller import file_controller
            return file_controller({"action": "list", "path": arg.strip() or "desktop"})
        except Exception as e:
            return f"Error listando archivos: {e}"

    reg.register(
        "create_file", _create_file,
        "Crea un archivo de texto en el escritorio (o ruta indicada). Formato: 'nombre.txt|contenido'. "
        "Úsala cuando el usuario pida crear, guardar o escribir un archivo.",
        "create_file:notas.txt|Comprar leche\\nLlamar a mamá",
    )
    reg.register(
        "create_folder", _create_folder,
        "Crea una carpeta en el escritorio (o ruta indicada). Úsala cuando el usuario pida crear una carpeta.",
        "create_folder:MisProyectos",
    )
    reg.register(
        "read_file", _read_file,
        "Lee el contenido de un archivo. Argumento: ruta del archivo o 'desktop/nombre.txt'.",
        "read_file:desktop/notas.txt",
    )
    reg.register(
        "list_files", _list_files,
        "Lista los archivos de una carpeta. Argumentos: desktop, downloads, documents, o ruta absoluta.",
        "list_files:desktop",
    )

    log.info(f"[ToolRegistry] {len(reg.names())} tools registradas: {reg.names()}")
    return reg
