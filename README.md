# Jarvis — Asistente de IA por Voz

Asistente personal tipo Jarvis completamente gratuito, local y sin dependencias de internet.

## Instalación rápida

### 1. Descargar el repositorio
```bash
git clone https://github.com/tuusuario/jarvis.git
cd jarvis
```

### 2. Instalar dependencias
```bash
py -3.11 -m pip install -r requirements.txt
```

### 3. Descargar modelo de voz Vosk
- Ve a https://alphacephei.com/vosk/models
- Descarga `vosk-model-es-0.42` (1.8GB)
- Descomprímelo y renómbralo a `vosk-es`
- Pégalo en `jarvis/modelos/vosk-es/`

### 4. Instalar y arrancar Ollama
```bash
# Descargar e instalar desde https://ollama.com
# Luego en una terminal:
ollama serve

# En otra terminal:
ollama pull mistral
```

### 5. Ejecutar Jarvis
```bash
py -3.11 jarvis_core.py
```

**Nota:** La primera ejecución detectará automáticamente todas tus aplicaciones y guardará las rutas en `config.json`.

## Uso

1. **Aplaudí dos veces** para activar
2. **Habla tu comando** (ej: "abre spotify", "busca memes en youtube")
3. **Di "descansa"** para desactivar

## Requisitos
- Python 3.11+
- Windows 10/11
- 16GB RAM (recomendado)
- ~5GB disco (para Ollama + Vosk)

## Comandos soportados

### Apps
- "abre chrome/discord/spotify/steam/etc"
- "cierra spotify"

### Búsquedas
- "busca recetas de pasta" → Google
- "busca canción de beele en youtube" → YouTube
- "pon la plena en youtube"

### Sistema
- "sube el volumen"
- "baja el volumen"
- "apaga el equipo"

## Personalización

Edita `config.json` para cambiar rutas o modelos de IA.

## Licencia
MIT — Completamente gratuito y de código abierto.