@echo off
echo ============================================================
echo   Pushing BIA Academic Curriculum to GitHub
echo ============================================================
git push -u origin main
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Push failed. If the repository does not exist yet on GitHub,
    echo please create a new repository named 'bia-academic-curriculum'
    echo at https://github.com/new and make sure you are logged into Git.
) else (
    echo.
    echo [SUCCESS] Successfully deployed to GitHub!
)
pause
