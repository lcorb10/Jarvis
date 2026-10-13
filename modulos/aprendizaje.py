# modulos/aprendizaje.py
"""
Analiza los logs de Jarvis para detectar patrones y actualizar la memoria.

Patrones detectados:
  - Comandos más usados → memorizar como preferencias
  - Horas de activación → inferir rutinas
  - APIs frecuentes → priorizar en orquestador
  - Errores repetidos → registrar para evitarlos
"""
import os
import re
import json
import glob
import threading
from collections import Counter
from datetime import datetime
from modulos.logger import log

_LOGS_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
_ESTADO_PATH = os.path.join(os.path.dirname(__file__), "..", "aprendizaje_estado.json")

_IGNORAR_COMANDOS = {
    "hola", "gracias", "de nada", "descansa", "hasta luego",
    "adiós", "adios", "sí", "si", "no", "ok", "listo",
}

# Transcripciones erróneas de "Jarvis" que Vosk produce con frecuencia
_ALIAS_JARVIS = {"davis", "jarvis", "jervis", "tarvis", "garvis", "harvis", "marvis"}


def _normalizar_comando(cmd: str) -> str:
    """Reemplaza alias erróneos de 'Jarvis' y elimina el nombre del wake word."""
    palabras = cmd.split()
    # Quitar la primera palabra si es un alias de Jarvis (wake word)
    if palabras and palabras[0].lower() in _ALIAS_JARVIS:
        palabras = palabras[1:]
    return " ".join(palabras).strip()


def _cargar_estado() -> dict:
    try:
        if os.path.exists(_ESTADO_PATH):
            with open(_ESTADO_PATH, encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {"ultimo_analisis": None, "comandos_frecuentes": {}, "horas_activas": {}, "apis_usadas": {}, "errores": {}}


def _guardar_estado(estado: dict):
    try:
        with open(_ESTADO_PATH, "w", encoding="utf-8") as f:
            json.dump(estado, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log.error(f"[Aprendizaje] Error guardando estado: {e}")


def _leer_logs_nuevos(ultimo_analisis: str | None) -> list[str]:
    lineas = []
    archivos = sorted(glob.glob(os.path.join(_LOGS_DIR, "*.log")))
    for archivo in archivos:
        try:
            with open(archivo, encoding="utf-8", errors="ignore") as f:
                for linea in f:
                    if ultimo_analisis and linea[:19] <= ultimo_analisis:
                        continue
                    lineas.append(linea)
        except Exception:
            pass
    return lineas


def analizar(memoria=None) -> dict:
    estado = _cargar_estado()
    lineas = _leer_logs_nuevos(estado.get("ultimo_analisis"))

    if not lineas:
        log.info("[Aprendizaje] Sin logs nuevos para analizar")
        return estado

    log.info(f"[Aprendizaje] Analizando {len(lineas)} líneas de log...")

    comandos = Counter()
    horas = Counter()
    apis = Counter()
    errores = Counter()

    re_usuario = re.compile(r"Usuario: '(.+)'")
    re_hora    = re.compile(r"^(\d{4}-\d{2}-\d{2} (\d{2}):\d{2}:\d{2})")
    re_api     = re.compile(r"API seleccionada: (\w+)")
    re_error   = re.compile(r"\[ERROR\].*?:\s(.+)")
    re_ollama  = re.compile(r"\[Ollama\]|\[Gemini\]")

    for linea in lineas:
        m = re_usuario.search(linea)
        if m:
            cmd = m.group(1).lower().strip()
            cmd = _normalizar_comando(cmd)
            if not cmd:
                continue
            palabras = cmd.split()
            if len(palabras) >= 2 and palabras[0] not in _IGNORAR_COMANDOS:
                clave = " ".join(palabras[:3])
                if clave not in _IGNORAR_COMANDOS:
                    comandos[clave] += 1

        m = re_hora.search(linea)
        if m and re_usuario.search(linea):
            hora = m.group(2)
            horas[hora] += 1

        m = re_api.search(linea)
        if m:
            apis[m.group(1)] += 1

        m = re_error.search(linea)
        if m:
            err = m.group(1)[:60]
            errores[err] += 1

    # Actualizar estado acumulado
    for k, v in comandos.items():
        estado["comandos_frecuentes"][k] = estado["comandos_frecuentes"].get(k, 0) + v
    for k, v in horas.items():
        estado["horas_activas"][k] = estado["horas_activas"].get(k, 0) + v
    for k, v in apis.items():
        estado["apis_usadas"][k] = estado["apis_usadas"].get(k, 0) + v
    for k, v in errores.items():
        estado["errores"][k] = estado["errores"].get(k, 0) + v

    estado["ultimo_analisis"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Guardar insights en memoria de Jarvis
    if memoria:
        _aplicar_a_memoria(estado, memoria)

    _guardar_estado(estado)
    log.info(f"[Aprendizaje] Análisis completado. Top comandos: {list(sorted(estado['comandos_frecuentes'].items(), key=lambda x: -x[1])[:3])}")
    return estado


def _aplicar_a_memoria(estado: dict, memoria):
    try:
        # Hora más activa → preferencia de uso
        if estado["horas_activas"]:
            hora_top = max(estado["horas_activas"], key=lambda h: estado["horas_activas"][h])
            memoria.guardar_memoria_larga(
                "rutina", "hora_mas_activa",
                f"{hora_top}:00 — uso frecuente detectado"
            )

        # Top 5 comandos frecuentes
        top_cmds = sorted(estado["comandos_frecuentes"].items(), key=lambda x: -x[1])[:5]
        for cmd, cnt in top_cmds:
            if cnt >= 3:
                memoria.guardar_memoria_larga(
                    "habitos", f"cmd_{cmd[:20].replace(' ','_')}",
                    f"'{cmd}' usado {cnt} veces"
                )

        # API más usada
        if estado["apis_usadas"]:
            api_top = max(estado["apis_usadas"], key=lambda a: estado["apis_usadas"][a])
            memoria.guardar_memoria_larga(
                "habitos", "api_preferida",
                f"{api_top} (más usada)"
            )

    except Exception as e:
        log.error(f"[Aprendizaje] Error aplicando a memoria: {e}")


def iniciar_loop(memoria=None, intervalo_horas: float = 24):
    """Ejecuta el análisis periódicamente en hilo de fondo."""
    def _loop():
        while True:
            try:
                analizar(memoria=memoria)
            except Exception as e:
                log.error(f"[Aprendizaje] Error en loop: {e}")
            threading.Event().wait(intervalo_horas * 3600)

    hilo = threading.Thread(target=_loop, daemon=True, name="JarvisAprendizaje")
    hilo.start()
    log.info(f"[Aprendizaje] Loop activo — cada {intervalo_horas}h")
