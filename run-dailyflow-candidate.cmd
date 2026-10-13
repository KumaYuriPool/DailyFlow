@echo off
rem Stage-B candidate with the merged 2026-10-14 U fixes; reuse existing review state in place.
"C:\Users\44231\AppData\Local\Programs\Python\Python313\python.exe" -X utf8 "%~dp0build\overnight-20261013\integration-r1\run_candidate.py" %*
if errorlevel 1 pause
