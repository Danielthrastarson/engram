@echo off
REM ============================================
REM  ENGRAM MEMORY SYSTEM - ONE-CLICK LAUNCHER
REM ============================================

echo.
echo ========================================
echo   ENGRAM MEMORY SYSTEM V1
echo ========================================
echo.
echo Starting API Server...
echo.

REM Set Python path
set PYTHONPATH=c:\Users\Notandi\Desktop\agi\engram-system

REM Start API server in background
start "Engram API Server" cmd /k "python core/api.py"

REM Wait for server to start
timeout /t 3 /nobreak > nul

echo.
echo Opening Control Center...
start http://localhost:8000/control.html

echo.
echo Opening 3D Memory Universe...
timeout /t 1 /nobreak > nul
start http://localhost:8000/index.html

echo.
echo ========================================
echo   ENGRAM SYSTEM IS RUNNING!
echo ========================================
echo.
echo   Control Center: http://localhost:8000/control.html
echo   3D Universe:    http://localhost:8000/index.html
echo.
echo   Press any key to close this launcher...
echo   (API server will keep running in separate window)
echo.
pause > nul
