# modulos/tools/web_search.py
import requests
import re
from modulos.logger import log

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
}


def web_search(parameters: dict, speak=None) -> str:
    query = parameters.get("query", parameters.get("text", "")).strip()
    max_results = int(parameters.get("max_results", 3))

    if not query:
        return "No se especificó qué buscar."

    log.info(f"[WebSearch] Buscando: {query}")

    result = _duckduckgo_instant(query)
    if result:
        return result

    result = _duckduckgo_lite(query, max_results)
    if result:
        return result

    return f"No encontré información sobre: {query}"


def _duckduckgo_instant(query: str) -> str:
    try:
        resp = requests.get(
            "https://api.duckduckgo.com/",
            params={"q": query, "format": "json", "no_html": "1", "skip_disambig": "1"},
            timeout=8,
            headers=_HEADERS,
        )
        data = resp.json()
        for key in ("AbstractText", "Answer", "Definition"):
            val = data.get(key, "").strip()
            if len(val) > 30:
                return val[:600]
        # Related topics fallback
        topics = data.get("RelatedTopics", [])
        snippets = []
        for t in topics[:3]:
            text = t.get("Text", "").strip()
            if text:
                snippets.append(text[:150])
        return "\n".join(snippets) if snippets else ""
    except Exception as e:
        log.debug(f"[WebSearch] DDG instant: {e}")
        return ""


def _duckduckgo_lite(query: str, max_results: int) -> str:
    try:
        resp = requests.get(
            "https://lite.duckduckgo.com/lite/",
            params={"q": query},
            timeout=10,
            headers=_HEADERS,
        )
        text = resp.text
        # DDG lite wraps snippets in <td class="result-snippet">
        snippets = re.findall(
            r'class=["\']result-snippet["\'][^>]*>(.*?)</td>', text, re.DOTALL
        )
        results = []
        for s in snippets[:max_results]:
            clean = re.sub(r"<[^>]+>", "", s).strip()
            clean = re.sub(r"\s+", " ", clean)
            if len(clean) > 20:
                results.append(clean)
        return "\n\n".join(results) if results else ""
    except Exception as e:
        log.debug(f"[WebSearch] DDG lite: {e}")
        return ""
