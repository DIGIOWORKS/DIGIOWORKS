#!/bin/bash
# Build script for creating Windows executable

echo "Building Inventory Management System executable..."
echo ""

# Check if PyInstaller is installed
if ! command -v pyinstaller &> /dev/null
then
    echo "PyInstaller not found. Installing dependencies..."
    pip install -r requirements.txt
fi

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build dist

# Build the executable
echo "Building executable..."
pyinstaller inventory_app.spec

# Check if build was successful
if [ -f "dist/InventoryManagement" ] || [ -f "dist/InventoryManagement.exe" ]; then
    echo ""
    echo "Build successful!"
    echo "Executable location: dist/InventoryManagement"
    echo ""
else
    echo ""
    echo "Build failed! Check the output above for errors."
    exit 1
fi
