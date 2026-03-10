@echo off
echo Building InvenScan Windows executable...
pip install -r requirements.txt
pyinstaller invenscan.spec --clean
echo.
echo Build complete. Executable is in the dist/ folder.
pause
