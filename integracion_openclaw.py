# integracion_openclaw.py — OpenClaw para tools adicionales
"""
OpenClaw es un registry centralizado de tools para agentes de IA.
Permite descubrir y cargar tools dinámicamente sin recompilar.

Más info: https://github.com/openclaw-ai/openclaw-registry
"""

import json
import requests
from typing import List, Dict, Any
from modulos.logger import log


class OpenClawIntegration:
    """Integra el registry de OpenClaw para acceder a tools adicionales."""

    REGISTRY_URL = "https://api.openclaw.io/v1"
    CATEGORIES = [
        "web_scraping",
        "data_processing", 
        "file_operations",
        "api_integration",
        "content_generation",
        "image_processing",
        "email",
        "calendar",
        "database",
        "devops",
        "system_management",
    ]

    def __init__(self):
        self.tools_cache = {}
        self.available_categories = []
        self._cargar_categorias()

    def _cargar_categorias(self):
        """Carga categorías disponibles del registry"""
        try:
            resp = requests.get(
                f"{self.REGISTRY_URL}/categories",
                timeout=5,
            )
            if resp.status_code == 200:
                self.available_categories = resp.json().get("categories", [])
                log.info(f"[OpenClaw] {len(self.available_categories)} categorías cargadas")
            else:
                log.warning("[OpenClaw] No se pudo conectar al registry")
                self.available_categories = self.CATEGORIES
        except Exception as e:
            log.warning(f"[OpenClaw] Offline mode: {e}")
            self.available_categories = self.CATEGORIES

    def buscar_tools(self, query: str, categoria: str = None) -> List[Dict]:
        """Busca tools en el registry por keyword y categoría opcional."""
        try:
            params = {"q": query}
            if categoria:
                params["category"] = categoria
            
            resp = requests.get(
                f"{self.REGISTRY_URL}/tools/search",
                params=params,
                timeout=10,
            )
            
            if resp.status_code == 200:
                tools = resp.json().get("tools", [])
                log.info(f"[OpenClaw] {len(tools)} tools encontradas para '{query}'")
                return tools
            else:
                log.warning(f"[OpenClaw] Search failed: {resp.status_code}")
                return []
        except Exception as e:
            log.error(f"[OpenClaw] Search error: {e}")
            return []

    def cargar_tool(self, tool_id: str) -> Dict[str, Any] | None:
        """Descarga y carga una herramienta específica del registry."""
        try:
            resp = requests.get(
                f"{self.REGISTRY_URL}/tools/{tool_id}",
                timeout=10,
            )
            
            if resp.status_code == 200:
                tool = resp.json()
                self.tools_cache[tool_id] = tool
                log.info(f"[OpenClaw] Tool cargada: {tool_id}")
                return tool
            else:
                log.warning(f"[OpenClaw] Tool no encontrada: {tool_id}")
                return None
        except Exception as e:
            log.error(f"[OpenClaw] Load error: {e}")
            return None

    def listar_populares(self, categoria: str = None, limit: int = 10) -> List[Dict]:
        """Lista las tools más populares de una categoría."""
        try:
            params = {"limit": limit}
            if categoria:
                params["category"] = categoria
            
            resp = requests.get(
                f"{self.REGISTRY_URL}/tools/popular",
                params=params,
                timeout=10,
            )
            
            if resp.status_code == 200:
                return resp.json().get("tools", [])
            return []
        except Exception as e:
            log.error(f"[OpenClaw] Popular tools error: {e}")
            return []

    def ejecutar_tool(self, tool_id: str, parameters: Dict) -> str:
        """Ejecuta una tool del registry."""
        tool = self.tools_cache.get(tool_id)
        
        if not tool:
            tool = self.cargar_tool(tool_id)
        
        if not tool:
            return f"Tool no encontrada: {tool_id}"

        source_type = tool.get("source", "python")
        code = tool.get("code", "")

        if source_type == "python":
            try:
                namespace = {
                    "parameters": parameters,
                    "__builtins__": {},
                }
                
                import math
                import json as json_lib
                import re
                namespace.update({
                    "math": math,
                    "json": json_lib,
                    "re": re,
                })
                
                exec(code, namespace)
                
                if "execute" in namespace:
                    resultado = namespace["execute"](**parameters)
                elif "run" in namespace:
                    resultado = namespace["run"](**parameters)
                else:
                    resultado = "Tool ejecutada pero sin función de salida"
                
                return str(resultado)
            
            except Exception as e:
                log.error(f"[OpenClaw] Execution error: {e}")
                return f"Error ejecutando tool: {e}"
        
        elif source_type == "http":
            endpoint = tool.get("endpoint", "")
            try:
                resp = requests.post(endpoint, json=parameters, timeout=15)
                return resp.text
            except Exception as e:
                return f"Error llamando endpoint: {e}"
        
        else:
            return f"Source type no soportado: {source_type}"


if __name__ == "__main__":
    print("\n=== OpenClaw Integration Demo ===\n")
    
    oc = OpenClawIntegration()
    
    print(f"Categorías disponibles: {len(oc.available_categories)}")
    print(f"  {', '.join(oc.available_categories[:5])}...\n")
    
    print("Buscando tools para 'web scraping'...")
    tools = oc.buscar_tools("web scraping", "web_scraping")
    if tools:
        for t in tools[:3]:
            print(f"  - {t.get('name')}: {t.get('description', '')[:60]}")
    else:
        print("  (Registry offline o sin resultados)")
    
    print("\n✅ OpenClaw Integration lista\n")