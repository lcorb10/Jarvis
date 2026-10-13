# modulos/apis/traductor.py
import requests
from modulos.apis.base import APIBase
from modulos.logger import log


class APITraductor(APIBase):
    nombre = "traductor"
    descripcion = "Traduce texto (MyMemory, gratuito)"
    requiere_key = False

    PALABRAS = [
        "traduce", "traducir", "cómo se dice", "como se dice",
        "en inglés", "en ingles", "en francés", "en frances",
        "en portugués", "en portugues", "en alemán", "en aleman",
        "en italiano", "traducción", "traduccion",
    ]

    IDIOMAS = {
        "inglés": "en", "ingles": "en",
        "francés": "fr", "frances": "fr",
        "portugués": "pt", "portugues": "pt",
        "alemán": "de", "aleman": "de",
        "italiano": "it", "chino": "zh",
        "japonés": "ja", "japones": "ja",
    }

    def activado(self):
        return True

    def detectar_intencion(self, texto):
        return any(p in texto.lower() for p in self.PALABRAS)

    def ejecutar(self, texto):
        texto_lower = texto.lower()
        idioma_destino = "en"
        for nombre, codigo in self.IDIOMAS.items():
            if nombre in texto_lower:
                idioma_destino = codigo
                break

        termino = texto_lower
        for p in sorted(self.PALABRAS, key=len, reverse=True):
            termino = termino.replace(p, "").strip()
        for nombre in self.IDIOMAS:
            termino = termino.replace(f"en {nombre}", "").strip()

        if not termino:
            return "¿Qué quiere que traduzca?"

        try:
            resp = requests.get(
                "https://api.mymemory.translated.net/get",
                params={"q": termino, "langpair": f"es|{idioma_destino}"},
                timeout=5,
            )
            traduccion = resp.json()["responseData"]["translatedText"]
            return f'"{termino}" en {idioma_destino} es: {traduccion}'
        except Exception as e:
            log.error(f"Error traductor: {e}")
            return "No pude traducir eso ahora mismo."
