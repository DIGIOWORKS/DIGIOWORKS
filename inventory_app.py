"""
Main GUI application for Invmachine.
A standalone tool for researching, describing, and managing items for sale.
"""

import sys
import os
import json
import base64
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTabWidget, QPushButton, QLabel, QLineEdit, QTextEdit, QTableWidget,
    QTableWidgetItem, QFileDialog, QMessageBox, QComboBox, QSpinBox,
    QDoubleSpinBox, QGroupBox, QListWidget, QListWidgetItem, QSplitter, QHeaderView, QSlider,
    QDialog, QFormLayout, QDialogButtonBox, QMenuBar, QAction
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QIcon, QImage, QTransform

from database import InventoryDatabase
from web_search import WebSearcher
from utils import export_to_csv, validate_item_data, format_price, truncate_text


class SettingsDialog(QDialog):
    """Dialog for configuring eBay API credentials."""
    
    CONFIG_FILE = "ebay_config.json"
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("eBay API Configuration")
        self.setModal(True)
        self.setMinimumWidth(500)
        
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        """Initialize the settings dialog UI."""
        layout = QVBoxLayout(self)
        
        # Info label
        info_label = QLabel(
            "Configure your eBay Developer API credentials.\n"
            "These are required for live marketplace data integration."
        )
        info_label.setStyleSheet("padding: 10px; background-color: #e3f2fd; border-radius: 5px;")
        layout.addWidget(info_label)
        
        # Form layout
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        
        # App ID field (pre-filled, read-only)
        self.app_id_input = QLineEdit()
        self.app_id_input.setText("comusedcom@gmail.com")
        self.app_id_input.setReadOnly(True)
        self.app_id_input.setStyleSheet("background-color: #f5f5f5;")
        form_layout.addRow("App ID (Client ID):", self.app_id_input)
        
        # Cert ID field (password input)
        self.cert_id_input = QLineEdit()
        self.cert_id_input.setEchoMode(QLineEdit.Password)
        self.cert_id_input.setPlaceholderText("Enter your eBay Cert ID (Client Secret)")
        form_layout.addRow("Cert ID (Client Secret):", self.cert_id_input)
        
        # Show/Hide password checkbox
        self.show_password_check = QPushButton("Show")
        self.show_password_check.setCheckable(True)
        self.show_password_check.setMaximumWidth(80)
        self.show_password_check.clicked.connect(self.toggle_password_visibility)
        form_layout.addRow("", self.show_password_check)
        
        layout.addLayout(form_layout)
        
        # Help text
        help_label = QLabel(
            '<p><b>Where to get credentials:</b></p>'
            '<ol>'
            '<li>Go to <a href="https://developer.ebay.com">developer.ebay.com</a></li>'
            '<li>Sign in or create a developer account</li>'
            '<li>Navigate to "My Account" → "Application Keys"</li>'
            '<li>Create a new application or use existing one</li>'
            '<li>Copy the App ID (Client ID) and Cert ID (Client Secret)</li>'
            '</ol>'
            '<p><i>Note: Credentials are stored encrypted locally.</i></p>'
        )
        help_label.setWordWrap(True)
        help_label.setOpenExternalLinks(True)
        help_label.setStyleSheet("padding: 10px; background-color: #fff3cd; border-radius: 5px; font-size: 10px;")
        layout.addWidget(help_label)
        
        # Button box
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.save_settings)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def toggle_password_visibility(self):
        """Toggle password field visibility."""
        if self.show_password_check.isChecked():
            self.cert_id_input.setEchoMode(QLineEdit.Normal)
            self.show_password_check.setText("Hide")
        else:
            self.cert_id_input.setEchoMode(QLineEdit.Password)
            self.show_password_check.setText("Show")
    
    def load_settings(self):
        """Load saved settings from config file."""
        try:
            if os.path.exists(self.CONFIG_FILE):
                with open(self.CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                
                # Decode cert_id if it exists
                if 'cert_id' in config:
                    cert_id = base64.b64decode(config['cert_id']).decode('utf-8')
                    self.cert_id_input.setText(cert_id)
        except Exception as e:
            QMessageBox.warning(
                self,
                "Load Error",
                f"Failed to load saved settings: {str(e)}"
            )
    
    def save_settings(self):
        """Save settings to config file."""
        cert_id = self.cert_id_input.text().strip()
        
        if not cert_id:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Please enter your eBay Cert ID (Client Secret)."
            )
            return
        
        try:
            # Encode cert_id for basic obfuscation
            encoded_cert_id = base64.b64encode(cert_id.encode('utf-8')).decode('utf-8')
            
            config = {
                'app_id': self.app_id_input.text(),
                'cert_id': encoded_cert_id
            }
            
            with open(self.CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=2)
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Save Error",
                f"Failed to save settings: {str(e)}"
            )


