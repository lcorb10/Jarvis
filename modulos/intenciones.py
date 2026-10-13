# modulos/intenciones.py
import random
from modulos.logger import log

RESPUESTAS_OK = [
    "Listo.", "Hecho.", "En marcha.", "Perfecto.", "Ya está.",
    "De acuerdo.", "Entendido.", "Sin problema.", "Considerado.",
]

RESPUESTAS_EMOCION = {
    "cansado": [
        "Entiendo, descanse un poco. ¿Quiere que ponga música relajante?",
        "El descanso es importante, señor. ¿Necesita algo antes de parar?",
    ],
    "estresado": [
        "Respire profundo. ¿Quiere que cierre algunas aplicaciones?",
        "Estoy aquí para facilitar las cosas, señor. ¿Qué puedo hacer?",
    ],
    "aburrido": [
        "¿Quiere que busque algo entretenido en YouTube?",
        "Puedo abrir Spotify o Netflix si lo prefiere.",
    ],
    "triste": [
        "Lo siento, señor. Estoy aquí si necesita algo.",
        "¿Quiere hablar o prefiere un poco de música?",
    ],
    "feliz": [
        "Me alegra escuchar eso, señor.",
        "Excelente. ¿En qué puedo ayudarle hoy?",
    ],
}

MODOS = {
    "estudio": {
        "abrir": ["spotify"],
        "cerrar": ["discord", "steam", "epic"],
        "mensaje": "Modo estudio activado. Cerrando distracciones y preparando ambiente.",
    },
    "gaming": {
        "abrir": ["discord", "steam"],
        "cerrar": [],
        "mensaje": "Modo gaming activado. Abriendo Discord y Steam.",
    },
    "trabajo": {
        "abrir": ["vscode", "chrome"],
        "cerrar": ["spotify", "discord"],
        "mensaje": "Modo trabajo activado. Preparando el entorno de desarrollo.",
    },
    "descanso": {
        "abrir": ["spotify", "netflix"],
        "cerrar": ["vscode"],
        "mensaje": "Modo descanso activado. A relajarse, señor.",
    },
    "concentracion": {
        "abrir": [],
        "cerrar": ["discord", "steam", "chrome"],
        "mensaje": "Modo concentración activado. Eliminando distracciones.",
    },
}


