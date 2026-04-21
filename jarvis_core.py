# jarvis_core.py
import os
from modulos.detector_rutas import DetectorRutas
from modulos.detector_aplausos import DetectorAplausos
from modulos.reconocimiento_voz import ReconocimientoVoz
from modulos.ia_local import IALocal
from modulos.sintesis_voz import SintesisVoz
from modulos.control_sistema import ControlSistema

class Jarvis:
    def __init__(self):
        print("⚙️  Inicializando Jarvis...")
        
        # 1. Detectar rutas si no existen
        self.detector_rutas = DetectorRutas()
        if not self.detector_rutas.config["paths"]["chrome"]:
            print("\n🔍 Primera ejecución detectada...")
            self.detector_rutas.detectar_todas_las_rutas()
        
        # 2. Verificar Ollama
        print("\n🤖 Verificando Ollama y Mistral...")
        ollama_ok = self.detector_rutas.verificar_ollama()
        if not ollama_ok:
            print("\n⚠️ ADVERTENCIA: Ollama no está activo o Mistral no está instalado")
            print("   Necesitas ejecutar en otra terminal:")
            print("   1. ollama serve")
            print("   2. ollama pull mistral")
            print("\n   Continuando sin IA por ahora...\n")
        
        # 3. Inicializar módulos
        self.tts      = SintesisVoz()
        self.stt      = ReconocimientoVoz()
        self.ia       = IALocal(modelo="mistral")
        self.control  = ControlSistema()
        self.detector = DetectorAplausos(callback_activacion=self.activar)
        self.en_conversacion = False
        print("✅ Jarvis listo.\n")

    def activar(self):
        if self.en_conversacion:
            return
        self.en_conversacion = True
        print("\n✅ ¡JARVIS ACTIVADO!")
        self.tts.hablar("Sí, estoy aquí. ¿En qué puedo ayudarte?")
        self._ciclo_conversacion()

    def _ciclo_conversacion(self):
        intentos_vacios = 0

        while True:
            texto = self.stt.escuchar_comando(timeout=10)

            if not texto:
                intentos_vacios += 1
                if intentos_vacios == 1:
                    self.tts.hablar("¿Sigues ahí?")
                elif intentos_vacios >= 2:
                    self.tts.hablar("Volviendo al modo espera.")
                    break
                continue

            intentos_vacios = 0
            texto_lower = texto.lower()

            if any(p in texto_lower for p in ["descansa", "hasta luego", "adiós", "bye"]):
                self.tts.hablar("Descansando. Aplaude dos veces cuando me necesites.")
                break

            if "limpia el historial" in texto_lower:
                self.ia.limpiar_historial()
                self.tts.hablar("Historial limpiado.")
                continue

            respuesta_sistema = self.control.interpretar_comando(texto)
            if respuesta_sistema:
                self.tts.hablar(respuesta_sistema)
                continue

            print("🤖 Consultando IA...")
            respuesta = self.ia.consultar(texto)

            if respuesta.startswith("BUSCAR_GOOGLE:"):
                termino = respuesta.replace("BUSCAR_GOOGLE:", "").strip()
                respuesta = self.control.buscar_google(termino)

            self.tts.hablar(respuesta)

        self.en_conversacion = False
        print("\n😴 Jarvis en modo espera...")

    def iniciar(self):
        self.tts.hablar("Jarvis iniciado. Esperando tu señal.")
        self.detector.escuchar()

if __name__ == "__main__":
    jarvis = Jarvis()
    jarvis.iniciar()