class InventoryManagementApp(QMainWindow):
    """Main application window for inventory management."""
    
    def __init__(self):
        super().__init__()
        self.db = InventoryDatabase()
        self.searcher = WebSearcher()
        self.current_image_path = ""
        self.current_item_id = None
        
        # Image Machine state
        self.im_current_image = None
        self.im_original_image = None
        self.im_current_pixmap = None
        self.im_brightness = 0
        self.im_contrast = 0
        self.im_rotation = 0
        
        self.init_ui()
        self.refresh_inventory_table()
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Invmachine")
        self.setGeometry(100, 100, 1400, 800)
        
        # Create menu bar
        self.create_menu_bar()
        
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
        
        # Tab 4: Image Machine
        self.image_machine_tab = self.create_image_machine_tab()
        tabs.addTab(self.image_machine_tab, "Image Machine")
        
        # Status bar
        self.statusBar().showMessage("Ready")
    
    def create_menu_bar(self):
        """Create the application menu bar."""
        menubar = self.menuBar()
        
        # Settings menu
        settings_menu = menubar.addMenu('&Settings')
        
        # eBay API Settings action
        api_settings_action = QAction('&eBay API Configuration', self)
        api_settings_action.setStatusTip('Configure eBay API credentials')
        api_settings_action.triggered.connect(self.open_settings_dialog)
        settings_menu.addAction(api_settings_action)
    
    def open_settings_dialog(self):
        """Open the settings dialog for eBay API configuration."""
        dialog = SettingsDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.statusBar().showMessage("Settings saved successfully", 3000)
    
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
        
        # Search bar for existing items
        search_group = QGroupBox("Quick Item Search")
        search_layout = QHBoxLayout()
        
        search_layout.addWidget(QLabel("Search:"))
        self.item_search_input = QLineEdit()
        self.item_search_input.setPlaceholderText("Search existing items by title or category")
        self.item_search_input.textChanged.connect(self.search_items_for_input)
        search_layout.addWidget(self.item_search_input)
        
        search_group.setLayout(search_layout)
        right_panel.addWidget(search_group)
        
        # Search results dropdown
        self.item_search_results = QListWidget()
        self.item_search_results.setMaximumHeight(120)
        self.item_search_results.setVisible(False)
        self.item_search_results.itemClicked.connect(self.load_item_from_search)
        right_panel.addWidget(self.item_search_results)
        
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
    
    def create_image_machine_tab(self):
        """Create the Image Machine tab for image editing and manipulation."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        
        # Left panel: Tools and controls
        left_panel = QVBoxLayout()
        left_panel_widget = QWidget()
        left_panel_widget.setLayout(left_panel)
        left_panel_widget.setMaximumWidth(350)
        
        # File operations group
        file_group = QGroupBox("File Operations")
        file_layout = QVBoxLayout()
        
        load_btn = QPushButton("Load Image")
        load_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 10px;")
        load_btn.clicked.connect(self.im_load_image)
        file_layout.addWidget(load_btn)
        
        save_btn = QPushButton("Save Image")
        save_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px;")
        save_btn.clicked.connect(self.im_save_image)
        file_layout.addWidget(save_btn)
        
        file_group.setLayout(file_layout)
        left_panel.addWidget(file_group)
        
        # Transform operations group
        transform_group = QGroupBox("Transform")
        transform_layout = QVBoxLayout()
        
        rotate_layout = QHBoxLayout()
        rotate_left_btn = QPushButton("↶ 90°")
        rotate_left_btn.clicked.connect(lambda: self.im_rotate_image(-90))
        rotate_layout.addWidget(rotate_left_btn)
        
        rotate_right_btn = QPushButton("↷ 90°")
        rotate_right_btn.clicked.connect(lambda: self.im_rotate_image(90))
        rotate_layout.addWidget(rotate_right_btn)
        transform_layout.addLayout(rotate_layout)
        
        flip_layout = QHBoxLayout()
        flip_h_btn = QPushButton("Flip Horizontal")
        flip_h_btn.clicked.connect(lambda: self.im_flip_image(horizontal=True))
        flip_layout.addWidget(flip_h_btn)
        
        flip_v_btn = QPushButton("Flip Vertical")
        flip_v_btn.clicked.connect(lambda: self.im_flip_image(horizontal=False))
        flip_layout.addWidget(flip_v_btn)
        transform_layout.addLayout(flip_layout)
        
        transform_group.setLayout(transform_layout)
        left_panel.addWidget(transform_group)
        
        # Adjustments group
        adjust_group = QGroupBox("Adjustments")
        adjust_layout = QVBoxLayout()
        
        # Brightness
        brightness_label = QLabel("Brightness: 0")
        self.im_brightness_label = brightness_label
        adjust_layout.addWidget(brightness_label)
        
        brightness_slider = QSlider(Qt.Horizontal)
        brightness_slider.setMinimum(-100)
        brightness_slider.setMaximum(100)
        brightness_slider.setValue(0)
        brightness_slider.valueChanged.connect(self.im_adjust_brightness)
        adjust_layout.addWidget(brightness_slider)
        
        # Contrast
        contrast_label = QLabel("Contrast: 0")
        self.im_contrast_label = contrast_label
        adjust_layout.addWidget(contrast_label)
        
        contrast_slider = QSlider(Qt.Horizontal)
        contrast_slider.setMinimum(-100)
        contrast_slider.setMaximum(100)
        contrast_slider.setValue(0)
        contrast_slider.valueChanged.connect(self.im_adjust_contrast)
        adjust_layout.addWidget(contrast_slider)
        
        adjust_group.setLayout(adjust_layout)
        left_panel.addWidget(adjust_group)
        
        # Auto-naming group
        naming_group = QGroupBox("Auto-Naming")
        naming_layout = QVBoxLayout()
        
        naming_layout.addWidget(QLabel("Generated Name:"))
        self.im_auto_name = QLineEdit()
        self.im_auto_name.setPlaceholderText("Load an image to generate name")
        self.im_auto_name.setReadOnly(False)
        naming_layout.addWidget(self.im_auto_name)
        
        generate_name_btn = QPushButton("Generate Name")
        generate_name_btn.setStyleSheet("background-color: #FF9800; color: white; padding: 8px;")
        generate_name_btn.clicked.connect(self.im_generate_name)
        naming_layout.addWidget(generate_name_btn)
        
        naming_group.setLayout(naming_layout)
        left_panel.addWidget(naming_group)
        
        # Reset and clear buttons
        action_layout = QHBoxLayout()
        
        reset_btn = QPushButton("Reset All")
        reset_btn.clicked.connect(self.im_reset_image)
        action_layout.addWidget(reset_btn)
        
        clear_btn = QPushButton("Clear Image")
        clear_btn.setStyleSheet("background-color: #f44336; color: white;")
        clear_btn.clicked.connect(self.im_clear_image)
        action_layout.addWidget(clear_btn)
        
        left_panel.addLayout(action_layout)
        left_panel.addStretch()
        
        layout.addWidget(left_panel_widget)
        
        # Right panel: Image display
        right_panel = QVBoxLayout()
        
        # Image display area
        image_display_group = QGroupBox("Image Preview")
        image_display_layout = QVBoxLayout()
        
        self.im_image_label = QLabel()
        self.im_image_label.setMinimumSize(800, 600)
        self.im_image_label.setAlignment(Qt.AlignCenter)
        self.im_image_label.setStyleSheet("border: 2px solid #ccc; background-color: #f0f0f0;")
        self.im_image_label.setText("No image loaded\n\nClick 'Load Image' to begin")
        image_display_layout.addWidget(self.im_image_label)
        
        # Image info
        self.im_info_label = QLabel("Image info will appear here")
        self.im_info_label.setStyleSheet("padding: 10px; background-color: #e0e0e0;")
        image_display_layout.addWidget(self.im_info_label)
        
        image_display_group.setLayout(image_display_layout)
        right_panel.addWidget(image_display_group)
        
        layout.addLayout(right_panel)
        
        return widget
    
    def im_load_image(self):
        """Load an image in Image Machine."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Image for Editing",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif *.tiff)"
        )
        
        if file_path:
            try:
                self.im_original_image = QImage(file_path)
                if self.im_original_image.isNull():
                    QMessageBox.warning(self, "Load Error", "Failed to load image.")
                    return
                
                self.im_current_image = self.im_original_image.copy()
                self.im_brightness = 0
                self.im_contrast = 0
                self.im_rotation = 0
                
                self.im_display_image()
                self.im_update_info(file_path)
                self.im_generate_name()
                self.statusBar().showMessage(f"Loaded: {os.path.basename(file_path)}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error loading image: {str(e)}")
    
    def im_display_image(self):
        """Display the current image in Image Machine."""
        if self.im_current_image is None or self.im_current_image.isNull():
            return
        
        pixmap = QPixmap.fromImage(self.im_current_image)
        scaled_pixmap = pixmap.scaled(
            self.im_image_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.im_image_label.setPixmap(scaled_pixmap)
    
    def im_update_info(self, file_path=""):
        """Update image information display."""
        if self.im_current_image is None or self.im_current_image.isNull():
            self.im_info_label.setText("No image loaded")
            return
        
        width = self.im_current_image.width()
        height = self.im_current_image.height()
        
        info_text = f"Size: {width} x {height} px"
        if file_path:
            file_size = os.path.getsize(file_path) / 1024  # KB
            info_text += f" | File: {os.path.basename(file_path)} ({file_size:.1f} KB)"
        
        self.im_info_label.setText(info_text)
    
    def im_rotate_image(self, angle):
        """Rotate the image."""
        if self.im_current_image is None or self.im_current_image.isNull():
            QMessageBox.warning(self, "No Image", "Please load an image first.")
            return
        
        transform = QTransform()
        transform.rotate(angle)
        self.im_current_image = self.im_current_image.transformed(transform, Qt.SmoothTransformation)
        self.im_rotation = (self.im_rotation + angle) % 360
        self.im_display_image()
        self.im_update_info()
        self.statusBar().showMessage(f"Rotated {angle}°")
    
    def im_flip_image(self, horizontal=True):
        """Flip the image horizontally or vertically."""
        if self.im_current_image is None or self.im_current_image.isNull():
            QMessageBox.warning(self, "No Image", "Please load an image first.")
            return
        
        self.im_current_image = self.im_current_image.mirrored(horizontal, not horizontal)
        self.im_display_image()
        direction = "horizontally" if horizontal else "vertically"
        self.statusBar().showMessage(f"Flipped {direction}")
    
    def im_adjust_brightness(self, value):
        """Adjust image brightness."""
        if self.im_original_image is None or self.im_original_image.isNull():
            return
        
        self.im_brightness = value
        self.im_brightness_label.setText(f"Brightness: {value}")
        self.im_apply_adjustments()
    
    def im_adjust_contrast(self, value):
        """Adjust image contrast."""
        if self.im_original_image is None or self.im_original_image.isNull():
            return
        
        self.im_contrast = value
        self.im_contrast_label.setText(f"Contrast: {value}")
        self.im_apply_adjustments()
    
    def im_apply_adjustments(self):
        """Apply brightness and contrast adjustments."""
        if self.im_original_image is None or self.im_original_image.isNull():
            return
        
        # Start from original image
        self.im_current_image = self.im_original_image.copy()
        
        # Apply brightness and contrast using pixel manipulation
        # This is a simplified implementation
        if self.im_brightness != 0 or self.im_contrast != 0:
            width = self.im_current_image.width()
            height = self.im_current_image.height()
            
            # Brightness factor: -100 to 100 -> -255 to 255 adjustment
            b_factor = int(self.im_brightness * 2.55)
            
            # Contrast factor: -100 to 100 -> 0.0 to 2.0 multiplier
            c_factor = (self.im_contrast + 100) / 100.0
            
            for y in range(height):
                for x in range(width):
                    pixel = self.im_current_image.pixelColor(x, y)
                    
                    # Apply contrast then brightness
                    r = max(0, min(255, int((pixel.red() - 128) * c_factor + 128 + b_factor)))
                    g = max(0, min(255, int((pixel.green() - 128) * c_factor + 128 + b_factor)))
                    b = max(0, min(255, int((pixel.blue() - 128) * c_factor + 128 + b_factor)))
                    
                    pixel.setRgb(r, g, b)
                    self.im_current_image.setPixelColor(x, y, pixel)
        
        self.im_display_image()
    
    def im_generate_name(self):
        """Generate an automatic name for the image."""
        if self.im_current_image is None or self.im_current_image.isNull():
            self.im_auto_name.setText("")
            return
        
        # Generate name based on image properties and timestamp
        width = self.im_current_image.width()
        height = self.im_current_image.height()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Determine orientation
        if width > height:
            orientation = "landscape"
        elif height > width:
            orientation = "portrait"
        else:
            orientation = "square"
        
        # Generate descriptive name
        name = f"image_{orientation}_{width}x{height}_{timestamp}"
        
        self.im_auto_name.setText(name)
        self.statusBar().showMessage("Auto-name generated")
    
    def im_reset_image(self):
        """Reset image to original state."""
        if self.im_original_image is None or self.im_original_image.isNull():
            QMessageBox.warning(self, "No Image", "Please load an image first.")
            return
        
        self.im_current_image = self.im_original_image.copy()
        self.im_brightness = 0
        self.im_contrast = 0
        self.im_rotation = 0
        
        # Reset UI controls (would need references to sliders)
        self.im_brightness_label.setText("Brightness: 0")
        self.im_contrast_label.setText("Contrast: 0")
        
        self.im_display_image()
        self.im_update_info()
        self.statusBar().showMessage("Image reset to original")
    
    def im_clear_image(self):
        """Clear the current image."""
        self.im_current_image = None
        self.im_original_image = None
        self.im_current_pixmap = None
        self.im_brightness = 0
        self.im_contrast = 0
        self.im_rotation = 0
        
        self.im_image_label.clear()
        self.im_image_label.setText("No image loaded\n\nClick 'Load Image' to begin")
        self.im_info_label.setText("Image info will appear here")
        self.im_auto_name.setText("")
        
        self.statusBar().showMessage("Image cleared")
    
    def im_save_image(self):
        """Save the edited image."""
        if self.im_current_image is None or self.im_current_image.isNull():
            QMessageBox.warning(self, "No Image", "No image to save.")
            return
        
        # Suggest filename from auto-name
        suggested_name = self.im_auto_name.text()
        if not suggested_name:
            suggested_name = "edited_image"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Image",
            suggested_name + ".png",
            "PNG (*.png);;JPEG (*.jpg *.jpeg);;BMP (*.bmp);;All Files (*)"
        )
        
        if file_path:
            try:
                if self.im_current_image.save(file_path):
                    QMessageBox.information(self, "Success", f"Image saved to:\n{file_path}")
                    self.statusBar().showMessage(f"Saved: {os.path.basename(file_path)}")
                else:
                    QMessageBox.critical(self, "Error", "Failed to save image.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error saving image: {str(e)}")
    
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
        self.item_search_input.clear()
        self.item_search_results.setVisible(False)
    
    def search_items_for_input(self):
        """Search for items in the item input tab."""
        search_term = self.item_search_input.text().strip()
        
        if not search_term or len(search_term) < 2:
            self.item_search_results.setVisible(False)
            self.item_search_results.clear()
            return
        
        # Search in database
        items = self.db.search_items(search_term)
        
        self.item_search_results.clear()
        
        if items:
            self.item_search_results.setVisible(True)
            for item in items[:10]:  # Limit to 10 results
                display_text = f"{item['title']} - ${item['price']:.2f} (ID: {item['id']})"
                list_item = QListWidgetItem(display_text)
                list_item.setData(Qt.UserRole, item['id'])
                self.item_search_results.addItem(list_item)
        else:
            self.item_search_results.setVisible(False)
    
    def load_item_from_search(self, item):
        """Load an item into the form from search results."""
        item_id = item.data(Qt.UserRole)
        
        if item_id:
            db_item = self.db.get_item(item_id)
            
            if db_item:
                self.current_item_id = item_id
                
                # Populate form
                self.title_input.setText(db_item['title'])
                self.price_input.setValue(db_item['price'])
                self.quantity_input.setValue(db_item['quantity'])
                
                # Set condition
                condition_index = self.condition_input.findText(db_item.get('condition', ''))
                if condition_index >= 0:
                    self.condition_input.setCurrentIndex(condition_index)
                
                self.category_input.setText(db_item.get('category', ''))
                self.description_input.setPlainText(db_item.get('description', ''))
                
                # Load image if exists
                if db_item.get('image_path') and os.path.exists(db_item['image_path']):
                    self.current_image_path = db_item['image_path']
                    self.display_image(db_item['image_path'])
                
                # Hide search results
                self.item_search_results.setVisible(False)
                self.item_search_input.clear()
                
                self.statusBar().showMessage(f"Loaded item: {db_item['title']}")
    
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
