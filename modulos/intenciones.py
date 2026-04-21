# modulos/intenciones.py
import random
from modulos.logger import log

# Respuestas variadas para humanizar
RESPUESTAS_OK = [
    "Listo.", "Hecho.", "En marcha.", "Perfecto.", "Ya está.",
    "De acuerdo.", "Entendido.", "Sin problema."
]

RESPUESTAS_EMOCION = {
    "cansado": [
        "Entiendo, descansa un poco. ¿Quieres que ponga música relajante?",
        "Pareces cansado. Tómate un descanso, yo me encargo de lo que necesites.",
        "El descanso es importante. ¿Necesitas algo antes de parar?"
    ],
    "estresado": [
        "Respira profundo. ¿Quiero ayudarte a relajarte con algo de música?",
        "El estrés no es bueno. ¿Qué puedo hacer para ayudarte ahora mismo?",
        "Entiendo. Estoy aquí para facilitarte las cosas."
    ],
    "aburrido": [
        "¿Quieres que busque algo entretenido en YouTube?",
        "Puedo abrirte Spotify o Netflix si quieres.",
        "¿Te propongo algo? Podemos escuchar música o ver algo."
    ],
    "triste": [
        "Lo siento. Estoy aquí si necesitas algo.",
        "¿Quieres hablar o prefieres un poco de música?",
        "No estás solo, aquí estoy para ayudarte."
    ],
    "feliz": [
        "Me alegra escuchar eso.",
        "¡Excelente! ¿En qué puedo ayudarte hoy?",
        "Eso es genial. ¿Qué necesitas?"
    ]
}

MODOS = {
    "estudio": {
        "abrir": ["spotify"],
        "cerrar": ["discord", "steam", "epic"],
        "mensaje": "Modo estudio activado. Cerrando distracciones y abriendo Spotify."
    },
    "gaming": {
        "abrir": ["discord", "steam"],
        "cerrar": [],
        "mensaje": "Modo gaming activado. Abriendo Discord y Steam."
    },
    "trabajo": {
        "abrir": ["vscode", "chrome"],
        "cerrar": ["spotify", "discord"],
        "mensaje": "Modo trabajo activado. Preparando el entorno."
    },
    "descanso": {
        "abrir": ["spotify", "netflix"],
        "cerrar": ["vscode"],
        "mensaje": "Modo descanso activado. A relajarse."
    }
}

class DetectorIntenciones:
    def __init__(self, memoria):
        self.memoria = memoria
        self.esperando_confirmacion = False
        self.accion_pendiente = None
        self.modo_silencioso = False

        # Acciones que requieren confirmación
        self.acciones_criticas = [
            "apaga el equipo", "apagar equipo", "reiniciar equipo",
            "formatea", "eliminar", "borrar todo"
        ]

    def respuesta_ok(self):
        return random.choice(RESPUESTAS_OK)

    def detectar_intencion(self, texto):
        """
        Retorna un dict con:
        - tipo: str (el tipo de intención detectada)
        - datos: dict (información adicional)
        O None si no se detecta ninguna intención especial
        """
        texto_lower = texto.lower().strip()

        # 1. Confirmación pendiente
        if self.esperando_confirmacion:
            return self._manejar_confirmacion(texto_lower)

        # 2. Modo silencioso
        if "modo silencioso" in texto_lower:
            return {"tipo": "modo_silencioso", "activar": True}
        if "quitar modo silencioso" in texto_lower or "modo normal" in texto_lower:
            return {"tipo": "modo_silencioso", "activar": False}

        # 3. Acción crítica
        for accion in self.acciones_criticas:
            if accion in texto_lower:
                self.esperando_confirmacion = True
                self.accion_pendiente = accion
                return {"tipo": "confirmacion_requerida", "accion": accion}

        # 4. Guardar comando personalizado
        if "cuando diga" in texto_lower and ("abre" in texto_lower or "busca" in texto_lower):
            return self._parsear_comando_personalizado(texto_lower)

        # 5. Consultar memoria
        if any(f in texto_lower for f in [
            "qué recuerdas", "que recuerdas", "qué sabes de mí",
            "que sabes de mi", "qué sé sobre mí"
        ]):
            return {"tipo": "consultar_memoria"}

        # 6. Guardar en memoria explícitamente
        if any(f in texto_lower for f in [
            "recuerda que", "anota que", "guarda que"
        ]):
            return {"tipo": "guardar_memoria", "texto": texto}

        # 7. Detectar emoción
        emociones = {
            "cansado": ["cansado", "cansada", "agotado", "agotada", "sin energía"],
            "estresado": ["estresado", "estresada", "estres", "estrés", "ansioso", "ansiosa"],
            "aburrido": ["aburrido", "aburrida", "aburrimiento"],
            "triste": ["triste", "mal", "deprimido", "deprimida", "solo", "sola"],
            "feliz": ["feliz", "contento", "contenta", "bien", "genial", "excelente"]
        }
        for emocion, palabras in emociones.items():
            if any(p in texto_lower for p in palabras):
                if any(f in texto_lower for f in ["estoy", "me siento", "siento", "me encuentro"]):
                    return {"tipo": "emocion", "emocion": emocion}

        # 8. Modo personalizado
        for modo in MODOS:
            if f"modo {modo}" in texto_lower:
                return {"tipo": "modo", "modo": modo}

        # 9. Multi-comando
        separadores = [" y luego ", " y después ", " y también ", " luego ", " después "]
        for sep in separadores:
            if sep in texto_lower:
                partes = [p.strip() for p in texto_lower.split(sep) if p.strip()]
                if len(partes) > 1:
                    return {"tipo": "multi_comando", "comandos": partes}

        # 10. Comando personalizado guardado
        accion_custom = self.memoria