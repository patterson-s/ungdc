@echo off
cd /d "%~dp0"
echo Starting UNGDC full system...
echo.

start "API Server" cmd /k "cd /d "%~dp0\ungdc_web" && uvicorn api.main:app --reload"
timeout /t 2 /nobreak >nul
echo API server should be running at http://localhost:8000
echo.

start "Web Server" cmd /k "cd /d "%~dp0\ungdc_web" && python -m http.server 8080 --directory web"
timeout /t 2 /nobreak >nul
echo Web interface should be available at http://localhost:8080
echo.

echo Both servers are starting...
echo Press any key to exit this window (servers will continue running)
pause >nul