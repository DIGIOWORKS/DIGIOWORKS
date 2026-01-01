"""
Main GUI application for Inventory Management System.
A standalone tool for researching, describing, and managing items for sale.
"""

import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTabWidget, QPushButton, QLabel, QLineEdit, QTextEdit, QTableWidget,
    QTableWidgetItem, QFileDialog, QMessageBox, QComboBox, QSpinBox,
    QDoubleSpinBox, QGroupBox, QListWidget, QSplitter, QHeaderView
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QIcon

from database import InventoryDatabase
from web_search import WebSearcher
from utils import export_to_csv, validate_item_data, format_price, truncate_text


class InventoryManagementApp(QMainWindow):
    """Main application window for inventory management."""
    
    def __init__(self):
        super().__init__()
        self.db = InventoryDatabase()
        self.searcher = WebSearcher()
        self.current_image_path = ""
        self.current_item_id = None
        
        self.init_ui()
        self.refresh_inventory_table()
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Inventory Management System")
        self.setGeometry(100, 100, 1400, 800)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create tab widget for different sections
        tabs = QTabWidget()
        main_layout.addWidget(tabs)
        
        # Tab 1: Item Input
        self.item_input_tab = self.create_item_input_tab()
        tabs.addTab(self.item_input_tab, "Item Input")
        
        # Tab 2: Inventory Overview
        self.inventory_tab = self.create_inventory_tab()
        tabs.addTab(self.inventory_tab, "Inventory Overview")
        
        # Tab 3: Web Search & Research
        self.search_tab = self.create_search_tab()
        tabs.addTab(self.search_tab, "Web Search & Research")
        
        # Status bar
        self.statusBar().showMessage("Ready")
    
    def create_item_input_tab(self):
        """Create the item input tab."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        
        # Left side: Image and input controls
        left_panel = QVBoxLayout()
        
        # Image display group
        image_group = QGroupBox("Item Image")
        image_layout = QVBoxLayout()
        
        self.image_label = QLabel()
        self.image_label.setFixedSize(400, 400)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("border: 2px solid #ccc; background-color: #f0f0f0;")
        self.image_label.setText("No image loaded")
        image_layout.addWidget(self.image_label)
        
        # Image control buttons
        image_buttons = QHBoxLayout()
        
        upload_btn = QPushButton("Upload Photo")
        upload_btn.clicked.connect(self.upload_photo)
        image_buttons.addWidget(upload_btn)
        
        scan_barcode_btn = QPushButton("Scan Barcode")
        scan_barcode_btn.clicked.connect(self.scan_barcode)
        image_buttons.addWidget(scan_barcode_btn)
        
        clear_image_btn = QPushButton("Clear Image")
        clear_image_btn.clicked.connect(self.clear_image)
        image_buttons.addWidget(clear_image_btn)
        
        image_layout.addLayout(image_buttons)
        image_group.setLayout(image_layout)
        left_panel.addWidget(image_group)
        
        left_panel.addStretch()
        layout.addLayout(left_panel)
        
        # Right side: Item details form
        right_panel = QVBoxLayout()
        
        details_group = QGroupBox("Item Details")
        details_layout = QVBoxLayout()
        
        # Title
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel("Title:"))
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Enter item title")
        title_layout.addWidget(self.title_input)
        details_layout.addLayout(title_layout)
        
        # Price
        price_layout = QHBoxLayout()
        price_layout.addWidget(QLabel("Price:"))
        self.price_input = QDoubleSpinBox()
        self.price_input.setPrefix("$ ")
        self.price_input.setMaximum(999999.99)
        self.price_input.setDecimals(2)
        price_layout.addWidget(self.price_input)
        
        # Quantity
        price_layout.addWidget(QLabel("Quantity:"))
        self.quantity_input = QSpinBox()
        self.quantity_input.setMinimum(0)
        self.quantity_input.setMaximum(999999)
        self.quantity_input.setValue(1)
        price_layout.addWidget(self.quantity_input)
        details_layout.addLayout(price_layout)
        
        # Condition
        condition_layout = QHBoxLayout()
        condition_layout.addWidget(QLabel("Condition:"))
        self.condition_input = QComboBox()
        self.condition_input.addItems([
            "New", 
            "Used - Like New", 
            "Used - Good", 
            "Used - Fair",
            "Refurbished",
            "For Parts"
        ])
        self.condition_input.setCurrentIndex(2)
        condition_layout.addWidget(self.condition_input)
        details_layout.addLayout(condition_layout)
        
        # Category
        category_layout = QHBoxLayout()
        category_layout.addWidget(QLabel("Category:"))
        self.category_input = QLineEdit()
        self.category_input.setPlaceholderText("Enter category")
        category_layout.addWidget(self.category_input)
        details_layout.addLayout(category_layout)
        
        # Description
        details_layout.addWidget(QLabel("Description:"))
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Enter detailed item description")
        self.description_input.setMaximumHeight(150)
        details_layout.addWidget(self.description_input)
        
        details_group.setLayout(details_layout)
        right_panel.addWidget(details_group)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("Save Item")
        save_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px; font-size: 14px;")
        save_btn.clicked.connect(self.save_item)
        button_layout.addWidget(save_btn)
        
        clear_btn = QPushButton("Clear Form")
        clear_btn.clicked.connect(self.clear_form)
        button_layout.addWidget(clear_btn)
        
        right_panel.addLayout(button_layout)
        
        layout.addLayout(right_panel)
        
        return widget
    
    def create_inventory_tab(self):
        """Create the inventory overview tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Search and filter section
        search_layout = QHBoxLayout()
        
        search_layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by title, description, or category")
        self.search_input.textChanged.connect(self.search_inventory)
        search_layout.addWidget(self.search_input)
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_inventory_table)
        search_layout.addWidget(refresh_btn)
        
        layout.addLayout(search_layout)
        
        # Inventory table
        self.inventory_table = QTableWidget()
        self.inventory_table.setColumnCount(8)
        self.inventory_table.setHorizontalHeaderLabels([
            "ID", "Title", "Price", "Quantity", "Condition", "Category", "Created", "Actions"
        ])
        
        # Set column widths
        header = self.inventory_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Title column stretches
        self.inventory_table.setColumnWidth(0, 50)
        self.inventory_table.setColumnWidth(2, 80)
        self.inventory_table.setColumnWidth(3, 80)
        self.inventory_table.setColumnWidth(4, 120)
        self.inventory_table.setColumnWidth(5, 120)
        self.inventory_table.setColumnWidth(6, 150)
        self.inventory_table.setColumnWidth(7, 150)
        
        layout.addWidget(self.inventory_table)
        
        # Bottom action buttons
        button_layout = QHBoxLayout()
        
        export_btn = QPushButton("Export to CSV")
        export_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 8px;")
        export_btn.clicked.connect(self.export_inventory)
        button_layout.addWidget(export_btn)
        
        button_layout.addStretch()
        
        stats_label = QLabel()
        self.inventory_stats_label = stats_label
        button_layout.addWidget(stats_label)
        
        layout.addLayout(button_layout)
        
        return widget
    
    def create_search_tab(self):
        """Create the web search and research tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Search input section
        search_section = QGroupBox("Item Research")
        search_layout = QVBoxLayout()
        
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("Search Query:"))
        self.web_search_input = QLineEdit()
        self.web_search_input.setPlaceholderText("Enter item description for research")
        input_layout.addWidget(self.web_search_input)
        
        search_btn = QPushButton("Search")
        search_btn.setStyleSheet("background-color: #FF9800; color: white; padding: 8px;")
        search_btn.clicked.connect(self.perform_web_search)
        input_layout.addWidget(search_btn)
        
        search_layout.addLayout(input_layout)
        search_section.setLayout(search_layout)
        layout.addWidget(search_section)
        
        # Splitter for suggestions and results
        splitter = QSplitter(Qt.Horizontal)
        
        # Left: Search suggestions
        suggestions_group = QGroupBox("Search Suggestions")
        suggestions_layout = QVBoxLayout()
        
        self.suggestions_list = QListWidget()
        self.suggestions_list.itemClicked.connect(self.on_suggestion_clicked)
        suggestions_layout.addWidget(self.suggestions_list)
        
        suggestions_group.setLayout(suggestions_layout)
        splitter.addWidget(suggestions_group)
        
        # Right: Market research results
        results_group = QGroupBox("Market Research Results (Terapeak-style)")
        results_layout = QVBoxLayout()
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        results_layout.addWidget(self.results_text)
        
        results_group.setLayout(results_layout)
        splitter.addWidget(results_group)
        
        splitter.setSizes([400, 800])
        layout.addWidget(splitter)
        
        return widget
    
    def upload_photo(self):
        """Handle photo upload."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Image",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        
        if file_path:
            self.current_image_path = file_path
            self.display_image(file_path)
            self.statusBar().showMessage(f"Image loaded: {os.path.basename(file_path)}")
    
    def display_image(self, image_path):
        """Display image in the image label."""
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(
                self.image_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)
        else:
            self.image_label.setText("Failed to load image")
    
    def scan_barcode(self):
        """Handle barcode scanning."""
        # Simulated barcode scanning
        # In production, this would integrate with camera/scanner
        QMessageBox.information(
            self,
            "Barcode Scanner",
            "Barcode scanning would integrate with camera/scanner hardware.\n\n"
            "For this demonstration, please use manual entry or photo upload."
        )
    
    def clear_image(self):
        """Clear the loaded image."""
        self.current_image_path = ""
        self.image_label.clear()
        self.image_label.setText("No image loaded")
        self.statusBar().showMessage("Image cleared")
    
    def save_item(self):
        """Save or update inventory item."""
        # Get form values
        title = self.title_input.text().strip()
        price = self.price_input.value()
        quantity = self.quantity_input.value()
        condition = self.condition_input.currentText()
        category = self.category_input.text().strip()
        description = self.description_input.toPlainText().strip()
        
        # Validate
        is_valid, error_msg = validate_item_data(title, str(price), str(quantity))
        if not is_valid:
            QMessageBox.warning(self, "Validation Error", error_msg)
            return
        
        # Save to database
        try:
            if self.current_item_id:
                # Update existing item
                self.db.update_item(
                    self.current_item_id,
                    title, price, quantity, condition,
                    description, category, self.current_image_path
                )
                QMessageBox.information(self, "Success", "Item updated successfully!")
                self.current_item_id = None
            else:
                # Add new item
                item_id = self.db.add_item(
                    title, price, quantity, condition,
                    description, category, self.current_image_path
                )
                QMessageBox.information(self, "Success", f"Item added successfully! ID: {item_id}")
            
            # Clear form and refresh inventory
            self.clear_form()
            self.refresh_inventory_table()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save item: {str(e)}")
    
    def clear_form(self):
        """Clear the item input form."""
        self.title_input.clear()
        self.price_input.setValue(0.0)
        self.quantity_input.setValue(1)
        self.condition_input.setCurrentIndex(2)
        self.category_input.clear()
        self.description_input.clear()
        self.clear_image()
        self.current_item_id = None
    
    def refresh_inventory_table(self):
        """Refresh the inventory table with current data."""
        items = self.db.get_all_items()
        self.populate_table(items)
        
        # Update stats
        total_items = len(items)
        total_quantity = sum(item['quantity'] for item in items)
        total_value = sum(item['price'] * item['quantity'] for item in items)
        
        self.inventory_stats_label.setText(
            f"Total Items: {total_items} | Total Quantity: {total_quantity} | "
            f"Total Value: ${total_value:.2f}"
        )
    
    def populate_table(self, items):
        """Populate inventory table with items."""
        self.inventory_table.setRowCount(len(items))
        
        for row, item in enumerate(items):
            # ID
            self.inventory_table.setItem(row, 0, QTableWidgetItem(str(item['id'])))
            
            # Title
            self.inventory_table.setItem(row, 1, QTableWidgetItem(item['title']))
            
            # Price
            self.inventory_table.setItem(row, 2, QTableWidgetItem(format_price(item['price'])))
            
            # Quantity
            self.inventory_table.setItem(row, 3, QTableWidgetItem(str(item['quantity'])))
            
            # Condition
            self.inventory_table.setItem(row, 4, QTableWidgetItem(item.get('condition', '')))
            
            # Category
            self.inventory_table.setItem(row, 5, QTableWidgetItem(item.get('category', '')))
            
            # Created date
            created = item.get('created_at', '')
            if created:
                created = created.split('.')[0]  # Remove microseconds
            self.inventory_table.setItem(row, 6, QTableWidgetItem(created))
            
            # Action buttons
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(2, 2, 2, 2)
            
            edit_btn = QPushButton("Edit")
            edit_btn.clicked.connect(lambda checked, item_id=item['id']: self.edit_item(item_id))
            action_layout.addWidget(edit_btn)
            
            delete_btn = QPushButton("Delete")
            delete_btn.setStyleSheet("background-color: #f44336; color: white;")
            delete_btn.clicked.connect(lambda checked, item_id=item['id']: self.delete_item(item_id))
            action_layout.addWidget(delete_btn)
            
            self.inventory_table.setCellWidget(row, 7, action_widget)
    
    def search_inventory(self):
        """Search inventory based on search input."""
        search_term = self.search_input.text().strip()
        
        if search_term:
            items = self.db.search_items(search_term)
        else:
            items = self.db.get_all_items()
        
        self.populate_table(items)
    
    def edit_item(self, item_id):
        """Load item for editing."""
        item = self.db.get_item(item_id)
        
        if item:
            self.current_item_id = item_id
            
            # Populate form
            self.title_input.setText(item['title'])
            self.price_input.setValue(item['price'])
            self.quantity_input.setValue(item['quantity'])
            
            # Set condition
            condition_index = self.condition_input.findText(item.get('condition', ''))
            if condition_index >= 0:
                self.condition_input.setCurrentIndex(condition_index)
            
            self.category_input.setText(item.get('category', ''))
            self.description_input.setPlainText(item.get('description', ''))
            
            # Load image if exists
            if item.get('image_path') and os.path.exists(item['image_path']):
                self.current_image_path = item['image_path']
                self.display_image(item['image_path'])
            
            # Switch to item input tab
            self.findChild(QTabWidget).setCurrentIndex(0)
            
            self.statusBar().showMessage(f"Editing item ID: {item_id}")
    
    def delete_item(self, item_id):
        """Delete an inventory item."""
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this item?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.db.delete_item(item_id):
                QMessageBox.information(self, "Success", "Item deleted successfully!")
                self.refresh_inventory_table()
            else:
                QMessageBox.warning(self, "Error", "Failed to delete item.")
    
    def export_inventory(self):
        """Export inventory to CSV file."""
        items = self.db.get_all_items()
        
        if not items:
            QMessageBox.warning(self, "No Data", "No inventory items to export.")
            return
        
        # Ask for save location
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save CSV File",
            "inventory_export.csv",
            "CSV Files (*.csv)"
        )
        
        if file_path:
            try:
                export_to_csv(items, file_path)
                QMessageBox.information(
                    self,
                    "Export Success",
                    f"Inventory exported successfully to:\n{file_path}"
                )
                self.statusBar().showMessage(f"Exported to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export: {str(e)}")
    
    def perform_web_search(self):
        """Perform web search for item research."""
        query = self.web_search_input.text().strip()
        
        if not query:
            QMessageBox.warning(self, "Input Required", "Please enter a search query.")
            return
        
        # Generate suggestions
        suggestions = self.searcher.generate_search_suggestions(query)
        self.suggestions_list.clear()
        for suggestion in suggestions:
            self.suggestions_list.addItem(suggestion)
        
        # Get market research results
        results = self.searcher.simulate_terapeak_search(query)
        
        # Format and display results
        results_html = f"<h2>Market Research: {query}</h2>"
        results_html += "<hr>"
        
        for result in results:
            results_html += f"""
            <div style="margin-bottom: 20px; padding: 10px; background-color: #f9f9f9; border-left: 4px solid #2196F3;">
                <h3>{result['title_sample']}</h3>
                <p><strong>Condition:</strong> {result['condition']}</p>
                <p><strong>Average Price:</strong> ${result['avg_price']:.2f}</p>
                <p><strong>Price Range:</strong> ${result['price_range']['min']:.2f} - ${result['price_range']['max']:.2f}</p>
                <p><strong>Average Shipping:</strong> ${result['avg_shipping']:.2f}</p>
                <p><strong>Sell-Through Rate:</strong> {result['sell_through_rate']}%</p>
                <p><strong>Average Days to Sell:</strong> {result['avg_days_to_sell']} days</p>
                <p><strong>Total Listings:</strong> {result['total_listings']} | <strong>Total Sold:</strong> {result['total_sold']}</p>
            </div>
            """
        
        self.results_text.setHtml(results_html)
        self.statusBar().showMessage(f"Search completed for: {query}")
    
    def on_suggestion_clicked(self, item):
        """Handle click on search suggestion."""
        suggestion_text = item.text()
        self.web_search_input.setText(suggestion_text)
        self.perform_web_search()


def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Modern look
    
    window = InventoryManagementApp()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
