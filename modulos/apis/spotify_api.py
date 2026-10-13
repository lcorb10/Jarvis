# modulos/apis/spotify_api.py
import subprocess
import urllib.parse
import webbrowser
from modulos.apis.base import APIBase
from modulos.logger import log


class APISpotify(APIBase):
    nombre = "spotify"
    descripcion = "Busca y reproduce canciones o artistas en Spotify"
    requiere_key = False

    PALABRAS_ACCION = [
        "coloca en spotify", "coloca musica en spotify", "coloca música en spotify",
        "pon en spotify", "reproduce en spotify", "busca en spotify",
        "ponme en spotify", "abre spotify y pon", "pon la canción en spotify",
        "pon la cancion en spotify", "en spotify pon", "en spotify coloca",
        "en spotify busca", "spotify pon", "quiero escuchar en spotify",
        "en spotify",  # catch-all: cualquier cosa que mencione "en spotify"
    ]

    PALABRAS_EXCLUIR = [
        "para qué", "para que", "qué es", "que es",
        "cómo funciona", "como funciona", "api de spotify",
        "en youtube",
    ]

    def activado(self):
        return True

    def detectar_intencion(self, texto):
        texto_lower = texto.lower()
        if any(p in texto_lower for p in self.PALABRAS_EXCLUIR):
            return False
        return any(p in texto_lower for p in self.PALABRAS_ACCION)

    def ejecutar(self, texto):
        termino = self._extraer_termino(texto)
        if not termino or len(termino) < 2:
            return "¿Qué quiere reproducir en Spotify?"
        return self._reproducir(termino)

    def _extraer_termino(self, texto):
        texto_lower = texto.lower()
        for p in sorted(self.PALABRAS_ACCION, key=len, reverse=True):
            texto_lower = texto_lower.replace(p, "").strip()
        texto_lower = texto_lower.replace("en spotify", "").replace("spotify", "").strip()
        return texto_lower.strip()

    def _reproducir(self, termino):
        query = urllib.parse.quote(termino)
        uri = f"spotify:search:{query}"
        try:
            subprocess.Popen(
                ["cmd", "/c", "start", "", uri],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            log.info(f"[Spotify] Reproduciendo: {termino}")
            return f"Reproduciendo {termino} en Spotify."
        except Exception as e:
            log.error(f"[Spotify] Error: {e}")
            try:
                webbrowser.open(uri)
                return f"Abriendo Spotify con {termino}."
            except Exception:
                return "No pude abrir Spotify."
