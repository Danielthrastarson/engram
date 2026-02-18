@echo off
REM ============================================
REM  FIX GITHUB PUSH - MERGE REMOTE CHANGES
REM ============================================

echo.
echo Pulling remote changes and merging...
echo.

REM Pull with allow unrelated histories
git pull origin main --allow-unrelated-histories --no-edit

if errorlevel 1 (
    echo.
    echo If there are merge conflicts, resolve them manually.
    echo Then run: git push
    pause
    exit /b 1
)

echo.
echo Pushing to GitHub...
git push -u origin main

if errorlevel 1 (
    echo.
    echo Push failed. Check error above.
    pause
    exit /b 1
) else (
    echo.
    echo ========================================
    echo   SUCCESS!
    echo ========================================
    echo.
    echo Your code is now on GitHub!
    echo Visit: https://github.com/Danielthrastarson/engram
    echo.
    pause
)
