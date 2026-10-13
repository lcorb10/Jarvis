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

        self.frases_memoria = [
            "recuerda que", "recuerda esto", "anota que",
            "me gusta", "me encanta", "prefiero", "odio",
            "no me gusta", "siempre", "nunca", "mi favorito",
            "mi favorita", "soy de", "tengo", "me llamo",
            "mi nombre es", "trabajo en", "estudio", "vivo en",
        ]

    def _estructura_default(self):
        return {
            "preferencias": [],
            "comandos_personalizados": {},
            "conversaciones": 0,
            "contexto": {},
            "memoria_larga": {},   # categoria → {clave: {value, timestamp}}
        }

    def _cargar(self):
        if os.path.exists(self.archivo):
            try:
                with open(self.archivo, "r", encoding="utf-8") as f:
                    datos = json.load(f)
                default = self._estructura_default()
                for clave, valor in default.items():
                    if clave not in datos:
                        datos[clave] = valor
                return datos
            except Exception as e:
                log.error(f"Error cargando memoria: {e}")
                return self._restaurar_backup()
        return self._estructura_default()

    def guardar(self):
        try:
            if os.path.exists(self.archivo):
                fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup = os.path.join(self.backup_dir, f"memoria_{fecha}.json")
                shutil.copy2(self.archivo, backup)
                backups = sorted(os.listdir(self.backup_dir))
                for viejo in backups[:-5]:
                    os.remove(os.path.join(self.backup_dir, viejo))
            with open(self.archivo, "w", encoding="utf-8") as f:
                json.dump(self.datos, f, ensure_ascii=False, indent=2)
            log.debug("Memoria guardada")
        except Exception as e:
            log.error(f"Error guardando memoria: {e}")

    def _restaurar_backup(self):
        try:
            backups = sorted(os.listdir(self.backup_dir)) \
                      if os.path.exists(self.backup_dir) else []
            if backups:
                ultimo = os.path.join(self.backup_dir, backups[-1])
                shutil.copy2(ultimo, self.archivo)
                with open(self.archivo, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            log.error(f"Error restaurando backup: {e}")
        return self._estructura_default()

    # ── Preferencias ──────────────────────────────────────────────────────────
    def detectar_y_guardar_preferencia(self, texto):
        texto_lower = texto.lower()
        for frase in self.frases_memoria:
            if frase in texto_lower:
                partes = texto_lower.split(frase, 1)
                if len(partes) > 1 and partes[1].strip():
                    pref = f"{frase} {partes[1].strip()}"
                    if pref not in self.datos["preferencias"]:
                        self.datos["preferencias"].append(pref)
                        self.guardar()
                        log.info(f"Preferencia guardada: {pref}")
                        return True
        return False

    def agregar_preferencia(self, dato):
        if dato not in self.datos["preferencias"]:
            self.datos["preferencias"].append(dato)
            self.guardar()

    def obtener_preferencias_texto(self):
        prefs = self.datos.get("preferencias", [])
        if prefs:
            return "Lo que sé del usuario: " + "; ".join(prefs[-15:]) + "."
        return ""

    # ── Memoria larga (clave-valor por categoría, estilo MK37) ────────────────
    def guardar_memoria_larga(self, categoria: str, clave: str, valor: str):
        if "memoria_larga" not in self.datos:
            self.datos["memoria_larga"] = {}
        if categoria not in self.datos["memoria_larga"]:
            self.datos["memoria_larga"][categoria] = {}
        self.datos["memoria_larga"][categoria][clave] = {
            "value": valor,
            "timestamp": datetime.now().isoformat()
        }
        self.guardar()
        log.info(f"Memoria larga: {categoria}/{clave} = {valor}")

    def obtener_memoria_larga_texto(self):
        ml = self.datos.get("memoria_larga", {})
        if not ml:
            return ""
        lineas = ["Memoria de largo plazo:"]
        for cat, items in ml.items():
            for clave, data in items.items():
                lineas.append(f"  [{cat}] {clave}: {data['value']}")
        return "\n".join(lineas)

    # ── Comandos personalizados ────────────────────────────────────────────────
    def guardar_comando_personalizado(self, trigger, acciones):
        self.datos["comandos_personalizados"][trigger] = acciones
        self.guardar()

    def obtener_comando_personalizado(self, texto):
        for trigger, acciones in self.datos["comandos_personalizados"].items():
            if trigger in texto.lower():
                return acciones
        return None

    # ── Contexto de sesión ────────────────────────────────────────────────────
    def actualizar_contexto(self, clave, valor):
        if "contexto" not in self.datos:
            self.datos["contexto"] = {}
        self.datos["contexto"][clave] = valor
        self.guardar()

    def obtener_contexto(self, clave):
        return self.datos.get("contexto", {}).get(clave)

    def incrementar_conversaciones(self):
        self.datos["conversaciones"] = self.datos.get("conversaciones", 0) + 1
        self.guardar()
