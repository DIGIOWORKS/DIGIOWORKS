# Application Screenshots Guide

Since this is a GUI application and screenshots cannot be generated in a headless environment, here's a detailed description of what the application looks like when running:

## Main Window

### Window Title
"Inventory Management System"

### Dimensions
1400x800 pixels (default size, resizable)

### Status Bar
Bottom of window shows current operation status

---

## Tab 1: Item Input

### Layout
Split into two columns:

#### Left Column - Image Section
- **Image Display Area**: 400x400 pixel box with gray border
- **Default State**: "No image loaded" text
- **Three Buttons Below**:
  - "Upload Photo" - Opens file dialog
  - "Scan Barcode" - Info dialog (hardware integration ready)
  - "Clear Image" - Removes loaded image

#### Right Column - Item Details Form
- **Title Field**: Full-width text input
- **Price & Quantity Row**: 
  - Price: Dollar-prefixed decimal input ($0.00 format)
  - Quantity: Integer spin box (0-999999)
- **Condition Dropdown**: 6 options
  - New
  - Used - Like New
  - Used - Good
  - Used - Fair
  - Refurbished
  - For Parts
- **Category Field**: Text input
- **Description Area**: Multi-line text box (150px height)
- **Action Buttons**:
  - "Save Item" - Green button (10px padding, 14px font)
  - "Clear Form" - Standard button

---

## Tab 2: Inventory Overview

### Search Bar (Top)
- Label "Search:"
- Text input with placeholder "Search by title, description, or category"
- "Refresh" button

### Inventory Table
- **8 Columns**:
  1. ID (50px width)
  2. Title (stretches to fill)
  3. Price (80px width)
  4. Quantity (80px width)
  5. Condition (120px width)
  6. Category (120px width)
  7. Created (150px width)
  8. Actions (150px width)

- **Actions Column** contains two buttons per row:
  - "Edit" - Standard button
  - "Delete" - Red button

### Bottom Bar
- Left: "Export to CSV" button (blue background, white text)
- Right: Statistics label showing:
  - Total Items: X
  - Total Quantity: Y
  - Total Value: $Z.ZZ

---

## Tab 3: Web Search & Research

### Top Section - Search Input
- Label "Search Query:"
- Text input with placeholder "Enter item description for research"
- "Search" button (orange background, white text)

### Split Panel (Horizontal)

#### Left Panel (40% width) - Search Suggestions
- Title: "Search Suggestions"
- List widget showing clickable suggestions
- Each suggestion is a separate clickable item

#### Right Panel (60% width) - Market Research Results
- Title: "Market Research Results (Terapeak-style)"
- Read-only text area with HTML formatting
- Shows structured data:
  - Result heading with item name
  - Condition-specific sections with blue left border
  - Each section displays:
    - Title sample
    - Condition
    - Average price
    - Price range
    - Average shipping
    - Sell-through rate (percentage)
    - Average days to sell
    - Listing/sold statistics

---

## Color Scheme

### Buttons
- **Save/Success**: #4CAF50 (Green)
- **Info/Export**: #2196F3 (Blue)
- **Warning/Search**: #FF9800 (Orange)
- **Danger/Delete**: #f44336 (Red)

### Backgrounds
- **Results sections**: #f9f9f9 (Light gray)
- **Image placeholder**: #f0f0f0 (Gray)

### Borders
- **Image frame**: #ccc (2px solid)
- **Result sections**: #2196F3 (4px left border)

---

## Dialogs

### Success Messages
- Icon: Information
- Green-themed

### Error Messages
- Icon: Warning/Critical
- Red-themed

### Confirmations
- Icon: Question
- Yes/No buttons

---

## Application Behavior

### Responsive Features
- Window is resizable
- Table columns adjust appropriately
- Title column stretches to fill available space

### Interactive Elements
- All buttons show hover effects
- Table rows can be selected
- Search updates instantly as you type
- Clickable suggestions update search query

### Visual Feedback
- Status bar updates with operation messages
- Image preview updates immediately on upload
- Table refreshes after add/edit/delete operations
- Statistics update automatically

---

## Window Style
- **Theme**: Fusion (modern Qt theme)
- **Font**: System default
- **Padding**: Consistent 8-10px throughout
- **Spacing**: Clean, organized layouts

---

To see the actual application, run:
```bash
python inventory_app.py
```

All visual elements are implemented in PyQt5 and follow modern desktop application design patterns.
