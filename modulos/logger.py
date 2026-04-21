# modulos/logger.py
import logging
import os
from datetime import datetime

def configurar_logger():
    os.makedirs("logs", exist_ok=True)
    fecha = datetime.now().strftime("%Y-%m-%d")
    
    logger = logging.getLogger("Jarvis")
    logger.setLevel(logging.DEBUG)
    
    # Consola — solo INFO y superior
    consola = logging.StreamHandler()
    consola.setLevel(logging.INFO)
    consola.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S"
    ))
    
    # Archivo — todo incluyendo DEBUG
    archivo = logging.FileHandler(
        f"logs/jarvis_{fecha}.log",
        encoding="utf-8"
    )
    archivo.setLevel(logging.DEBUG)
    archivo.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    ))
    
    logger.addHandler(consola)
    logger.addHandler(archivo)
    return logger

log = configurar_logger()