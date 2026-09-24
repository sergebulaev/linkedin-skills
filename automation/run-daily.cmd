@echo off
rem Draft-only LinkedIn comment candidates. Intended for Windows Task Scheduler.
setlocal
cd /d "%~dp0.."
if not exist "%~dp0logs" mkdir "%~dp0logs"
set "NODE_EXE=C:\Program Files\nodejs\node.exe"
if not exist "%NODE_EXE%" set "NODE_EXE=node"
echo ===== %DATE% %TIME% run-daily.cmd %* >> "%~dp0logs\scheduler.log"
"%NODE_EXE%" "%~dp0run-daily.js" %* >> "%~dp0logs\scheduler.log" 2>&1
exit /b %ERRORLEVEL%
