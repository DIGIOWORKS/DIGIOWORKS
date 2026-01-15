@echo off
REM Build script for creating Windows executable

echo Building Inventory Management System executable...
echo.

REM Check if PyInstaller is installed
where pyinstaller >nul 2>nul
if %errorlevel% neq 0 (
    echo PyInstaller not found. Installing dependencies...
    pip install -r requirements.txt
)

REM Clean previous builds
echo Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Build the executable
echo Building executable...
pyinstaller inventory_app.spec

REM Check if build was successful
if exist "dist\InventoryManagement.exe" (
    echo.
    echo Build successful!
    echo Executable location: dist\InventoryManagement.exe
    echo.
) else (
    echo.
    echo Build failed! Check the output above for errors.
    exit /b 1
)

pause
