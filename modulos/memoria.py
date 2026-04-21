# modulos/memoria.py
import json
import os
import shutil
from datetime import datetime
from modulos.logger import log

class Memoria:
    def __init__(self, archivo="memoria_jarvis.json"):
        self.archivo = archivo
        self.backup_dir = "backups"
        os.makedirs(self.backup_dir, exist_ok=True)
        self.datos = self._cargar()

        # Frases que indican preferencias del usuario
        self.frases_memoria = [
            "recuerda que", "recuerda esto", "anota que",
            "me gusta", "me encanta", "prefiero", "odio",
            "no me gusta", "siempre", "nunca", "mi favorito",
            "mi favorita", "soy de", "tengo", "me llamo",
            "mi nombre es"
        ]

    def _cargar(self):
        if os.path.exists(self.archivo):
            try:
                with open(self.archivo, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                log.error(f"Error cargando memoria: {e}")
                self._restaurar_backup()
        return self._estructura_default()

    def _estructura_default(self):
        return {
            "preferencias": [],
            "comandos_personalizados": {},
            "conversaciones": 0,
            "contexto": {}
        }

    def guardar(self):
        try:
            # Backup antes de guardar
            if os.path.exists(self.archivo):
                fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup = os.path.join(self.backup_dir, f"memoria_{fecha}.json")
                shutil.copy2(self.archivo, backup)
                # Mantener solo los últimos 5 backups
                backups = sorted(os.listdir(self.backup_dir))
                for viejo in backups[:-5]:
                    os.remove(os.path.join(self.backup_dir, viejo))

            with open(self.archivo, "w", encoding="utf-8") as f:
                json.dump(self.datos, f, ensure_ascii=False, indent=2)
            log.debug("Memoria guardada correctamente")
        except Exception as e:
            log.error(f"Error guardando memoria: {e}")

    def _restaurar_backup(self):
        backups = sorted(os.listdir(self.backup_dir)) if os.path.exists(self.backup_dir) else []
        if backups:
            ultimo = os.path.join(self.backup_dir, backups[-1])
            shutil.copy2(ultimo, self.archivo)
            log.warning(f"Memoria restaurada desde backup: {ultimo}")
            with open(self.archivo, "r", encoding="utf-8") as f:
                self.datos = json.load(f)
        else:
            log.warning("No hay backups disponibles. Iniciando memoria vacía.")
            self.datos = self._estructura_default()

    def detectar_y_guardar_preferencia(self, texto):
        """Detecta automáticamente preferencias en el texto"""
        texto_lower = texto.lower()
        for frase in self.frases_memoria:
            if frase in texto_lower:
                partes = texto_lower.split(frase, 1)
                if len(partes) > 1 and partes[1].strip():
                    preferencia = f"{frase} {partes[1].strip()}"
                    if preferencia not in self.datos["preferencias"]:
                        self.datos["preferencias"].append(preferencia)
                        self.guardar()
                        log.info(f"Preferencia guardada: {preferencia}")
                        return True
        return False

    def agregar_preferencia(self, dato):
        if dato not in self.datos["preferencias"]:
            self.datos["preferencias"].append(dato)
            self.guardar()

    def obtener_preferencias_texto(self):
        prefs = self.datos.get("preferencias", [])
        if prefs:
            return "Lo que sé del usuario: " + "; ".join(prefs[-10:]) + "."
        return ""

    def guardar_comando_personalizado(self, trigger, acciones):
        self.datos["comandos_personalizados"][trigger] = acciones
        self.guardar()
        log.info(f"Comando personalizado guardado: '{trigger}' → {acciones}")

    def obtener_comando_personalizado(self, texto):
        for trigger, acciones in self.datos["comandos_personalizados"].items():
            if trigger in texto.lower():
                return acciones
        return None

    def actualizar_contexto(self, clave, valor):
        self.datos["contexto"][clave] = valor
        self.guardar()

    def obtener_contexto(self, clave):
        return self.datos["contexto"].get(clave)

    def incrementar_conversaciones(self):
        self.datos["conversaciones"] = self.datos.get("conversaciones", 0) + 1
        self.guardar()