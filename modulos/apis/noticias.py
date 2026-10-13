# modulos/apis/noticias.py
import os
import requests
from modulos.apis.base import APIBase
from modulos.logger import log


class APINoticias(APIBase):
    nombre = "noticias"
    descripcion = "Noticias recientes vía NewsAPI"
    requiere_key = True

    PALABRAS = [
        "noticias", "qué pasó", "que paso", "últimas noticias",
        "ultimas noticias", "actualidad", "qué hay de nuevo",
        "que hay de nuevo", "dime las noticias",
    ]

    def __init__(self):
        self.api_key = os.getenv("NEWS_API_KEY", "")

    def activado(self):
        return bool(self.api_key)

    def detectar_intencion(self, texto):
        return any(p in texto.lower() for p in self.PALABRAS)

    def ejecutar(self, texto):
        try:
            url = "https://newsapi.org/v2/top-headlines"
            params = {"language": "es", "pageSize": 3, "apiKey": self.api_key}
            resp = requests.get(url, params=params, timeout=5)
            articulos = resp.json().get("articles", [])
            if not articulos:
                params["language"] = "en"
                articulos = requests.get(url, params=params, timeout=5).json().get("articles", [])
            titulos = [a["title"].split(" - ")[0] for a in articulos[:3] if a.get("title") and "[Removed]" not in a["title"]]
            if not titulos:
                return "No encontré noticias disponibles."
            return f"Últimas noticias: {titulos[0]}. También: {titulos[1]}." if len(titulos) > 1 else f"Última noticia: {titulos[0]}."
        except Exception as e:
            log.error(f"Error noticias: {e}")
            return "No pude obtener las noticias."
