@echo off
rem Resume the existing isolated RC2 acceptance data, not the personal environment.
"%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -X utf8 "%~dp0..\build\semifinal-202610\rc2\resume_agent_window.py"
if errorlevel 1 pause
