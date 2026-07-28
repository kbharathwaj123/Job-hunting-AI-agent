@echo off
title Setup Windows Background Task Scheduler for Job Agent

echo ============================================================
echo   Setting up Background Scheduled Task for Job Hunting Agent
echo ============================================================
echo.
echo Task Name: JobHuntingAIAgent
echo Trigger: Daily at 9:00 AM (and runs even if laptop is locked)
echo.

schtasks /create /tn "JobHuntingAIAgent" /tr "wscript.exe c:\projects\job-agent\run_background.vbs" /sc daily /st 09:00 /f /rl HIGHEST

echo.
echo ============================================================
echo   [SUCCESS 🎉] Scheduled Task 'JobHuntingAIAgent' Created!
echo ============================================================
echo  - It will run silently in the background even if laptop is locked.
echo  - To run it manually right now in the background, double click:
echo    c:\projects\job-agent\run_background.vbs
echo ============================================================
pause
