# modulos/tools/openclaw.py
"""
Wrapper de OpenClaw para el sistema de tools del agente.
Busca y ejecuta tools del registry OpenClaw.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import requests
from modulos.logger import log

_REGISTRY_URL = "https://api.openclaw.io/v1"
_cache: dict = {}


def openclaw(parameters: dict, speak=None) -> str:
    action = parameters.get("action", "execute")

    if action == "search":
        query = parameters.get("query", "")
        return _search(query)
    elif action == "execute":
        tool_id = parameters.get("tool_id", "")
        params = parameters.get("params", {})
        return _execute(tool_id, params)
    elif action == "list":
        category = parameters.get("category", "")
        return _list_popular(category)
    else:
        return f"Acción OpenClaw desconocida: {action}"


def _search(query: str) -> str:
    try:
        resp = requests.get(
            f"{_REGISTRY_URL}/tools/search",
            params={"q": query},
            timeout=10,
        )
        if resp.status_code == 200:
            tools = resp.json().get("tools", [])
            if not tools:
                return "No se encontraron tools en OpenClaw para esa búsqueda."
            lines = [f"- {t.get('name')}: {t.get('description', '')[:80]}" for t in tools[:5]]
            return "Tools encontradas:\n" + "\n".join(lines)
        return "OpenClaw registry no respondió."
    except Exception as e:
        log.warning(f"[OpenClaw] Search error: {e}")
        return f"OpenClaw no disponible: {e}"


def _execute(tool_id: str, params: dict) -> str:
    if not tool_id:
        return "Se requiere tool_id para ejecutar."

    tool = _cache.get(tool_id)
    if not tool:
        try:
            resp = requests.get(f"{_REGISTRY_URL}/tools/{tool_id}", timeout=10)
            if resp.status_code == 200:
                tool = resp.json()
                _cache[tool_id] = tool
            else:
                return f"Tool '{tool_id}' no encontrada en OpenClaw."
        except Exception as e:
            log.error(f"[OpenClaw] Load error: {e}")
            return f"Error cargando tool: {e}"

    source_type = tool.get("source", "python")
    code = tool.get("code", "")

    if source_type == "python":
        try:
            import math, json as _json, re as _re
            namespace = {
                "parameters": params,
                "__builtins__": {"print": print, "len": len, "str": str,
                                  "int": int, "float": float, "list": list,
                                  "dict": dict, "range": range},
                "math": math, "json": _json, "re": _re,
            }
            exec(code, namespace)
            fn = namespace.get("execute") or namespace.get("run")
            if fn:
                return str(fn(**params))
            return "Tool ejecutada (sin salida)."
        except Exception as e:
            log.error(f"[OpenClaw] Execution error: {e}")
            return f"Error ejecutando tool: {e}"

    elif source_type == "http":
        endpoint = tool.get("endpoint", "")
        try:
            resp = requests.post(endpoint, json=params, timeout=15)
            return resp.text[:500]
        except Exception as e:
            return f"Error llamando endpoint: {e}"

    return f"Source type no soportado: {source_type}"


def _list_popular(category: str) -> str:
    try:
        params = {"limit": 5}
        if category:
            params["category"] = category
        resp = requests.get(f"{_REGISTRY_URL}/tools/popular", params=params, timeout=10)
        if resp.status_code == 200:
            tools = resp.json().get("tools", [])
            lines = [f"- {t.get('name')}: {t.get('description', '')[:80]}" for t in tools]
            return "Tools populares:\n" + "\n".join(lines) if lines else "Sin resultados."
        return "OpenClaw no respondió."
    except Exception as e:
        return f"OpenClaw no disponible: {e}"
