# modulos/apis/base.py
from abc import ABC, abstractmethod


class APIBase(ABC):
    nombre = "base"
    descripcion = "API base"
    requiere_key = False

    @abstractmethod
    def activado(self) -> bool:
        pass

    @abstractmethod
    def detectar_intencion(self, texto: str) -> bool:
        pass

    @abstractmethod
    def ejecutar(self, texto: str) -> str:
        pass
