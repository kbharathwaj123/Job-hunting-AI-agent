@echo off
title Job Agent Run
cd /d "c:\projects\job-agent"
echo =========================================
echo       STARTING AUTOMATED JOB AGENT
echo =========================================
echo.
echo [INFO] Activating Python virtual environment...
call venv\Scripts\activate.bat
echo.
echo [INFO] Launching Job Agent...
python main.py
echo.
echo =========================================
echo       JOB AGENT RUN COMPLETED
echo =========================================
echo.
pause
