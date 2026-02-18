@echo off
echo ===========================================
echo   Engram Cortex - Ollama Setup
echo ===========================================
echo.

:: Check if Ollama is installed
where ollama >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Ollama is not installed or not in PATH.
    echo Please download it from: https://ollama.com
    echo Install it, then run this script again.
    pause
    exit /b 1
)

echo [INFO] Ollama found. Checking service...
:: Try to get tags to see if running
curl -s http://localhost:11434/api/tags >nul
if %errorlevel% neq 0 (
    echo [WARN] Ollama service might not be running.
    echo Starting Ollama...
    start ollama serve
    timeout /t 5 >nul
)

echo.
echo [INFO] Pulling Llama 3.1 (8B) - The best balance for reasoning...
echo This may take a while (4.7 GB)...
echo.
ollama pull llama3.1

echo.
echo [SUCCESS] Model ready.
echo You can now run 'python main.py' to use the AI.
pause
