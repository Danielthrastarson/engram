@echo off
title Engram Memory System
echo Starting Engram Cortex...
echo.

:: Set Python Path to current directory
set PYTHONPATH=%~dp0

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found! Please install Python 3.10+
    pause
    exit /b
)

:: Run the system
python main.py

pause
