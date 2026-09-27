@echo off
cd /d "%~dp0"
echo ================================================================
echo Setting up Windows Task Scheduler for BIA Course Material Sync
echo Runs every Monday at 09:30 AM IST
echo ================================================================

set PYTHON_PATH=%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe
set SCRIPT_PATH=%~dp0sync_curriculum.py

if not exist "%PYTHON_PATH%" (
    for /f "tokens=*" %%i in ('where python') do (
        set PYTHON_PATH=%%i
        goto :found_python
    )
)
:found_python

echo Using Python: "%PYTHON_PATH%"
echo Target Script: "%SCRIPT_PATH%"

echo.
echo Registering Monday 09:30 AM Weekly Task...
schtasks /Create /SC WEEKLY /D MON /TN "BIA_CurriculumSync_Monday" /TR "\"%PYTHON_PATH%\" \"%SCRIPT_PATH%\"" /ST 09:30 /F

echo.
echo ================================================================
echo Done! Weekly task has been registered.
echo You can view or run it anytime in Windows Task Scheduler:
echo Task Name: BIA_CurriculumSync_Monday
echo ================================================================
pause
