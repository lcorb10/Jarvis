# modulos/control_sistema.py
import subprocess
import psutil
import webbrowser
import urllib.parse
from modulos.detector_rutas import DetectorRutas

class ControlSistema:
    def __init__(self):
        self.detector = DetectorRutas()
        self.CHROME = self.detector.obtener_ruta("chrome") or r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        self.DISCORD = self.detector.obtener_ruta("discord") or r"C:\Users\{usuario}\AppData\Local\Discord\app-1.0.9233\Discord.exe"
        self.STEAM = self.detector.obtener_ruta("steam") or r"C:\Program Files (x86)\Steam\steam.exe"
        self.EA_DESKTOP = self.detector.obtener_ruta("ea_desktop") or r"C:\Program Files\Electronic Arts\EA Desktop\EADesktop.exe"

    APPS = {
        "chrome": {
            "alias": ["chrome", "google", "google chrome", "crome", "navegador", "browser", "goo"],
            "busca_automatica": True
        },
        "discord": {
            "alias": ["discord", "discor", "disc", "doscord"],
            "busca_automatica": True
        },
        "spotify": {
            "alias": ["spotify", "spotifi", "espotify", "musica"],
            "protocolo": "spotify:"
        },
        "steam": {
            "alias": ["steam", "juegos steam"],
            "busca_automatica": True
        },
        "ea": {
            "alias": ["ea", "ea desktop", "electronic arts"],
            "busca_automatica": True
        },
        "fc26": {
            "alias": ["fc26", "fifa", "futbol"],
            "busca_automatica": True,
            "launcher": "ea"
        },
        "brawlhalla": {
            "alias": ["brawlhalla", "brawl"],
            "steam_id": "291550"
        },
        # ... resto de apps igual que antes
    }

    def abrir_app(self, nombre_app):
        datos = self.APPS.get(nombre_app)
        if not datos:
            return f"App {nombre_app} no reconocida."

        # Apps por protocolo
        if "protocolo" in datos:
            try:
                subprocess.Popen(["cmd", "/c", "start", datos["protocolo"]])
                return f"Abriendo {nombre_app}."
            except Exception:
                return f"No pude abrir {nombre_app}."

        # Apps por Steam ID
        if "steam_id" in datos:
            try:
                subprocess.Popen([self.STEAM, "-applaunch", datos["steam_id"]])
                return f"Abriendo {nombre_app} desde Steam."
            except Exception:
                return f"No pude abrir {nombre_app}."

        # Apps con búsqueda automática
        if datos.get("busca_automatica"):
            if nombre_app == "chrome" and self.CHROME:
                try:
                    subprocess.Popen([self.CHROME])
                    return f"Abriendo Chrome."
                except Exception:
                    return "No pude abrir Chrome."
            
            elif nombre_app == "discord" and self.DISCORD:
                try:
                    subprocess.Popen([self.DISCORD])
                    return f"Abriendo Discord."
                except Exception:
                    return "No pude abrir Discord."
            
            elif nombre_app == "steam" and self.STEAM:
                try:
                    subprocess.Popen([self.STEAM])
                    return f"Abriendo Steam."
                except Exception:
                    return "No pude abrir Steam."
            
            elif nombre_app == "ea" and self.EA_DESKTOP:
                try:
                    subprocess.Popen([self.EA_DESKTOP])
                    return f"Abriendo EA Desktop."
                except Exception:
                    return "No pude abrir EA Desktop."

        return f"No pude abrir {nombre_app}. Revisa la configuración."