@echo off
title Indeed Login Launcher (Official Chrome)
cd /d "c:\projects\job-agent"
echo ===========================================================
echo            INDEED BROWSER LOGIN LAUNCHER
echo ===========================================================
echo.
echo Launching official Google Chrome with the agent's persistent profile...
echo (This allows reCAPTCHA and Google SSO to connect normally without bot detection)
echo.

if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --user-data-dir="c:\projects\job-agent\data\browser_profile" "https://secure.indeed.com/auth"
) else if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (
    start "" "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" --user-data-dir="c:\projects\job-agent\data\browser_profile" "https://secure.indeed.com/auth"
) else (
    .\venv\Scripts\python.exe open_indeed_login.py
)

echo.
echo Browser opened!
echo.
echo 1. Sign in to your Indeed account in the Chrome window.
echo 2. Once you are logged in and see your Indeed home page, close Chrome.
echo 3. Your login session will be permanently saved for the Job Agent.
echo.
pause