class DetectorIntenciones:
    def __init__(self, memoria):
        self.memoria = memoria
        self.esperando_confirmacion = False
        self.accion_pendiente = None

        self.acciones_criticas = [
            "apaga el equipo", "apagar equipo", "reiniciar equipo",
            "formatea", "eliminar todo", "borrar todo",
        ]

    def respuesta_ok(self):
        return random.choice(RESPUESTAS_OK)

    def detectar_intencion(self, texto):
        texto_lower = texto.lower().strip()

        # 1. Confirmación pendiente
        if self.esperando_confirmacion:
            return self._manejar_confirmacion(texto_lower)

        # 2. Modo silencioso
        if "modo silencioso" in texto_lower:
            return {"tipo": "modo_silencioso", "activar": True}
        if any(p in texto_lower for p in ["quitar modo silencioso", "modo normal", "activa el sonido"]):
            return {"tipo": "modo_silencioso", "activar": False}

        # 3. Acciones críticas
        for accion in self.acciones_criticas:
            if accion in texto_lower:
                self.esperando_confirmacion = True
                self.accion_pendiente = accion
                return {"tipo": "confirmacion_requerida", "accion": accion}

        # 4. Cambiar IA
        if any(p in texto_lower for p in ["usa gemini", "cambia a gemini", "activa gemini"]):
            return {"tipo": "cambiar_ia", "ia": "gemini"}
        if any(p in texto_lower for p in ["usa ollama", "cambia a ollama", "activa ollama", "modo local"]):
            return {"tipo": "cambiar_ia", "ia": "ollama"}

        # 4b. Cambiar voz TTS
        if any(p in texto_lower for p in ["activa la voz de gemini", "usa la voz de gemini", "voz gemini"]):
            return {"tipo": "cambiar_voz", "motor": "gemini"}
        if any(p in texto_lower for p in ["activa la voz de edge", "usa la voz de edge", "voz edge", "voz normal"]):
            return {"tipo": "cambiar_voz", "motor": "edge"}

        # 5. Guardar comando personalizado
        if "cuando diga" in texto_lower:
            return self._parsear_comando_personalizado(texto_lower)

        # 6. Consultar memoria
        if any(f in texto_lower for f in [
            "qué recuerdas", "que recuerdas", "qué sabes de mí",
            "que sabes de mi", "qué tienes guardado", "que tienes guardado",
        ]):
            return {"tipo": "consultar_memoria"}

        # 7. Guardar en memoria
        if any(f in texto_lower for f in ["recuerda que", "anota que", "guarda que"]):
            return {"tipo": "guardar_memoria", "texto": texto}

        # 8. Limpiar historial
        if any(p in texto_lower for p in ["limpia el historial", "borra el historial", "olvida lo anterior"]):
            return {"tipo": "limpiar_historial"}

        # 9. Emoción
        emociones = {
            "cansado":   ["cansado", "cansada", "agotado", "agotada", "sin energía"],
            "estresado": ["estresado", "estresada", "estrés", "estres", "ansioso"],
            "aburrido":  ["aburrido", "aburrida", "aburrimiento"],
            "triste":    ["triste", "mal", "deprimido", "deprimida"],
            "feliz":     ["feliz", "contento", "contenta", "genial", "excelente"],
        }
        for emocion, palabras in emociones.items():
            if any(p in texto_lower for p in palabras):
                if any(f in texto_lower for f in ["estoy", "me siento", "siento", "me encuentro", "ando"]):
                    return {"tipo": "emocion", "emocion": emocion}

        # 10. Modo
        for modo in MODOS:
            if f"modo {modo}" in texto_lower or f"activa modo {modo}" in texto_lower:
                return {"tipo": "modo", "modo": modo}

        # 11. Multi-comando con separadores
        separadores = [" y luego ", " y después ", " y también ", " luego ", " después "]
        for sep in separadores:
            if sep in texto_lower:
                partes = [p.strip() for p in texto_lower.split(sep) if p.strip()]
                if len(partes) > 1:
                    return {"tipo": "multi_comando", "comandos": partes}

        # 12. Comando personalizado guardado
        accion_custom = self.memoria.obtener_comando_personalizado(texto_lower)
        if accion_custom:
            return {"tipo": "comando_personalizado", "acciones": accion_custom}

        return None

    def _manejar_confirmacion(self, texto_lower):
        if any(p in texto_lower for p in ["sí", "si", "confirmo", "hazlo", "adelante", "procede"]):
            self.esperando_confirmacion = False
            accion = self.accion_pendiente
            self.accion_pendiente = None
            return {"tipo": "confirmado", "accion": accion}
        else:
            self.esperando_confirmacion = False
            self.accion_pendiente = None
            return {"tipo": "cancelado"}

    def _parsear_comando_personalizado(self, texto):
        """Parsea: 'cuando diga modo trabajo abre vscode y chrome' """
        try:
            partes = texto.split("cuando diga", 1)
            if len(partes) < 2:
                return None
            resto = partes[1].strip()
            acciones_raw = []
            for conector in [" haz ", " ejecuta ", " abre ", " cierra ", " busca "]:
                if conector in resto:
                    idx = resto.index(conector)
                    trigger = resto[:idx].strip()
                    accion_str = resto[idx:].strip()
                    acciones_raw = [a.strip() for a in accion_str.split(" y ") if a.strip()]
                    self.memoria.guardar_comando_personalizado(trigger, acciones_raw)
                    return {"tipo": "definir_comando", "trigger": trigger, "acciones": acciones_raw}
            # Si no encontró conector, guardar el trigger completo
            return {"tipo": "definir_comando_incompleto", "texto": texto}
        except Exception as e:
            log.error(f"Error parseando comando personalizado: {e}")
            return None
