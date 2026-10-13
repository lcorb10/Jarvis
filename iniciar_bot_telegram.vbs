Set oShell = CreateObject("WScript.Shell")
oShell.Run "wsl -e bash -c ""tmux new-session -A -s jarvis bash /home/sebastian/start_jarvis_bot.sh""", 0, False
