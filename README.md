# Inventory Management System

A standalone GUI-based inventory management application designed to help users research, describe, and manage items for sale, primarily for the eBay Marketplace. This tool provides comprehensive inventory tracking, web-based item research, and CSV export capabilities.

## Features

### 🖼️ Item Input
- **Photo Upload**: Upload product images for your inventory items
- **Barcode Scanning**: Interface for barcode scanning (hardware integration ready)
- **Manual Entry**: Complete form for entering item details

### 📊 Inventory Management
- **Full CRUD Operations**: Create, Read, Update, and Delete inventory items
- **Search & Filter**: Quick search across titles, descriptions, and categories
- **Real-time Stats**: View total items, quantities, and inventory value
- **Edit Mode**: Load items for editing with pre-filled forms

### 🔍 Web Search & Research
- **Smart Suggestions**: Get clickable search refinements based on your query
- **Terapeak-Style Results**: Simulated market research data including:
  - Average prices by condition
  - Price ranges
  - Sell-through rates
  - Days to sell
  - Total listings and sold counts

### 💾 Database
- **SQLite Backend**: Reliable local database storage
- **Listing Counter**: Synchronized listing numbers across all instances
- **Data Persistence**: All data stored locally in `inventory.db`

### 📤 Export Capabilities
- **CSV Export**: Export inventory to flat file with columns:
  - Title (automatically capitalized)
  - Price
  - Quantity
  - Condition
  - Description
  - Category
  - Image Path
- **Custom Save Location**: Choose where to save exported files

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup

1. Clone the repository:
```bash
git clone https://github.com/DIGIOWORKS/DIGIOWORKS.git
cd DIGIOWORKS
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Running the Application

To launch the application:
```bash
python inventory_app.py
```

### Application Tabs

#### 1. Item Input Tab
- Upload or scan item images
- Enter item details:
  - Title
  - Price
  - Quantity
  - Condition (New, Used, Refurbished, etc.)
  - Category
  - Description
- Save items to inventory

#### 2. Inventory Overview Tab
- View all inventory items in a table
- Search and filter items
- Edit existing items
- Delete items
- Export inventory to CSV
- View inventory statistics

#### 3. Web Search & Research Tab
- Enter search queries for item research
- View clickable search suggestions
- See market research data (Terapeak-style):
  - Price recommendations
  - Condition-based pricing
  - Market trends
  - Selling statistics

## Building Windows Executable

To create a standalone `.exe` file for Windows:

### Using PyInstaller Spec File

```bash
pyinstaller inventory_app.spec
```

The executable will be created in the `dist` folder as `InventoryManagement.exe`.

### Manual Build (Alternative)

```bash
pyinstaller --onefile --windowed --name "InventoryManagement" inventory_app.py
```

### Distribution

The built executable can be distributed as a standalone application. Users do not need Python installed to run it.

## Project Structure

```
DIGIOWORKS/
├── inventory_app.py       # Main GUI application
├── database.py            # SQLite database operations
├── web_search.py          # Web search and research functionality
├── utils.py               # Utility functions (CSV export, validation)
├── requirements.txt       # Python dependencies
├── inventory_app.spec     # PyInstaller configuration
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

## Dependencies

- **PyQt5**: GUI framework
- **Pillow**: Image processing
- **requests**: HTTP library for web features
- **pyzbar**: Barcode scanning library
- **opencv-python**: Image processing
- **pyinstaller**: Executable builder

## Database Schema

### Inventory Table
- `id`: Primary key
- `title`: Item title
- `price`: Item price
- `quantity`: Stock quantity
- `condition`: Item condition
- `description`: Detailed description
- `category`: Item category
- `image_path`: Path to item image
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

### Listing Counter Table
- `id`: Primary key (always 1)
- `next_listing_number`: Next available listing number

## Future Enhancements

This stage acts as the foundation for:
- Direct eBay API integration
- Automated listing creation
- Advanced image recognition
- Real-time market data
- Multi-marketplace support
- Cloud synchronization

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

This project is provided as-is for inventory management purposes.

## Support

For issues or questions, please open an issue on GitHub.
