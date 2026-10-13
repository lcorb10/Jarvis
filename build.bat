@echo off
setlocal

set PYTHON=C:\Users\Sebastian\AppData\Local\Python\pythoncore-3.11-64\python.exe
set PROJECT=%~dp0

echo.
echo  ===================================================
echo   J.A.R.V.I.S MK2  ^|  Build Script
echo  ===================================================
echo.

:: Verificar Python
%PYTHON% --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 3.11 no encontrado en: %PYTHON%
    pause & exit /b 1
)

:: Instalar / actualizar dependencias
echo [1/4] Instalando dependencias...
%PYTHON% -m pip install -r "%PROJECT%requirements.txt" --quiet
if errorlevel 1 (
    echo [WARN] Algunas dependencias fallaron, continuando...
)

:: Instalar PyInstaller si no está
%PYTHON% -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [INFO] Instalando PyInstaller...
    %PYTHON% -m pip install pyinstaller --quiet
)

:: Limpiar builds anteriores
echo [2/4] Limpiando builds anteriores...
if exist "%PROJECT%build" rmdir /s /q "%PROJECT%build"
if exist "%PROJECT%dist"  rmdir /s /q "%PROJECT%dist"

:: Compilar con PyInstaller
echo [3/4] Compilando con PyInstaller...
%PYTHON% -m PyInstaller "%PROJECT%jarvis.spec" --distpath "%PROJECT%dist" --workpath "%PROJECT%build" --noconfirm
if errorlevel 1 (
    echo [ERROR] PyInstaller falló.
    pause & exit /b 1
)

echo [4/4] Build completado.
echo.
echo  Ejecutable: %PROJECT%dist\JarvisMK2\JarvisMK2.exe
echo.

:: Preguntar si compilar instalador
set /p INNO="¿Compilar instalador con Inno Setup? (s/n): "
if /i "%INNO%"=="s" (
    if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
        "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" "%PROJECT%instalador.iss"
        echo  Instalador generado en: %PROJECT%dist\JarvisMK2_Setup.exe
    ) else (
        echo [WARN] Inno Setup no encontrado. Descarga desde https://jrsoftware.org/isdl.php
    )
)

echo.
echo  ===================================================
echo   Build finalizado correctamente
echo  ===================================================
pause
