# modulos/detector_rutas.py
import subprocess
import json
import os
import sys
from pathlib import Path


class DetectorRutas:
    def __init__(self, archivo_config="config.json"):
        self.archivo_config = archivo_config
        self.config = self._cargar_config()

    def _cargar_config(self):
        if os.path.exists(self.archivo_config):
            try:
                with open(self.archivo_config, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return self._config_default()

    def _config_default(self):
        return {
            "paths": {"chrome": "", "discord": "", "steam": "", "ea_desktop": "", "python": sys.executable},
            "ollama": {"modelo": "mistral", "url": "http://localhost:11434/api/chat", "activo": False},
            "gemini": {"modelo_chat": "gemini-2.5-flash", "activo": True},
            "vosk": {"modelo_ruta": "modelos/vosk-es"},
        }

    def _guardar_config(self):
        with open(self.archivo_config, "w", encoding="utf-8") as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)

    def buscar_con_powershell(self, nombre_app, patrones):
        try:
            for patron in patrones:
                cmd = f'Get-ChildItem "{patron}" -Recurse -Filter "*.exe" -ErrorAction SilentlyContinue | Select-Object -First 1 FullName'
                resultado = subprocess.run(
                    ["powershell", "-NoProfile", "-Command", cmd],
                    capture_output=True, text=True, timeout=10,
                )
                if resultado.stdout.strip():
                    ruta = resultado.stdout.strip().split("\n")[-1]
                    if ruta and os.path.exists(ruta):
                        return ruta
        except Exception:
            pass
        return ""

    def detectar_todas_las_rutas(self):
        rutas = {
            "chrome":  ["C:\\Program Files\\Google\\Chrome", "C:\\Program Files (x86)\\Google\\Chrome"],
            "discord": [f"{os.path.expanduser('~')}\\AppData\\Local\\Discord"],
            "steam":   ["C:\\Program Files\\Steam", "C:\\Program Files (x86)\\Steam"],
            "ea_desktop": ["C:\\Program Files\\Electronic Arts\\EA Desktop"],
        }
        for app, patrones in rutas.items():
            ruta = self.buscar_con_powershell(app, patrones)
            if ruta:
                self.config["paths"][app] = ruta
        self._guardar_config()
        return self.config

    def verificar_ollama(self):
        try:
            import requests
            resp = requests.get("http://localhost:11434/api/tags", timeout=2)
            if resp.status_code == 200:
                modelos = resp.json()
                activo = any(m["name"].startswith("mistral") for m in modelos.get("models", []))
                self.config["ollama"]["activo"] = activo
                self._guardar_config()
                return activo
        except Exception:
            self.config["ollama"]["activo"] = False
            self._guardar_config()
        return False

    def obtener_ruta(self, app):
        return self.config["paths"].get(app, "")

    def actualizar_ruta(self, app, ruta):
        self.config["paths"][app] = ruta
        self._guardar_config()
