@echo off
echo ===========================================
echo Starting Automated Build Script
echo ===========================================

echo.
echo [1/2] Converting python to main.exe
python -m PyInstaller -w -F --icon=icon.ico --add-data "icon.ico;." --add-data "icon.png;." main.py

echo.
echo [2/2] Compiling Setup_Script.iss
set "ISCC_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if exist "%LocalAppData%\Programs\Inno Setup 6\ISCC.exe" set "ISCC_PATH=%LocalAppData%\Programs\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC_PATH=%ProgramFiles%\Inno Setup 6\ISCC.exe"

"%ISCC_PATH%" Setup_Script.iss

echo.
echo ===========================================
echo [SUCCESS] Pipeline Completed!
echo ===========================================
pause
