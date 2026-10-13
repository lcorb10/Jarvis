# modulos/apis/youtube_api.py
import os
import re
import subprocess
import urllib.parse
import requests
from modulos.apis.base import APIBase
from modulos.logger import log


class APIYouTube(APIBase):
    nombre = "youtube"
    descripcion = "Busca y reproduce videos de YouTube"
    requiere_key = False

    PALABRAS_ACCION = [
        "coloca en youtube", "coloca musica en youtube", "coloca música en youtube",
        "busca en youtube", "pon en youtube", "reproduce en youtube",
        "busca el video de", "busca la cancion", "busca la canción",
        "pon la cancion", "pon la canción", "quiero escuchar",
        "pon música", "pon musica", "busca la música", "busca la musica",
        "ponme la cancion", "ponme la canción", "busca el video",
        "en youtube busca", "abre youtube y busca",
        "en youtube",  # catch-all para "X en youtube"
    ]

    PALABRAS_EXCLUIR = [
        "para qué", "para que", "qué es", "que es",
        "cómo funciona", "como funciona", "api de youtube",
        "en spotify",
    ]

    def __init__(self):
        self.api_key = os.getenv("YOUTUBE_API_KEY", "")
        self.chrome = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

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
            return "¿Qué quiere buscar en YouTube?"
        if self.api_key:
            return self._buscar_con_api(termino)
        return self._buscar_primer_video(termino)

    def _extraer_termino(self, texto):
        texto_lower = texto.lower()
        for p in sorted(self.PALABRAS_ACCION, key=len, reverse=True):
            texto_lower = texto_lower.replace(p, "").strip()
        # quitar "en youtube" residual
        texto_lower = texto_lower.replace("en youtube", "").replace("youtube", "").strip()
        return texto_lower.strip()

    def _abrir_url(self, url):
        try:
            subprocess.Popen([self.chrome, url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            import webbrowser
            webbrowser.open(url)

    def _buscar_primer_video(self, termino):
        """Scrapea la página de resultados de YouTube para abrir el primer video directamente."""
        try:
            query = urllib.parse.quote(termino)
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            resp = requests.get(
                f"https://www.youtube.com/results?search_query={query}",
                headers=headers,
                timeout=6,
            )
            # El primer videoId aparece en el JSON embebido de la página
            match = re.search(r'"videoId":"([a-zA-Z0-9_-]{11})"', resp.text)
            if match:
                vid_id = match.group(1)
                url = f"https://www.youtube.com/watch?v={vid_id}"
                self._abrir_url(url)
                return f"Reproduciendo {termino} en YouTube."
        except Exception as e:
            log.warning(f"[YouTube] Scraping falló: {e}")
        # Fallback: abrir resultados
        url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(termino)}"
        self._abrir_url(url)
        return f"Buscando {termino} en YouTube."

    def _buscar_con_api(self, termino):
        try:
            resp = requests.get(
                "https://www.googleapis.com/youtube/v3/search",
                params={"part": "snippet", "q": termino, "maxResults": 1,
                        "type": "video", "key": self.api_key},
                timeout=5,
            )
            items = resp.json().get("items", [])
            if items:
                vid_id = items[0]["id"]["videoId"]
                titulo = items[0]["snippet"]["title"]
                url = f"https://www.youtube.com/watch?v={vid_id}"
                self._abrir_url(url)
                return f"Reproduciendo: {titulo[:50]}"
            return self._buscar_primer_video(termino)
        except Exception as e:
            log.error(f"YouTube API error: {e}")
            return self._buscar_primer_video(termino)
