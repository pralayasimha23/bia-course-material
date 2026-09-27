@echo off
cd /d "%~dp0"
echo ================================================================
echo   BIA SharePoint Physical File Downloader
echo ================================================================
echo A browser will open for SharePoint / Microsoft authentication.
echo Please log in to your account.
echo.
python download_materials.py --login
echo.
echo Syncing downloaded files with GitHub...
git add lessons/
git commit -m "feat(materials): download and store physical class notes, slides, and notebooks"
git push origin main
echo.
echo ================================================================
echo All files downloaded and pushed to GitHub!
echo ================================================================
pause
