@echo off
cd /d "%~dp0"
echo Starting UNGDC web server...
python -m http.server 8080 --directory web
pause