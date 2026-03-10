## InvenScan

A standalone GUI inventory management and barcode scanning application built with Python, PyQt5, and SQLite.

### Features

- **📷 Item Input** — Upload photos, scan barcodes/QR codes with your webcam, or enter details manually
- **📦 Inventory Management** — View, search, filter, edit, and delete inventory items with status tracking (active / draft / sold)
- **🔍 Market Research** — Dual-panel eBay marketplace research (active listings vs. sold/completed items)
- **🖼 Image Machine** — Built-in image editor with rotate, flip, brightness/contrast controls and auto-naming
- **📤 CSV Export** — One-click export with auto-capitalized titles
- **🔢 Listing Numbers** — Synchronized listing number counter across all sessions

### Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.8+ |
| GUI | PyQt5 |
| Database | SQLite |
| Barcode scanning | pyzbar + OpenCV |
| eBay integration | eBay Finding & Browse APIs |
| Build | PyInstaller |

### Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python invenscan.py

# Run tests
python -m pytest test_invenscan.py -v

# Build Windows executable
build.bat   # Windows
./build.sh  # Linux / macOS
```

### Web Inventory Page (`index.php`)

A lightweight PHP/HTML scanning page for rapid inventory entry:

- Enter an **ItemID** (numeric) and a **Location** string
- Once **4 or more characters** are typed in the Location field, the form **auto-submits within 0.5 seconds** — no need to press Enter or click Submit
- Each submission appends a tab-delimited record to `inventory.csv` and `inventory-history.csv`
- A **Print** button triggers label printing via `printer.csv`

**Dependencies:** PHP with file-write permissions; `print.php` helper in the same directory.
