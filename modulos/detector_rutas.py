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
            except:
                return self._config_default()
        return self._config_default()

    def _config_default(self):
        return {
            "paths": {
                "chrome": "",
                "discord": "",
                "steam": "",
                "ea_desktop": "",
                "python": sys.executable
            },
            "ollama": {
                "modelo": "mistral",
                "url": "http://localhost:11434/api/chat",
                "activo": False
            },
            "vosk": {
                "modelo_ruta": "modelos/vosk-es"
            }
        }

    def _guardar_config(self):
        with open(self.archivo_config, "w", encoding="utf-8") as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
        print(f"✅ Configuración guardada en {self.archivo_config}")

    def buscar_con_powershell(self, nombre_app, patrones):
        """Busca una app usando PowerShell"""
        try:
            for patron in patrones:
                cmd = f'Get-ChildItem "{patron}" -Recurse -Filter "*.exe" -ErrorAction SilentlyContinue | Select-Object -First 1 FullName'
                resultado = subprocess.run(
                    ["powershell", "-NoProfile", "-Command", cmd],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if resultado.stdout.strip():
                    ruta = resultado.stdout.strip().split("\n")[-1]
                    if ruta and os.path.exists(ruta):
                        print(f"✅ {nombre_app} encontrado: {ruta}")
                        return ruta
        except Exception as e:
            print(f"⚠️ Error buscando {nombre_app}: {e}")
        return ""

    def detectar_todas_las_rutas(self):
        """Detecta automáticamente todas las rutas de aplicaciones"""
        print("\n🔍 Detectando aplicaciones instaladas...")
        print("⏳ Esto puede tomar un minuto...\n")

        rutas_a_buscar = {
            "chrome": [
                "C:\\Program Files\\Google\\Chrome",
                "C:\\Program Files (x86)\\Google\\Chrome",
                f"{os.path.expanduser('~')}\\AppData\\Local\\Google\\Chrome"
            ],
            "discord": [
                f"{os.path.expanduser('~')}\\AppData\\Local\\Discord"
            ],
            "steam": [
                "C:\\Program Files\\Steam",
                "C:\\Program Files (x86)\\Steam"
            ],
            "ea_desktop": [
                "C:\\Program Files\\Electronic Arts\\EA Desktop",
                "C:\\Program Files (x86)\\Electronic Arts\\EA Desktop"
            ]
        }

        for app, patrones in rutas_a_buscar.items():
            ruta = self.buscar_con_powershell(app, patrones)
            if ruta:
                self.config["paths"][app] = ruta

        self._guardar_config()
        return self.config

    def verificar_ollama(self):
        """Verifica si Ollama está corriendo y si tiene el modelo"""
        try:
            import requests
            resp = requests.get("http://localhost:11434/api/tags", timeout=2)
            if resp.status_code == 200:
                modelos = resp.json()
                modelo_activo = any(m["name"].startswith("mistral") 
                                   for m in modelos.get("models", []))
                self.config["ollama"]["activo"] = modelo_activo
                if modelo_activo:
                    print("✅ Ollama activo con Mistral")
                else:
                    print("⚠️ Ollama activo pero Mistral no instalado")
                    print("   Ejecuta en terminal: ollama pull mistral")
                self._guardar_config()
                return modelo_activo
        except Exception as e:
            print(f"⚠️ Ollama no disponible: {e}")
            print("   Asegúrate de haber ejecutado: ollama serve")
            self.config["ollama"]["activo"] = False
            self._guardar_config()
        return False

    def obtener_ruta(self, app):
        """Obtiene la ruta guardada de una app"""
        return self.config["paths"].get(app, "")

    def obtener_url_ollama(self):
        return self.config["ollama"]["url"]

    def obtener_modelo_vosk(self):
        return self.config["vosk"]["modelo_ruta"]

    def actualizar_ruta(self, app, ruta):
        """Actualiza la ruta de una app manualmente"""
        self.config["paths"][app] = ruta
        self._guardar_config()