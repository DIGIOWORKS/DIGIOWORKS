# Quick Start Guide

## Installation and Setup

### Step 1: Install Python
- Download and install Python 3.8 or higher from [python.org](https://www.python.org/downloads/)
- During installation, check "Add Python to PATH"

### Step 2: Install Dependencies
Open a terminal/command prompt in the project directory and run:
```bash
pip install -r requirements.txt
```

### Step 3: Run the Application
```bash
python inventory_app.py
```

## Using the Application

### Adding Items

1. **Go to "Item Input" tab**
2. **Upload a photo** (optional):
   - Click "Upload Photo" button
   - Select an image file from your computer
3. **Enter item details**:
   - Title: Name of your item
   - Price: Selling price
   - Quantity: Number in stock
   - Condition: Select from dropdown
   - Category: Item category (e.g., Electronics, Clothing)
   - Description: Detailed item description
4. **Click "Save Item"**

### Managing Inventory

1. **Go to "Inventory Overview" tab**
2. **Search items**: Use the search box to filter by title, description, or category
3. **Edit item**: Click "Edit" button in the Actions column
4. **Delete item**: Click "Delete" button (requires confirmation)
5. **Export to CSV**: Click "Export to CSV" button to save inventory data

### Research Items

1. **Go to "Web Search & Research" tab**
2. **Enter search query**: Type item description
3. **Click "Search"**
4. **View suggestions**: Click any suggestion to refine your search
5. **Review market data**: See pricing, sell-through rates, and other metrics

## Building Standalone Executable

### On Windows:
Double-click `build.bat` or run in command prompt:
```cmd
build.bat
```

### On Linux/Mac:
```bash
./build.sh
```

The executable will be created in the `dist` folder.

## Tips

- **Automatic title capitalization**: When you export to CSV, all titles are automatically capitalized
- **Search is instant**: The inventory search updates as you type
- **Market research**: Use the research tab to find optimal pricing for your items
- **Backup your database**: The `inventory.db` file contains all your data - back it up regularly

## Troubleshooting

### Application won't start
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check Python version: `python --version` (should be 3.8+)

### Can't upload images
- Ensure the image file format is supported (PNG, JPG, JPEG, BMP, GIF)
- Check file permissions

### Build fails
- Ensure PyInstaller is installed: `pip install pyinstaller`
- Try running: `pyinstaller --version` to verify installation

## Need Help?

Open an issue on GitHub with:
- Description of the problem
- Error messages (if any)
- Steps to reproduce
