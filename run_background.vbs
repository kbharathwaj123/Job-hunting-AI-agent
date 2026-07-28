Dim WinScriptHost
Set WinScriptHost = CreateObject("WScript.Shell")
Dim projectDir
projectDir = "c:\projects\job-agent"

' Run main.py silently in headless background mode with no command prompt window
WinScriptHost.Run "cmd /c cd /d " & projectDir & " && venv\Scripts\python.exe main.py --mode 2 --headless > data\background_run.log 2>&1", 0, False
Set WinScriptHost = Nothing
