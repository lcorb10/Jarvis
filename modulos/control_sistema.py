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
        self.DISCORD = self.config.get("paths", {}).get("discord") or ""
        self.STEAM = self.config.get("paths", {}).get("steam") or \
                     r"C:\Program Files (x86)\Steam\steam.exe"
        self.EA_DESKTOP = self.config.get("paths", {}).get("ea_desktop") or \
                          r"C:\Program Files\Electronic Arts\EA Desktop\EADesktop.exe"

        # Corregir Discord — Update.exe no es el ejecutable correcto
        if self.DISCORD and "Update.exe" in self.DISCORD:
            self.DISCORD = self.DISCORD.replace(
                "Update.exe",
                "app-1.0.9233\\Discord.exe"
            )
        # Corregir EA Desktop — EADestager.exe no es el correcto
        if self.EA_DESKTOP and "Destager" in self.EA_DESKTOP:
            self.EA_DESKTOP = self.EA_DESKTOP.replace(
                "Destager\\EADestager.exe",
                "13.676.0.6189-1775001998\\EA Desktop\\EADesktop.exe"
            )

    def _cargar_config(self):
        rutas = ["config.json", "modulos/config.json"]
        for ruta in rutas:
            if os.path.exists(ruta):
                try:
                    with open(ruta, "r", encoding="utf-8") as f:
                        return json.load(f)
                except:
                    pass
        return {"paths": {}}

    APPS = {
        "chrome": {
            "alias": ["chrome", "google", "google chrome", "crome",
                      "navegador", "browser", "goo"]
        },
        "edge": {
            "alias": ["edge", "microsoft edge", "egde"],
            "comando_fijo": ["msedge"]
        },
        "spotify": {
            "alias": ["spotify", "spotifi", "espotify", "musica", "music",
                      "spotifai", "pote", "potifi", "spoti", "spo", "sportify"],
            "protocolo": "spotify:"
        },
        "discord": {
            "alias": ["discord", "discor", "disc", "doscord", "discod",
                      "discort", "doscort"]
        },
        "whatsapp": {
            "alias": ["whatsapp", "whatsap", "wasa", "wasap"],
            "protocolo": "whatsapp:"
        },
        "notepad": {
            "alias": ["bloc de notas", "bloc", "notas", "notepad",
                      "nota", "editor de texto"],
            "comando_fijo": ["notepad"]
        },
        "calculadora": {
            "alias": ["calculadora", "calcular", "calcula", "calcu"],
            "comando_fijo": ["calc"]
        },
        "vscode": {
            "alias": ["codigo", "visual studio", "vs code", "vscode",
                      "code", "editor", "programar"],
            "comando_fijo": ["code"]
        },
        "explorador": {
            "alias": ["explorador", "archivos", "carpetas",
                      "mis archivos", "explorer"],
            "comando_fijo": ["explorer"]
        },
        "paint": {
            "alias": ["paint", "pintar", "dibujar"],
            "comando_fijo": ["mspaint"]
        },
        "terminal": {
            "alias": ["terminal", "consola", "cmd", "comandos"],
            "comando_fijo": ["cmd"]
        },
        "taskmanager": {
            "alias": ["administrador de tareas", "task manager",
                      "procesos", "tareas", "administrador"],
            "comando_fijo": ["taskmgr"]
        },
        "steam": {
            "alias": ["steam", "juegos steam", "estim"]
        },
        "epic": {
            "alias": ["epic", "epic games", "epik"],
            "comando_fijo": [r"C:\Program Files (x86)\Epic Games\Launcher\Portal\Binaries\Win32\EpicGamesLauncher.exe"]
        },
        "riot": {
            "alias": ["riot", "riot client", "riot games"],
            "comando_fijo": [r"C:\Riot Games\Riot Client\RiotClientServices.exe"]
        },
        "valorant": {
            "alias": ["valorant", "valo", "balorant", "valorat"],
            "comando_fijo": [r"C:\Riot Games\Riot Client\RiotClientServices.exe",
                             "--launch-product=valorant",
                             "--launch-patchline=live"]
        },
        "league": {
            "alias": ["league", "league of legends", "lol", "legends", "liga"],
            "comando_fijo": [r"C:\Riot Games\Riot Client\RiotClientServices.exe",
                             "--launch-product=league_of_legends",
                             "--launch-patchline=live"]
        },
        "ea": {
            "alias": ["ea", "ea desktop", "electronic arts", "ea app"]
        },
        "fc26": {
            "alias": ["fc26", "fc 26", "fifa", "futbol", "football",
                      "ea fc", "fut", "fc veintiseis"]
        },
        "brawlhalla": {
            "alias": ["brawlhalla", "brawl", "brawlala", "brawlhala",
                      "brulhalla", "brawl halla"],
            "steam_id": "291550"
        },
        "csgo": {
            "alias": ["counter strike", "cs go", "csgo", "cs2"],
            "steam_id": "730"
        },
        "minecraft": {
            "alias": ["minecraft", "mine", "maikraft", "maincraft"],
            "protocolo": "minecraft:"
        },
        "roblox": {
            "alias": ["roblox", "roblo"],
            "protocolo": "roblox:"
        },
        "battlenet": {
            "alias": ["battle net", "battlenet", "blizzard"],
            "comando_fijo": [r"C:\Program Files (x86)\Battle.net\Battle.net.exe"]
        },
        "github": {
            "alias": ["github", "github desktop"],
            "comando_fijo": [r"C:\Users\Sebastian\AppData\Local\GitHubDesktop\GitHubDesktop.exe"]
        },
        "filmora": {
            "alias": ["filmora", "filmore", "editor de video"],
            "comando_fijo": [r"C:\Users\Sebastian\AppData\Local\Wondershare\Wondershare Filmora\Filmora.exe"]
        },
        "winrar": {
            "alias": ["winrar", "rar", "comprimir"],
            "comando_fijo": [r"C:\Program Files\WinRAR\WinRAR.exe"]
        },
        "osu": {
            "alias": ["osu", "ritmo"],
            "comando_fijo": [r"C:\Users\Sebastian\AppData\Local\osu!\osu!.exe"]
        },
        "configuracion": {
            "alias": ["configuracion", "ajustes", "settings"],
            "protocolo": "ms-settings:"
        },
        "youtube": {
            "alias": ["youtube", "yutub"],
        },
        "netflix": {
            "alias": ["netflix", "netflis", "peliculas", "series"],
            "protocolo": "netflix:"
        },
        "capcut": {
            "alias": ["capcut", "cap cut"],
            "protocolo": "capcut:"
        },
        "outlook": {
            "alias": ["outlook", "correo", "email"],
            "protocolo": "outlook:"
        },
        "teams": {
            "alias": ["teams", "microsoft teams"],
            "protocolo": "msteams:"
        },
    }

    def _similitud(self, texto, alias):
        texto = texto.lower().strip()
        alias = alias.lower().strip()
        if texto == alias:
            return 1.0
        if alias in texto:
            return 0.95
        if texto in alias:
            return 0.85
        comunes = sum(1 for c in texto if c in alias)
        score = comunes / max(len(texto), len(alias), 1)
        return score

    def _encontrar_app(self, texto):
        mejor_app = None
        mejor_score = 0.3
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
                          "abreme", "ejecuta", "arranca", "muestrame",
                          "quiero ver", "abre el", "abre la", "abre los"]

        palabras_cerrar = ["cierra", "cerrar", "mata", "termina", "quita",
                           "cierra el", "cierra la"]

        # Búsqueda en YouTube
        palabras_youtube = ["busca en youtube", "en youtube", "pon en youtube",
                            "busca el video", "busca la cancion", "busca la canción",
                            "pon la cancion", "pon la canción", "busca la musica",
                            "busca la música", "quiero escuchar", "ponme la cancion",
                            "ponme la canción", "pon la", "ponme"]
        if any(w in texto_lower for w in palabras_youtube):
            termino = texto_lower
            for p in sorted(palabras_youtube, key=len, reverse=True):
                termino = termino.replace(p, "").strip()
            if termino:
                return self.buscar_youtube(termino)

        # Búsqueda en Google
        palabras_buscar = ["busca", "buscar", "googlea", "busca en google",
                           "busca en internet", "busca sobre",
                           "busca información", "busca informacion"]
        if any(w in texto_lower for w in palabras_buscar):
            termino = texto_lower
            for p in sorted(palabras_buscar, key=len, reverse=True):
                termino = termino.replace(p, "").strip()
            if termino:
                return self.buscar_google(termino)

        # Abrir o cerrar apps
        es_abrir = any(w in texto_lower for w in palabras_abrir)
        es_cerrar = any(w in texto_lower for w in palabras_cerrar)

        if es_abrir or es_cerrar:
            texto_limpio = texto_lower
            for palabra in sorted(palabras_abrir + palabras_cerrar,
                                  key=len, reverse=True):
                texto_limpio = texto_limpio.replace(palabra, "").strip()

            app, score = self._encontrar_app(texto_limpio)
            if not app or score < 0.4:
                app, score = self._encontrar_app(texto_lower)

            if app:
                print(f"🎯 App: {app} (score: {score:.2f})")
                if es_cerrar:
                    return self.cerrar_app(app)
                else:
                    return self.abrir_app(app)

        # Comandos del sistema
        if "apaga el equipo" in texto_lower or "apagar equipo" in texto_lower:
            return self.apagar_equipo()
        if any(w in texto_lower for w in ["sube el volumen", "aumenta el volumen",
                                           "mas volumen", "sube volumen"]):
            return self.cambiar_volumen("subir")
        if any(w in texto_lower for w in ["baja el volumen", "reduce el volumen",
                                           "menos volumen", "baja volumen"]):
            return self.cambiar_volumen("bajar")

        return None

    def abrir_app(self, nombre_app):
        datos = self.APPS.get(nombre_app, {})

        # Protocolo start
        if "protocolo" in datos:
            try:
                subprocess.Popen(["cmd", "/c", "start", datos["protocolo"]])
                print(f"✅ Abriendo: {nombre_app}")
                return f"Abriendo {nombre_app}."
            except Exception as e:
                print(f"❌ Error protocolo: {e}")
                return f"No pude abrir {nombre_app}."

        # Steam por ID de juego
        if "steam_id" in datos:
            try:
                subprocess.Popen([self.STEAM, "-applaunch", datos["steam_id"]],
                                 stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL)
                print(f"✅ Abriendo {nombre_app} desde Steam")
                return f"Abriendo {nombre_app} desde Steam."
            except Exception as e:
                print(f"❌ Error Steam: {e}")
                return f"No pude abrir {nombre_app}."

        # Comando fijo (rutas hardcodeadas o comandos del sistema)
        if "comando_fijo" in datos:
            cmds = datos["comando_fijo"]
            try:
                subprocess.Popen(cmds,
                                 stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL)
                print(f"✅ Abriendo: {nombre_app}")
                return f"Abriendo {nombre_app}."
            except Exception:
                try:
                    subprocess.Popen(" ".join(cmds), shell=True,
                                     stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL)
                    return f"Abriendo {nombre_app}."
                except Exception as e:
                    print(f"❌ Error comando_fijo: {e}")
                    return f"No pude abrir {nombre_app}."

        # Apps con ruta dinámica del config.json
        rutas_dinamicas = {
            "chrome":   self.CHROME,
            "discord":  self.DISCORD,
            "steam":    self.STEAM,
            "ea":       self.EA_DESKTOP,
            "fc26":     self.EA_DESKTOP,
            "youtube":  self.CHROME,
        }

        if nombre_app in rutas_dinamicas:
            ruta = rutas_dinamicas[nombre_app]
            if not ruta:
                return f"No encontré la ruta de {nombre_app}."
            try:
                if nombre_app == "youtube":
                    subprocess.Popen([ruta, "https://www.youtube.com"],
                                     stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL)
                else:
                    subprocess.Popen([ruta],
                                     stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL)
                print(f"✅ Abriendo: {nombre_app}")
                return f"Abriendo {nombre_app}."
            except Exception as e:
                print(f"❌ Error dinámico: {e}")
                return f"No pude abrir {nombre_app}."

        return f"No encontré {nombre_app}."

    def cerrar_app(self, nombre_app):
        procesos_map = {
            "chrome":        ["chrome.exe"],
            "edge":          ["msedge.exe"],
            "spotify":       ["spotify.exe"],
            "discord":       ["discord.exe"],
            "whatsapp":      ["whatsapp.exe"],
            "notepad":       ["notepad.exe"],
            "calculadora":   ["calculatorapp.exe", "calc.exe"],
            "vscode":        ["code.exe"],
            "explorador":    ["explorer.exe"],
            "paint":         ["mspaint.exe"],
            "terminal":      ["cmd.exe"],
            "taskmanager":   ["taskmgr.exe"],
            "steam":         ["steam.exe"],
            "epic":          ["epicgameslauncher.exe"],
            "riot":          ["riotclientservices.exe"],
            "valorant":      ["valorant.exe"],
            "league":        ["leagueclient.exe"],
            "ea":            ["eadesktop.exe"],
            "fc26":          ["fc26.exe", "eadesktop.exe"],
            "brawlhalla":    ["brawlhalla.exe"],
            "battlenet":     ["battle.net.exe"],
            "github":        ["githubdesktop.exe"],
            "filmora":       ["filmora.exe"],
            "winrar":        ["winrar.exe"],
            "osu":           ["osu!.exe"],
            "teams":         ["ms-teams.exe", "teams.exe"],
            "outlook":       ["outlook.exe"],
            "csgo":          ["cs2.exe", "csgo.exe"],
        }

        nombres_proceso = procesos_map.get(nombre_app, [nombre_app + ".exe"])
        cerrados = 0

        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'].lower() in [p.lower() for p in nombres_proceso]:
                    proc.terminate()
                    cerrados += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        if cerrados:
            return f"Cerré {nombre_app}."
        return f"No encontré {nombre_app} en ejecución."

    def buscar_google(self, termino):
        url = f"https://www.google.com/search?q={urllib.parse.quote(termino)}"
        try:
            subprocess.Popen([self.CHROME, url],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
            print(f"🔍 Buscando en Google: {termino}")
            return f"Buscando {termino} en Google."
        except Exception:
            webbrowser.open(url)
            return f"Buscando {termino} en el navegador."

    def buscar_youtube(self, termino):
        url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(termino)}"
        try:
            subprocess.Popen([self.CHROME, url],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
            print(f"▶️ Buscando en YouTube: {termino}")
            return f"Buscando {termino} en YouTube."
        except Exception:
            webbrowser.open(url)
            return f"Buscando {termino} en YouTube."

    def apagar_equipo(self):
        subprocess.run(["shutdown", "/s", "/t", "30"], shell=True)
        return "Apagando el equipo en 30 segundos."

    def cambiar_volumen(self, direccion):
        try:
            tecla = "[char]175" if direccion == "subir" else "[char]174"
            subprocess.run(
                f'powershell -c "$obj = New-Object -ComObject WScript.Shell; $obj.SendKeys({tecla})"',
                shell=True
            )
        except Exception:
            pass
        return "Volumen subido." if direccion == "subir" else "Volumen bajado."