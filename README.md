# J.A.R.V.I.S MK2

Asistente personal de IA por voz para Windows. Se activa con dos aplausos, entiende comandos en español y puede controlar el computador, buscar en la web, analizar la pantalla y ejecutar tareas de varios pasos.

## Características

- **Voz offline:** reconocimiento de voz con Vosk (modelo en español), sin enviar audio a internet.
- **IA híbrida:** chat con un LLM local vía Ollama y Google Gemini como respaldo opcional.
- **Agente multi-paso:** un planificador divide las tareas en pasos y un ejecutor las corre con manejo de errores.
- **Gestor de cuotas de Gemini:** verifica la API key al inicio, limita a 30 llamadas/min y bloquea por categoría tras errores repetidos, con fallback automático.
- **Síntesis de voz:** Gemini TTS → Edge TTS → pyttsx3, en cascada.
- **Visión:** captura de pantalla o cámara para describir lo que se ve.
- **Control del sistema:** abrir y cerrar aplicaciones (detectadas automáticamente), volumen, archivos, búsquedas en Google y YouTube.
- **Memoria y aprendizaje:** recuerda preferencias y conversaciones recientes.
- **Interfaz gráfica** en PySide6 con panel de configuración, e instalador para Windows (PyInstaller + Inno Setup).

## Tecnologías

Python 3.11 · Vosk · Ollama · Google Gemini API · Edge TTS · PySide6 · Playwright · PyAutoGUI

## Estructura

```
main.py              punto de entrada
jarvis_core.py       ciclo principal: escucha → intención → acción → respuesta
interfaz.py          interfaz gráfica (PySide6)
modulos/
  agent/             planificador, ejecutor y cola de tareas
  apis/              clima, noticias, traductor, Spotify, YouTube
  tools/             control del PC, archivos, búsqueda web, pantalla
  gemini_manager.py  control de cuotas de Gemini
  ia_local.py        cliente de Ollama
  reconocimiento_voz.py / sintesis_voz.py
test_jarvis.py       pruebas
```

## Instalación

1. Instala [Python 3.11+](https://www.python.org/) y [Ollama](https://ollama.com/) (`ollama pull mistral`).
2. Descarga el modelo de Vosk en español y ponlo en `modelos/vosk-es`.
3. Instala las dependencias:
   ```
   pip install -r requirements.txt
   ```
4. (Opcional) Crea un archivo `.env` con `GEMINI_API_KEY=tu_clave` para usar Gemini.
5. Ejecuta:
   ```
   python main.py
   ```

Requisitos recomendados: Windows 10/11, 16 GB de RAM.

## Licencia

MIT
