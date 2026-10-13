# modulos/apis/clima.py
import requests
from modulos.apis.base import APIBase
from modulos.logger import log


class APIClima(APIBase):
    nombre = "clima"
    descripcion = "Clima actual de cualquier ciudad (Open-Meteo, gratuito)"
    requiere_key = False

    PALABRAS = [
        "clima", "tiempo", "temperatura", "lluvia", "sol", "frío", "frio",
        "calor", "nublado", "pronóstico", "pronostico", "va a llover",
        "qué temperatura", "que temperatura", "cómo está el tiempo",
    ]

    CIUDADES = {
        "barranquilla": (10.9685, -74.7813),
        "bogota":       (4.7110, -74.0721),
        "medellin":     (6.2442, -75.5812),
        "cali":         (3.4516, -76.5320),
        "cartagena":    (10.3910, -75.4794),
        "madrid":       (40.4168, -3.7038),
        "buenos aires": (-34.6037, -58.3816),
        "mexico":       (19.4326, -99.1332),
        "new york":     (40.7128, -74.0060),
        "miami":        (25.7617, -80.1918),
        "bogotá":       (4.7110, -74.0721),
        "medellín":     (6.2442, -75.5812),
    }

    def activado(self):
        return True

    def detectar_intencion(self, texto):
        return any(p in texto.lower() for p in self.PALABRAS)

    def ejecutar(self, texto):
        ciudad = self._extraer_ciudad(texto)
        return self._obtener_clima(ciudad)

    def _extraer_ciudad(self, texto):
        texto = texto.lower()
        for ciudad in self.CIUDADES:
            if ciudad in texto:
                return ciudad
        return "barranquilla"

    def _obtener_clima(self, ciudad):
        coords = self.CIUDADES.get(ciudad.lower())
        if not coords:
            return f"No tengo datos de {ciudad}."
        lat, lon = coords
        try:
            url = (
                f"https://api.open-meteo.com/v1/forecast"
                f"?latitude={lat}&longitude={lon}"
                f"&current=temperature_2m,weathercode,windspeed_10m,relativehumidity_2m"
                f"&timezone=auto"
            )
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
            datos = resp.json()["current"]
            temp = datos["temperature_2m"]
            humedad = datos["relativehumidity_2m"]
            viento = datos["windspeed_10m"]
            desc = self._codigo_desc(datos["weathercode"])
            return f"En {ciudad.title()}: {desc}, {temp}°C, humedad {humedad}%, viento {viento} km/h."
        except Exception as e:
            log.error(f"Error clima: {e}")
            return "No pude obtener el clima en este momento."

    def _codigo_desc(self, codigo):
        return {
            0: "cielo despejado", 1: "mayormente despejado",
            2: "parcialmente nublado", 3: "nublado",
            45: "con niebla", 51: "llovizna ligera",
            61: "lluvia ligera", 63: "lluvia moderada", 65: "lluvia intensa",
            80: "chubascos", 95: "tormenta eléctrica",
        }.get(codigo, "condiciones variables")
