' Lanza Jarvis MK2 sin mostrar ventana de consola
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "cmd /c """"" & WScript.ScriptFullName & "\..\start_jarvis.bat""""", 0, False
