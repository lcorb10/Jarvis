# main.py
import threading
import sys
from interfaz import InterfazJarvis
from jarvis_core import Jarvis
from modulos.logger import log

def main():
    # Crear GUI
    gui = InterfazJarvis()

    # Crear Jarvis con callbacks hacia la GUI
    jarvis = Jarvis()

    # Conectar callbacks de Jarvis → GUI
    # Parchamos los métodos para que notifiquen a la GUI

    tts_original = jarvis.tts.hablar
    def hablar_con_gui(texto):
        gui.on_jarvis_response(texto)
        gui.on_state_change("hablando")
        tts_original(texto)
        gui.on_state_change("esperando")
    jarvis.tts.hablar = hablar_con_gui

    stt_original = jarvis.stt.escuchar_comando
    def escuchar_con_gui(timeout=10):
        gui.on_state_change("escuchando")
        texto = stt_original(timeout=timeout)
        if texto:
            gui.on_user_speech(texto)
        gui.on_state_change("procesando")
        return texto
    jarvis.stt.escuchar_comando = escuchar_con_gui

    activar_original = jarvis.activar
    def activar_con_gui():
        gui.on_sistema("Jarvis activado por aplauso")
        gui.on_state_change("escuchando")
        activar_original()
        gui.on_state_change("esperando")
    jarvis.detector.callback = activar_con_gui

    # Conectar Jarvis a GUI
    gui.conectar_jarvis(jarvis)

    # Ejecutar Jarvis en hilo separado
    def run_jarvis():
        try:
            jarvis.iniciar()
        except Exception as e:
            log.error(f"Error en Jarvis: {e}")

    hilo_jarvis = threading.Thread(target=run_jarvis, daemon=True)
    hilo_jarvis.start()

    log.info("🖥️ Interfaz iniciada")
    gui.iniciar()

if __name__ == "__main__":
    main()