# Optimización Gemini API — Jarvis MK2

## Arquitectura final

| Servicio | Default | Fallback |
|----------|---------|----------|
| Chat IA  | Ollama (llama3) | Gemini si motor=gemini |
| TTS      | **Gemini Charon** | Edge → pyttsx3 |
| Visión   | Gemini 2.0 Flash | (sin alternativa) |
| STT      | Vosk (offline) | (no Gemini) |
| Planner  | Gemini 2.0 Flash | Plan fallback local |

## GeminiManager — control central

Archivo: `modulos/gemini_manager.py`

### Protecciones automáticas

| Detección | Acción |
|-----------|--------|
| Sin API key | Bloquea sesión, no intenta |
| `API_KEY_INVALID` | Bloquea sesión completa, fallback a Edge/Ollama |
| `quota` / `429` | Bloquea sesión completa |
| 3 errores seguidos en una categoría | Bloquea solo esa categoría (TTS, chat, vision...) |
| Rate limit | Max 30 calls/min (cuota gratis = 60) |

### Verificación 1 sola vez al inicio

```
[GeminiManager] Inicializado (key=AIzaSy...)
[GeminiManager] ✅ API key válida
```

Si falla:
```
[GeminiManager] ❌ API key inválida
[GeminiManager] 🔒 SESIÓN BLOQUEADA
```

A partir de ese momento todas las llamadas a Gemini retornan inmediatamente sin tocar la API.

## Flujo TTS

```
hablar(texto)
   ├─ Gemini disponible? → SÍ → intentar
   │     └─ Error? → marcar y fallback
   ├─ Edge disponible? → SÍ → usar
   └─ pyttsx3 (último recurso)
```

## Cómo cambiar de motor IA

**Voz**: "usa gemini" / "usa llama" / "usa ollama"
**GUI**: botón "🤖 GEMINI" / "🤖 OLLAMA"

Si Gemini está bloqueado, el botón no hace nada y se mantiene Ollama.

## Cómo recuperar Gemini tras corregir API key

1. Edita `.env` → `GEMINI_API_KEY=tu_nueva_key`
2. GUI → ⚙ Configuración → guardar (esto resetea el manager)

O reinicia Jarvis.

## Consumo estimado (por hora de uso activo)

| Categoría | Llamadas |
|-----------|----------|
| TTS (Gemini) | ~30 (1 por respuesta) |
| Chat (si motor=ollama) | 0 |
| Chat (si motor=gemini) | ~15 |
| Vision | solo si pides análisis pantalla |
| Planner | solo en tareas multi-paso |

Total típico (motor=ollama, TTS=gemini): **~30-40 calls/h**
Cuota Gemini Free Tier: ~3600 calls/día
→ **Margen: 60-100 horas de uso diario** ✓

## Stats en tiempo real

Desde Python:
```python
from modulos.gemini_manager import gemini
print(gemini().stats())
```

Retorna:
```json
{
  "key_valida": true,
  "bloqueado": false,
  "categorias_bloqueadas": [],
  "calls_ultimo_min": 12,
  "stats": {
    "tts": {"ok": 45, "error": 0},
    "chat": {"ok": 8, "error": 1},
    ...
  }
}
```
