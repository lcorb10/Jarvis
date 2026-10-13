# modulos/apis/matematica.py
import re
import math
from modulos.apis.base import APIBase
from modulos.logger import log


class APIMatematica(APIBase):
    nombre = "matematica"
    descripcion = "Operaciones matemáticas sin API key"
    requiere_key = False

    PALABRAS = [
        "cuánto es", "cuanto es", "calcula", "calcular",
        "cuánto son", "cuanto son", "resultado de",
        "raíz de", "raiz de", "potencia", "porcentaje de",
    ]

    def activado(self):
        return True

    def detectar_intencion(self, texto):
        texto = texto.lower()
        if any(p in texto for p in self.PALABRAS):
            return True
        if re.search(r'\d+\s*[\+\-\*\/\^]\s*\d+', texto):
            return True
        return False

    def ejecutar(self, texto):
        texto_lower = texto.lower()

        raiz = re.search(r'raíz\s+(?:cuadrada\s+)?de\s+(\d+)', texto_lower)
        if raiz:
            n = float(raiz.group(1))
            return f"La raíz cuadrada de {int(n)} es {math.sqrt(n):.4f}"

        pct = re.search(r'(\d+)\s*(?:%|por ciento)\s+de\s+(\d+)', texto_lower)
        if pct:
            p, n = float(pct.group(1)), float(pct.group(2))
            return f"El {int(p)}% de {int(n)} es {p * n / 100:.2f}"

        texto_limpio = texto_lower
        for p in self.PALABRAS:
            texto_limpio = texto_limpio.replace(p, "").strip()
        texto_limpio = (texto_limpio
                        .replace("por", "*").replace("entre", "/")
                        .replace("más", "+").replace("menos", "-")
                        .replace("elevado a", "**").replace("al cuadrado", "**2"))
        expr = re.sub(r'[^\d\+\-\*\/\.\(\)\^]', '', texto_limpio).replace("^", "**")
        if expr:
            try:
                resultado = eval(expr, {"__builtins__": {}}, {})
                return f"El resultado es {resultado}"
            except Exception:
                pass
        return "No pude calcular eso. Intente con una expresión más clara."
