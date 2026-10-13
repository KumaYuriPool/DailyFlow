@echo off
rem Local development build. Uses a separate persistent data directory.
rem 2026-10-12 latest-runtime acceptance combination (see docs/LATEST_RUNTIME_ACCEPTANCE_20261012.md):
rem shell r7 9e239ef3 / kernel c2e1c575 561831b6 / hub fa3e50f2 / card-host 62304027 (first-card patch).
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0run-dailyflow-ai.ps1" -Binary "%~dp0..\build\latest-runtime-20261012-r1\shell\target\release\octosense.exe" -KernelBinary "%~dp0..\build\latest-runtime-20261012-r1\kernel-src\target\release\octos.exe" -HubBinary "%~dp0..\build\latest-runtime-20261012-r1\hub\target\release\hub.exe" -Bundle "%~dp0bundle" -DataDir "%~dp0.local-state\latest-desktop" %*
if errorlevel 1 pause
