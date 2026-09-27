@echo off
cd /d "%~dp0"
echo ============================================================
echo   Pushing BIA Academic Curriculum to GitHub: bia-course-material
echo ============================================================
git remote set-url origin https://github.com/pralayasimha23/bia-course-material.git
git push -u origin main
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [NOTE] If Git requested credentials or failed, you can enter a GitHub Personal Access Token (PAT) below.
    echo To create a PAT: go to https://github.com/settings/tokens (classic token with 'repo' scope).
    echo.
    set /p GHPAT="Paste your GitHub Personal Access Token (or press Enter to cancel): "
    if defined GHPAT (
        echo Pushing using token...
        git push https://pralayasimha23:%GHPAT%@github.com/pralayasimha23/bia-course-material.git main
        if %ERRORLEVEL% EQU 0 (
            git remote set-url origin https://pralayasimha23:%GHPAT%@github.com/pralayasimha23/bia-course-material.git
            echo.
            echo [SUCCESS] Successfully deployed to GitHub repository 'bia-course-material'!
        ) else (
            echo.
            echo [ERROR] Token push failed. Please verify your token permissions.
        )
    )
) else (
    echo.
    echo [SUCCESS] Successfully deployed to GitHub repository 'bia-course-material'!
)
pause

