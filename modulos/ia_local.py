# modulos/ia_local.py
import requests
import json
import os
from datetime import datetime

class IALocal:
    def __init__(self, modelo="mistral"):
        self.modelo = modelo
        self.url = "http://localhost:11434/api/chat"
        self.historial = []
        self.archivo_memoria = "memoria_jarvis.json"
        self.memoria = self._cargar_memoria()
        self.sistema = self._construir_sistema()

    def _construir_sistema(self):
        hora = datetime.now().strftime("%H:%M")
        fecha = datetime.now().strftime("%A %d de %B de %Y")
        
        memoria_texto = ""
        if self.memoria.get("preferencias"):
            memoria_texto = f"Lo que sé del usuario: {', '.join(self.memoria['preferencias'])}."

        return f"""Eres Jarvis, un asistente personal de IA inteligente y eficiente.

REGLAS ESTRICTAS:
- SIEMPRE respondes en español, sin excepciones
- Respuestas CORTAS: máximo 2 oraciones para voz
- Si te piden abrir una app o buscar algo, confirma brevemente
- Eres directo, útil y con personalidad tipo Jarvis de Iron Man
- La hora actual es {hora} y la fecha es {fecha}
- {memoria_texto}

CAPACIDADES:
- Puedes abrir aplicaciones cuando el usuario lo pide
- Puedes buscar en Google cuando el usuario dice "busca", "buscar", "googlea"
- Recuerdas el contexto de la conversación
- Respondes preguntas generales con precisión"""

    def _cargar_memoria(self):
        if os.path.exists(self.archivo_memoria):
            try:
                with open(self.archivo_memoria, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return {"preferencias": [], "conversaciones": 0}

    def _guardar_memoria(self):
        try:
            with open(self.archivo_memoria, "w", encoding="utf-8") as f:
                json.dump(self.memoria, f, ensure_ascii=False, indent=2)
        except:
            pass

    def _detectar_busqueda(self, texto):
        """Detecta si el usuario quiere buscar algo en Google"""
        texto_lower = texto.lower()
        palabras_busqueda = [
            "busca", "buscar", "googlea", "google", "busca en google",
            "busca en internet", "busca en la web", "busca información",
            "qué es", "que es", "quién es", "quien es", "cómo se hace",
            "como se hace", "dónde está", "donde esta", "busca sobre"
        ]
        for palabra in palabras_busqueda:
            if palabra in texto_lower:
                # Extraer el término de búsqueda
                termino = texto_lower
                for p in palabras_busqueda:
                    termino = termino.replace(p, "").strip()
                return termino if termino else texto
        return None

    def consultar(self, mensaje):
        # Actualizar sistema con hora actual
        self.sistema = self._construir_sistema()
        
        # Detectar si es una búsqueda
        termino_busqueda = self._detectar_busqueda(mensaje)
        if termino_busqueda:
            return f"BUSCAR_GOOGLE:{termino_busqueda}"

        self.historial.append({"role": "user", "content": mensaje})
        self.memoria["conversaciones"] = self.memoria.get("conversaciones", 0) + 1

        payload = {
            "model": self.modelo,
            "messages": [
                {"role": "system", "content": self.sistema},
                *self.historial[-12:]
            ],
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
            }
        }

        try:
            resp = requests.post(self.url, json=payload, timeout=30)
            resp.raise_for_status()
            respuesta = resp.json()["message"]["content"].strip()
            self.historial.append({"role": "assistant", "content": respuesta})
            self._guardar_memoria()
            return respuesta
        except requests.exceptions.ConnectionError:
            return "Ollama no está activo. Ejecuta ollama serve."
        except Exception as e:
            return f"Error: {str(e)}"

    def aprender(self, dato):
        """Guardar preferencia del usuario"""
        if dato not in self.memoria["preferencias"]:
            self.memoria["preferencias"].append(dato)
            self._guardar_memoria()

    def limpiar_historial(self):
        self.historial = []
        print("🗑️ Historial limpiado.")