@echo off
REM ============================================
REM  ENGRAM SYSTEM - PUSH TO GITHUB
REM ============================================

echo.
echo ========================================
echo   PUSH ENGRAM SYSTEM TO GITHUB
echo ========================================
echo.

REM Check if git is installed
git --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Git is not installed!
    echo.
    echo Download from: https://git-scm.com/download/win
    echo.
    pause
    exit /b 1
)

REM Check if already initialized
if not exist .git (
    echo Initializing Git repository...
    git init
    echo.
)

REM Add all files
echo Adding all files...
git add .
echo.

REM Commit
set /p commit_msg="Enter commit message (or press Enter for default): "
if "%commit_msg%"=="" (
    set commit_msg=Update: Engram Memory System with 16 phases and Truth Guard
)

git commit -m "%commit_msg%"
echo.

REM Check if remote exists
git remote -v | find "origin" >nul 2>&1
if errorlevel 1 (
    echo.
    echo ========================================
    echo   GITHUB REPOSITORY SETUP
    echo ========================================
    echo.
    echo First, create a repository on GitHub:
    echo 1. Go to: https://github.com/new
    echo 2. Repository name: engram-system
    echo 3. Don't initialize with README
    echo 4. Click Create
    echo.
    set /p repo_url="Enter your GitHub repository URL (e.g., https://github.com/username/engram-system.git): "
    
    git remote add origin !repo_url!
    echo.
    echo Remote added: !repo_url!
    echo.
)

REM Push to GitHub
echo Pushing to GitHub...
echo.
echo NOTE: When prompted for password, use your Personal Access Token
echo Create one at: https://github.com/settings/tokens
echo.

git branch -M main
git push -u origin main

if errorlevel 1 (
    echo.
    echo ========================================
    echo   PUSH FAILED
    echo ========================================
    echo.
    echo Common issues:
    echo - Make sure you're using a Personal Access Token, not password
    echo - Check repository URL is correct
    echo - Verify you have write access to the repository
    echo.
    pause
    exit /b 1
) else (
    echo.
    echo ========================================
    echo   SUCCESS! 
    echo ========================================
    echo.
    echo Your code is now on GitHub!
    echo Visit your repository to see it.
    echo.
    pause
)
