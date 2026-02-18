@echo off
REM Fix merge conflict - keep local README

echo Resolving conflict by keeping local README...
git checkout --ours README.md
git add README.md

echo Completing merge...
git commit -m "Merged with remote, keeping comprehensive local README"

echo Pushing to GitHub...
git push -u origin main

echo.
echo ========================================
echo   SUCCESS!
echo ========================================
echo.
echo Visit: https://github.com/Danielthrastarson/engram
echo.
pause
