# modulos/tools/game_updater.py
"""
Actualiza, instala y gestiona juegos de Steam y Epic Games.
"""
import os
import subprocess
import time
from pathlib import Path
from modulos.logger import log

_KNOWN_APPIDS = {
    "pubg": ("578080", "PUBG: Battlegrounds"),
    "gta5": ("271590", "Grand Theft Auto V"),
    "gta v": ("271590", "Grand Theft Auto V"),
    "cs2": ("730", "Counter-Strike 2"),
    "csgo": ("730", "Counter-Strike 2"),
    "counter-strike 2": ("730", "Counter-Strike 2"),
    "dota2": ("570", "Dota 2"),
    "dota 2": ("570", "Dota 2"),
    "rust": ("252490", "Rust"),
    "valheim": ("892970", "Valheim"),
    "cyberpunk 2077": ("1091500", "Cyberpunk 2077"),
    "elden ring": ("1245620", "ELDEN RING"),
    "minecraft": ("1672970", "Minecraft Launcher"),
    "apex legends": ("1172470", "Apex Legends"),
    "apex": ("1172470", "Apex Legends"),
    "fortnite": ("1517990", "Fortnite"),
    "among us": ("945360", "Among Us"),
    "fall guys": ("1097150", "Fall Guys"),
    "rocket league": ("252950", "Rocket League"),
    "warframe": ("230410", "Warframe"),
    "destiny 2": ("1085660", "Destiny 2"),
    "tf2": ("440", "Team Fortress 2"),
    "team fortress 2": ("440", "Team Fortress 2"),
    "left 4 dead 2": ("550", "Left 4 Dead 2"),
    "war thunder": ("236390", "War Thunder"),
    "brawlhalla": ("291550", "Brawlhalla"),
    "paladins": ("444090", "Paladins"),
    "lost ark": ("1599340", "Lost Ark"),
    "new world": ("1063730", "New World: Aeternum"),
}


def _find_steam() -> Path | None:
    posibles = [
        Path(r"C:\Program Files (x86)\Steam"),
        Path(r"C:\Program Files\Steam"),
        Path.home() / ".steam" / "steam",
    ]
    for p in posibles:
        if p.exists():
            return p
    # Buscar en registro
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                             r"SOFTWARE\WOW6432Node\Valve\Steam")
        path_str, _ = winreg.QueryValueEx(key, "InstallPath")
        p = Path(path_str)
        if p.exists():
            return p
    except Exception:
        pass
    return None


def _find_steamcmd() -> str | None:
    steam_path = _find_steam()
    if steam_path:
        exe = steam_path / "steam.exe"
        if exe.exists():
            return str(exe)
    return None


def game_updater(parameters: dict, speak=None) -> str:
    action = parameters.get("action", "update").lower()
    platform = parameters.get("platform", "both").lower()
    game_name = parameters.get("game_name", "").lower().strip()
    app_id = parameters.get("app_id", "")
    shutdown = parameters.get("shutdown_when_done", False)

    if action == "update":
        return _update_games(platform, speak)
    elif action == "install":
        return _install_game(game_name, app_id, platform, speak)
    elif action == "list":
        return _list_games(platform)
    elif action == "download_status":
        return _download_status()
    elif action == "launch":
        return _launch_game(game_name, app_id)
    else:
        return f"Acción desconocida: {action}"


def _update_games(platform: str, speak=None) -> str:
    resultados = []

    if platform in ("steam", "both"):
        r = _update_steam(speak)
        resultados.append(r)

    if platform in ("epic", "both"):
        r = _update_epic(speak)
        resultados.append(r)

    return " | ".join(resultados) if resultados else "No se realizaron actualizaciones."


def _update_steam(speak=None) -> str:
    steam_exe = _find_steamcmd()
    if not steam_exe:
        return "Steam no encontrado en el sistema."
    try:
        if speak:
            speak("Iniciando actualización de Steam, señor.")
        subprocess.Popen(
            [steam_exe, "-silent", "-login", "anonymous"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        time.sleep(2)
        subprocess.Popen(
            [steam_exe, "steam://updateui"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        return "Steam abierto con actualizaciones en marcha."
    except Exception as e:
        log.error(f"Steam update error: {e}")
        return f"Error actualizando Steam: {e}"


def _update_epic(speak=None) -> str:
    epic_exe = r"C:\Program Files (x86)\Epic Games\Launcher\Portal\Binaries\Win32\EpicGamesLauncher.exe"
    if not Path(epic_exe).exists():
        return "Epic Games Launcher no encontrado."
    try:
        subprocess.Popen([epic_exe], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return "Epic Games Launcher abierto."
    except Exception as e:
        return f"Error abriendo Epic: {e}"


def _install_game(game_name: str, app_id: str, platform: str, speak=None) -> str:
    if platform in ("steam", "both"):
        # Buscar app_id si no se proporcionó
        if not app_id and game_name:
            for nombre, (aid, titulo) in _KNOWN_APPIDS.items():
                if nombre in game_name or game_name in nombre:
                    app_id = aid
                    game_name = titulo
                    break

        if app_id:
            steam_exe = _find_steamcmd()
            if steam_exe:
                try:
                    if speak:
                        speak(f"Instalando {game_name} desde Steam, señor.")
                    subprocess.Popen(
                        [steam_exe, f"steam://install/{app_id}"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                    )
                    return f"Instalación de {game_name} iniciada desde Steam."
                except Exception as e:
                    return f"Error instalando: {e}"
            return "Steam no encontrado."
        return f"No encontré el App ID para '{game_name}'. Proporciona el app_id manualmente."

    if platform == "epic":
        return _update_epic(speak)

    return f"No pude instalar '{game_name}'."


def _list_games(platform: str) -> str:
    resultados = []
    if platform in ("steam", "both"):
        steam_path = _find_steam()
        if steam_path:
            apps_dir = steam_path / "steamapps"
            if apps_dir.exists():
                juegos = [f.stem.replace("appmanifest_", "")
                          for f in apps_dir.glob("appmanifest_*.acf")]
                resultados.append(f"Steam: {len(juegos)} juegos instalados.")
            else:
                resultados.append("Steam: directorio de apps no encontrado.")
        else:
            resultados.append("Steam: no instalado.")
    return "\n".join(resultados) if resultados else "No se encontraron juegos."


def _download_status() -> str:
    steam_exe = _find_steamcmd()
    if steam_exe:
        try:
            subprocess.Popen(
                [steam_exe, "steam://open/downloads"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            return "Abriendo estado de descargas de Steam."
        except Exception:
            pass
    return "No pude abrir el estado de descargas."


def _launch_game(game_name: str, app_id: str) -> str:
    if not app_id and game_name:
        for nombre, (aid, titulo) in _KNOWN_APPIDS.items():
            if nombre in game_name or game_name in nombre:
                app_id = aid
                break
    if app_id:
        steam_exe = _find_steamcmd()
        if steam_exe:
            try:
                subprocess.Popen(
                    [steam_exe, f"-applaunch", app_id],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
                return f"Lanzando juego (ID: {app_id})."
            except Exception as e:
                return f"Error: {e}"
    return f"No pude lanzar '{game_name}'."
