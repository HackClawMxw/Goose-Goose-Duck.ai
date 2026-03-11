@echo off
echo Starting Goose-Goose-Duck.ai...

echo.
echo Starting Backend Server...
start cmd /k "cd /d %~dp0 && uvicorn backend.main:app --reload --port 8000"

timeout /t 3 /nobreak > nul

echo.
echo Starting Frontend Dev Server...
start cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ========================================
echo   Goose-Goose-Duck.ai is starting!
echo ========================================
echo.
echo   Backend API:  http://localhost:8000
echo   API Docs:     http://localhost:8000/docs
echo   Frontend:     http://localhost:5173
echo.
echo ========================================
pause
