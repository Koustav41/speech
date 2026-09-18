@echo off
title Multilingual Speech Hub Launcher
echo ===================================================
echo   Starting Multilingual Speech Hub
echo ===================================================
echo.

cd /d "%~dp0"

echo [1/2] Launching FastAPI Backend on http://localhost:8000 ...
start "Speech Backend (FastAPI)" cmd /k "cd backend && .\venv\Scripts\activate && uvicorn main:app --reload --host 127.0.0.1 --port 8000"

timeout /t 2 /nobreak >nul

echo [2/2] Launching React Frontend on http://localhost:5173 ...
start "Speech Frontend (Vite)" cmd /k "cd frontend && npm run dev"

echo.
echo ===================================================
echo   Both services are starting!
echo   - Web UI:  http://localhost:5173
echo   - Backend: http://localhost:8000
echo   - Docs:    http://localhost:8000/docs
echo ===================================================
echo.
pause
