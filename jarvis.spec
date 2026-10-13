# -*- mode: python ; coding: utf-8 -*-
import os
from pathlib import Path

ROOT = Path(SPECPATH)

block_cipher = None

a = Analysis(
    [str(ROOT / 'main.py')],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        (str(ROOT / 'modelos' / 'vosk-es'), 'modelos/vosk-es'),
        (str(ROOT / 'config.json'), '.'),
        *( [(str(ROOT / '.env'), '.')] if (ROOT / '.env').exists() else [] ),
    ],
    hiddenimports=[
        # PySide6
        'PySide6.QtWidgets', 'PySide6.QtCore', 'PySide6.QtGui',
        # Vosk / audio
        'vosk', 'sounddevice', 'numpy',
        # TTS
        'edge_tts', 'pyttsx3', 'pygame', 'pygame.mixer',
        # IA — google-genai nuevo SDK
        'requests', 'google.genai', 'google.genai.types',
        'google.auth', 'google.auth.transport',
        # Tools
        'psutil', 'pyautogui', 'pyperclip', 'PIL', 'mss',
        # Utils
        'dotenv', 'watchdog.observers', 'watchdog.events',
        'aiohttp', 'asyncio', 'wave',
        # Módulos propios
        'modulos.logger', 'modulos.memoria', 'modulos.intenciones',
        'modulos.limpiador_texto', 'modulos.detector_aplausos',
        'modulos.reconocimiento_voz', 'modulos.sintesis_voz',
        'modulos.ia_local', 'modulos.control_sistema',
        'modulos.detector_rutas', 'modulos.config_manager',
        'modulos.gemini_manager', 'modulos.aprendizaje',
        'modulos.apis.gestor_apis', 'modulos.apis.clima',
        'modulos.apis.noticias', 'modulos.apis.youtube_api',
        'modulos.apis.traductor', 'modulos.apis.matematica',
        'modulos.agent.planner', 'modulos.agent.executor',
        'modulos.agent.task_queue', 'modulos.agent.error_handler',
        'modulos.tools.registry',
        'modulos.tools.computer_control', 'modulos.tools.file_controller',
        'modulos.tools.screen_processor', 'modulos.tools.send_message',
        'modulos.tools.code_helper', 'modulos.tools.game_updater',
        'modulos.tools.web_search', 'modulos.tools.openclaw',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'scipy', 'tkinter', 'notebook'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='JarvisMK2',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,           # Sin ventana de consola
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,               # Reemplazar con ruta a .ico si existe
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='JarvisMK2',
)
