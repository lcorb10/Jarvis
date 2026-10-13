# main.py — Jarvis MK2
import sys
import threading

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def _ya_corriendo_y_traer_al_frente() -> bool:
    """Si ya hay un Jarvis corriendo (bridge en :18790), le pide mostrar la GUI
    y devuelve True para que este lanzamiento se aborte."""
    try:
        import urllib.request, json
        with urllib.request.urlopen("http://127.0.0.1:18790/health", timeout=1.5) as r:
            data = json.loads(r.read())
            if data.get("status") == "ok":
                # Ya hay una instancia: pedirle que muestre la ventana
                req = urllib.request.Request(
                    "http://127.0.0.1:18790/show",
                    method="POST",
                    headers={"Content-Type": "application/json"},
                    data=b"{}",
                )
                try:
                    urllib.request.urlopen(req, timeout=2)
                except Exception:
                    pass
                return True
    except Exception:
        pass
    return False


def main():
    if _ya_corriendo_y_traer_al_frente():
        print("Jarvis MK2 ya está corriendo. Restaurando ventana.")
        sys.exit(0)

    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("Jarvis MK2")

    # GUI primero
    from interfaz import InterfazJarvis
    gui = InterfazJarvis()

    # Jarvis con callbacks hacia la GUI
    from jarvis_core import Jarvis
    jarvis = Jarvis(gui_callbacks=gui.get_callbacks())

    # Conectar referencia bidireccional
    gui.conectar_jarvis(jarvis)

    # Bridge HTTP para Telegram (WSL2 → Windows)
    try:
        from bridge_server import start_bridge
        start_bridge(jarvis)
    except Exception as e:
        from modulos.logger import log
        log.warning(f"Bridge no inició: {e}")

    # Jarvis en hilo de fondo
    def run_jarvis():
        try:
            jarvis.iniciar()
        except Exception as e:
            from modulos.logger import log
            log.error(f"Error en Jarvis: {e}")

    hilo = threading.Thread(target=run_jarvis, daemon=True)
    hilo.start()

    gui.iniciar()


if __name__ == "__main__":
    main()
