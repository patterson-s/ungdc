@echo off
cd /d "%~dp0"
echo Starting UNGDC API server...
uvicorn api.main:app --reload
pause