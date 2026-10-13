# modulos/apis/gestor_apis.py
from modulos.apis.clima import APIClima
from modulos.apis.youtube_api import APIYouTube
from modulos.apis.spotify_api import APISpotify
from modulos.apis.noticias import APINoticias
from modulos.apis.traductor import APITraductor
from modulos.apis.matematica import APIMatematica
from modulos.logger import log


class GestorAPIs:
    def __init__(self):
        self.apis = [
            APIMatematica(),   # primero — sin red
            APIClima(),
            APISpotify(),      # antes de YouTube para capturar "en spotify"
            APIYouTube(),
            APINoticias(),
            APITraductor(),
        ]
        for api in self.apis:
            estado = "✅" if api.activado() else "⚠️ (sin key)"
            log.info(f"API {api.nombre}: {estado}")

    def detectar_y_ejecutar(self, texto: str):
        for api in self.apis:
            if api.activado() and api.detectar_intencion(texto):
                log.info(f"API seleccionada: {api.nombre}")
                try:
                    return api.ejecutar(texto)
                except Exception as e:
                    log.error(f"Error en API {api.nombre}: {e}")
        return None

    def agregar_api(self, api_instance):
        self.apis.append(api_instance)
        log.info(f"API agregada: {api_instance.nombre}")

    def listar_apis(self):
        return [(a.nombre, a.descripcion, a.activado()) for a in self.apis]
