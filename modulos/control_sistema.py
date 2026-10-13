# modulos/control_sistema.py
import subprocess
import psutil
import webbrowser
import urllib.parse
import json
import os


class ControlSistema:

    def __init__(self):
        self.config = self._cargar_config()
        self.CHROME = self.config.get("paths", {}).get("chrome") or \
                      r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        self.DISCORD = self._resolver_discord(self.config.get("paths", {}).get("discord") or "")
        self.STEAM = self._resolver_steam(self.config.get("paths", {}).get("steam") or "")
        self.EA_DESKTOP = self._resolver_ea(self.config.get("paths", {}).get("ea_desktop") or "")

    @staticmethod
    def _resolver_discord(ruta_guardada: str) -> str:
        import glob as _glob
        if ruta_guardada and os.path.isfile(ruta_guardada):
            return ruta_guardada
        patron = os.path.join(os.path.expanduser("~"), "AppData", "Local",
                              "Discord", "app-*", "Discord.exe")
        candidatos = sorted(_glob.glob(patron), reverse=True)
        if candidatos:
            return candidatos[0]
        # Fallback: Update.exe lanza Discord correctamente
        update = os.path.join(os.path.expanduser("~"), "AppData", "Local", "Discord", "Update.exe")
        if os.path.isfile(update):
            return update
        return ""

    @staticmethod
    def _resolver_steam(ruta_guardada: str) -> str:
        if ruta_guardada and os.path.isfile(ruta_guardada):
            return ruta_guardada
        candidatos = [
            r"C:\Program Files (x86)\Steam\steam.exe",
            r"C:\Program Files\Steam\steam.exe",
        ]
        for c in candidatos:
            if os.path.isfile(c):
                return c
        return candidatos[0]  # devolver igual para intentarlo via shell

    @staticmethod
    def _resolver_ea(ruta_guardada: str) -> str:
        if ruta_guardada and os.path.isfile(ruta_guardada):
            return ruta_guardada
        candidatos = [
            r"C:\Program Files\Electronic Arts\EA Desktop\EADesktop.exe",
            r"C:\Program Files (x86)\Electronic Arts\EA Desktop\EADesktop.exe",
            os.path.join(os.path.expanduser("~"), "AppData", "Local",
                         "Electronic Arts", "EA Desktop", "EADesktop.exe"),
        ]
        for c in candidatos:
            if os.path.isfile(c):
                return c
        return candidatos[0]

    def _cargar_config(self):
        for ruta in ["config.json", os.path.join(os.path.dirname(__file__), "..", "config.json")]:
            if os.path.exists(ruta):
                try:
                    with open(ruta, "r", encoding="utf-8") as f:
                        return json.load(f)
                except Exception:
                    pass
        return {"paths": {}}

    APPS = {
        "chrome":       {"alias": ["chrome", "google", "google chrome", "navegador", "browser"]},
        "edge":         {"alias": ["edge", "microsoft edge"], "comando_fijo": ["msedge"]},
        "spotify":      {"alias": ["spotify", "spotifi", "spoti", "musica", "music"], "protocolo": "spotify:"},
        "discord":      {"alias": ["discord", "disc", "discor"]},
        "whatsapp":     {"alias": ["whatsapp", "whatsap", "wasa", "wasap"], "protocolo": "whatsapp:"},
        "notepad":      {"alias": ["bloc de notas", "bloc", "notas", "notepad"], "comando_fijo": ["notepad"]},
        "calculadora":  {"alias": ["calculadora", "calcular", "calcu"], "comando_fijo": ["calc"]},
        "vscode":       {"alias": ["codigo", "visual studio", "vs code", "vscode", "code", "programar"], "comando_fijo": ["code"]},
        "explorador":   {"alias": ["explorador", "archivos", "carpetas", "mis archivos"], "comando_fijo": ["explorer"]},
        "paint":        {"alias": ["paint", "pintar", "dibujar"], "comando_fijo": ["mspaint"]},
        "terminal":     {"alias": ["terminal", "consola", "cmd", "comandos"], "comando_fijo": ["cmd"]},
        "taskmanager":  {"alias": ["administrador de tareas", "task manager", "procesos"], "comando_fijo": ["taskmgr"]},
        "steam":        {"alias": ["steam", "juegos steam"]},
        "epic":         {"alias": ["epic", "epic games", "epik"], "comando_fijo": [r"C:\Program Files (x86)\Epic Games\Launcher\Portal\Binaries\Win32\EpicGamesLauncher.exe"]},
        "riot":         {"alias": ["riot", "riot client"], "comando_fijo": [r"C:\Riot Games\Riot Client\RiotClientServices.exe"]},
        "valorant":     {"alias": ["valorant", "valo", "balorant"], "comando_fijo": [r"C:\Riot Games\Riot Client\RiotClientServices.exe", "--launch-product=valorant", "--launch-patchline=live"]},
        "league":       {"alias": ["league", "league of legends", "lol", "liga"], "comando_fijo": [r"C:\Riot Games\Riot Client\RiotClientServices.exe", "--launch-product=league_of_legends", "--launch-patchline=live"]},
        "ea":           {"alias": ["ea", "ea desktop", "electronic arts", "ea app"]},
        "brawlhalla":   {"alias": ["brawlhalla", "brawl"], "steam_id": "291550"},
        "csgo":         {"alias": ["counter strike", "cs go", "csgo", "cs2"], "steam_id": "730"},
        "minecraft":    {"alias": ["minecraft", "mine"], "protocolo": "minecraft:"},
        "roblox":       {"alias": ["roblox", "roblo"], "protocolo": "roblox:"},
        "battlenet":    {"alias": ["battle net", "battlenet", "blizzard"], "comando_fijo": [r"C:\Program Files (x86)\Battle.net\Battle.net.exe"]},
        "github":       {"alias": ["github", "github desktop"], "comando_fijo": [r"C:\Users\Sebastian\AppData\Local\GitHubDesktop\GitHubDesktop.exe"]},
        "filmora":      {"alias": ["filmora", "editor de video"], "comando_fijo": [r"C:\Users\Sebastian\AppData\Local\Wondershare\Wondershare Filmora\Filmora.exe"]},
        "osu":          {"alias": ["osu", "ritmo"], "comando_fijo": [r"C:\Users\Sebastian\AppData\Local\osu!\osu!.exe"]},
        "configuracion":{"alias": ["configuracion", "ajustes", "settings"], "protocolo": "ms-settings:"},
        "youtube":      {"alias": ["youtube", "yutub"]},
        "netflix":      {"alias": ["netflix", "netflis", "peliculas", "series"], "protocolo": "netflix:"},
        "capcut":       {"alias": ["capcut", "cap cut"], "protocolo": "capcut:"},
        "outlook":      {"alias": ["outlook", "correo", "email"], "protocolo": "outlook:"},
        "teams":        {"alias": ["teams", "microsoft teams"], "protocolo": "msteams:"},
        "powershell":   {"alias": ["powershell", "power shell"], "comando_fijo": ["powershell"]},
        "winrar":       {"alias": ["winrar", "rar", "comprimir"], "comando_fijo": [r"C:\Program Files\WinRAR\WinRAR.exe"]},
    }

    def _similitud(self, texto, alias):
        texto, alias = texto.lower().strip(), alias.lower().strip()
        if texto == alias: return 1.0
        if alias in texto: return 0.95
        if texto in alias: return 0.85
        comunes = sum(1 for c in texto if c in alias)
        return comunes / max(len(texto), len(alias), 1)

    def _encontrar_app(self, texto):
        mejor_app, mejor_score = None, 0.3
        for nombre_app, datos in self.APPS.items():
            for alias in datos["alias"]:
                score = self._similitud(texto, alias)
                if score > mejor_score:
                    mejor_score = score
                    mejor_app = nombre_app
        return mejor_app, mejor_score

    def interpretar_comando(self, texto):
        texto_lower = texto.lower().strip()

        palabras_abrir = ["abre", "abrir", "lanza", "inicia", "pon", "ponme",
                          "ejecuta", "arranca", "muestrame", "quiero ver",
                          "abre el", "abre la"]
        palabras_cerrar = ["cierra", "cerrar", "mata", "termina", "quita",
                           "cierra el", "cierra la"]
        palabras_youtube = [
            "coloca en youtube", "coloca musica en youtube", "coloca música en youtube",
            "busca en youtube", "en youtube", "pon en youtube",
            "busca la cancion", "busca la canción", "pon la",
            "pon la cancion", "ponme",
        ]
        palabras_spotify = [
            "coloca en spotify", "coloca musica en spotify", "coloca música en spotify",
            "pon en spotify", "reproduce en spotify", "busca en spotify",
            "ponme en spotify", "abre spotify y pon", "pon la canción en spotify",
            "pon la cancion en spotify",
        ]
        palabras_buscar = ["busca", "buscar", "googlea", "busca en google",
                           "busca en internet", "busca sobre"]

        if any(w in texto_lower for w in palabras_spotify):
            termino = texto_lower
            for p in sorted(palabras_spotify, key=len, reverse=True):
                termino = termino.replace(p, "").strip()
            termino = termino.replace("en spotify", "").replace("spotify", "").strip()
            if termino:
                return self.reproducir_spotify(termino)

        if any(w in texto_lower for w in palabras_youtube):
            termino = texto_lower
            for p in sorted(palabras_youtube, key=len, reverse=True):
                termino = termino.replace(p, "").strip()
            termino = termino.replace("en youtube", "").replace("youtube", "").strip()
            if termino:
                return self.buscar_youtube(termino)

        if any(w in texto_lower for w in palabras_buscar):
            termino = texto_lower
            for p in sorted(palabras_buscar, key=len, reverse=True):
                termino = termino.replace(p, "").strip()
            if termino:
                return self.buscar_google(termino)

        es_abrir = any(w in texto_lower for w in palabras_abrir)
        es_cerrar = any(w in texto_lower for w in palabras_cerrar)

        if es_abrir or es_cerrar:
            texto_limpio = texto_lower
            for palabra in sorted(palabras_abrir + palabras_cerrar, key=len, reverse=True):
                texto_limpio = texto_limpio.replace(palabra, "").strip()
            app, score = self._encontrar_app(texto_limpio)
            if not app or score < 0.4:
                app, score = self._encontrar_app(texto_lower)
            if app:
                return self.cerrar_app(app) if es_cerrar else self.abrir_app(app)

        if any(w in texto_lower for w in ["apaga el equipo", "apagar equipo"]):
            return self.apagar_equipo()
        if any(w in texto_lower for w in ["sube el volumen", "más volumen", "sube volumen"]):
            return self.cambiar_volumen("subir")
        if any(w in texto_lower for w in ["baja el volumen", "menos volumen", "baja volumen"]):
            return self.cambiar_volumen("bajar")

        return None

    def abrir_app(self, nombre_app):
        datos = self.APPS.get(nombre_app, {})

        if "protocolo" in datos:
            try:
                subprocess.Popen(["cmd", "/c", "start", datos["protocolo"]])
                return f"Abriendo {nombre_app}."
            except Exception:
                return f"No pude abrir {nombre_app}."

        if "steam_id" in datos:
            try:
                subprocess.Popen([self.STEAM, "-applaunch", datos["steam_id"]],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return f"Abriendo {nombre_app} desde Steam."
            except Exception:
                return f"No pude abrir {nombre_app}."

        if "comando_fijo" in datos:
            cmds = datos["comando_fijo"]
            try:
                subprocess.Popen(cmds, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return f"Abriendo {nombre_app}."
            except Exception:
                try:
                    subprocess.Popen(" ".join(cmds), shell=True,
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return f"Abriendo {nombre_app}."
                except Exception:
                    return f"No pude abrir {nombre_app}."

        rutas_dinamicas = {
            "chrome":   self.CHROME,
            "discord":  self.DISCORD,
            "steam":    self.STEAM,
            "ea":       self.EA_DESKTOP,
            "youtube":  self.CHROME,
        }
        if nombre_app in rutas_dinamicas:
            ruta = rutas_dinamicas[nombre_app]
            if not ruta:
                return self._abrir_por_nombre(nombre_app)
            try:
                args = [ruta]
                if nombre_app == "youtube":
                    args.append("https://www.youtube.com")
                # Discord via Update.exe requiere flag especial
                if nombre_app == "discord" and ruta.endswith("Update.exe"):
                    args = [ruta, "--processStart", "Discord.exe"]
                subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return f"Abriendo {nombre_app}."
            except Exception:
                return self._abrir_por_nombre(nombre_app)

        return f"No encontré {nombre_app}."

    def _abrir_por_nombre(self, nombre_app: str) -> str:
        """Intenta abrir una app por su nombre usando el shell de Windows."""
        try:
            subprocess.Popen(
                ["cmd", "/c", "start", "", nombre_app],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            return f"Abriendo {nombre_app}."
        except Exception:
            return f"No pude abrir {nombre_app}."

    def cerrar_app(self, nombre_app):
        procesos_map = {
            "chrome":          ["chrome.exe"],
            "edge":            ["msedge.exe"],
            "spotify":         ["spotify.exe"],
            "discord":         ["discord.exe"],
            "whatsapp":        ["whatsapp.exe"],
            "notepad":         ["notepad.exe"],
            "calculadora":     ["calculatorapp.exe", "calc.exe"],
            "vscode":          ["code.exe"],
            "explorador":      ["explorer.exe"],
            "steam":           ["steam.exe"],
            "valorant":        ["valorant.exe"],
            "league":          ["leagueclient.exe"],
            "ea":              ["eadesktop.exe"],
            "teams":           ["ms-teams.exe", "teams.exe"],
            "csgo":            ["cs2.exe", "csgo.exe"],
            "osu":             ["osu!.exe"],
            "taskmanager":     ["taskmgr.exe"],
            "task manager":    ["taskmgr.exe"],
            "administrador":   ["taskmgr.exe"],
            "administrador de tareas": ["taskmgr.exe"],
            "taskmgr":         ["taskmgr.exe"],
            "battlenet":       ["battle.net.exe", "battlenet.exe"],
            "battle.net":      ["battle.net.exe", "battlenet.exe"],
            "github":          ["githubdesktop.exe"],
            "filmora":         ["filmora.exe"],
            "winrar":          ["winrar.exe"],
            "powershell":      ["powershell.exe"],
            "terminal":        ["cmd.exe", "windowsterminal.exe"],
            "paint":           ["mspaint.exe"],
        }
        # Normalizar: quitar espacios y minúsculas para match robusto
        nombre_norm = nombre_app.lower().strip()
        nombres_proceso = (
            procesos_map.get(nombre_norm) or
            procesos_map.get(nombre_norm.replace(" ", "")) or
            [nombre_norm + ".exe"]
        )
        cerrados = 0
        for proc in psutil.process_iter(["name"]):
            try:
                if proc.info["name"].lower() in [p.lower() for p in nombres_proceso]:
                    proc.terminate()
                    cerrados += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return f"Cerré {nombre_app}." if cerrados else f"No encontré {nombre_app} en ejecución."

    def buscar_google(self, termino):
        url = f"https://www.google.com/search?q={urllib.parse.quote(termino)}"
        try:
            subprocess.Popen([self.CHROME, url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            webbrowser.open(url)
        return f"Buscando {termino} en Google."

    def buscar_youtube(self, termino):
        """Abre el primer video de YouTube directamente (sin API key)."""
        import re
        try:
            import requests as _req
            query = urllib.parse.quote(termino)
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            resp = _req.get(
                f"https://www.youtube.com/results?search_query={query}",
                headers=headers, timeout=6,
            )
            match = re.search(r'"videoId":"([a-zA-Z0-9_-]{11})"', resp.text)
            if match:
                url = f"https://www.youtube.com/watch?v={match.group(1)}"
                try:
                    subprocess.Popen([self.CHROME, url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except Exception:
                    webbrowser.open(url)
                return f"Reproduciendo {termino} en YouTube."
        except Exception:
            pass
        # Fallback: página de resultados
        url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(termino)}"
        try:
            subprocess.Popen([self.CHROME, url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            webbrowser.open(url)
        return f"Buscando {termino} en YouTube."

    def reproducir_spotify(self, termino):
        """Abre Spotify y busca el término usando el protocolo URI."""
        query = urllib.parse.quote(termino)
        uri = f"spotify:search:{query}"
        try:
            subprocess.Popen(["cmd", "/c", "start", "", uri],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return f"Buscando {termino} en Spotify."
        except Exception:
            try:
                webbrowser.open(uri)
                return f"Buscando {termino} en Spotify."
            except Exception:
                return "No pude abrir Spotify."

    def apagar_equipo(self):
        subprocess.run(["shutdown", "/s", "/t", "30"], shell=True)
        return "Apagando el equipo en 30 segundos."

    def cambiar_volumen(self, direccion):
        tecla = "[char]175" if direccion == "subir" else "[char]174"
        try:
            subprocess.run(
                f'powershell -c "$obj = New-Object -ComObject WScript.Shell; $obj.SendKeys({tecla})"',
                shell=True
            )
        except Exception:
            pass
        return "Volumen subido." if direccion == "subir" else "Volumen bajado."
