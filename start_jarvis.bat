@echo off
REM Lanzador silencioso de Jarvis MK2
cd /d "%~dp0"
set PYTHON=C:\Users\Sebastian\AppData\Local\Python\pythoncore-3.11-64\python.exe
start "" /B "%PYTHON%" main.py
