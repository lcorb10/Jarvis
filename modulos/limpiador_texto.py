# modulos/limpiador_texto.py
import re

MULETILLAS = [
    "jarvis", "oye jarvis", "hey jarvis", "ey jarvis", "eh jarvis",
    "por favor", "por fa", "porfavor", "please",
    "puedes", "podrías", "podrias", "me puedes",
    "quiero que", "necesito que", "me gustaría que",
    "me gustaria que", "quisiera que", "oye", "mira",
]

SEPARADORES_MULTI = [
    " y también ", " y tambien ", " y luego ", " y después ",
    " y despues ", " y además ", " y ademas ", " después ",
    " despues ", " luego ", " también ", " tambien ",
    ", también ", ", tambien ", ", y ",
]


def limpiar(texto):
    texto = texto.lower().strip()
    for m in sorted(MULETILLAS, key=len, reverse=True):
        if texto.startswith(m + " "):
            texto = texto[len(m):].strip()
        elif texto.startswith(m):
            texto = texto[len(m):].strip()
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto


def separar_comandos(texto):
    texto = limpiar(texto)
    for sep in SEPARADORES_MULTI:
        if sep in texto:
            partes = [p.strip() for p in texto.split(sep) if p.strip()]
            if len(partes) > 1:
                return partes
    return [texto]


def es_nombre_jarvis(texto):
    texto = texto.lower().strip()
    return any(texto.startswith(m) for m in ["jarvis", "oye jarvis", "hey jarvis"])
