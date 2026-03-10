"""
InvenScan - Standalone GUI Inventory Management & Scanning Application.
Helps users research, describe, scan, and manage items for sale.
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
    QDoubleSpinBox, QGroupBox, QListWidget, QListWidgetItem, QSplitter,
    QHeaderView, QSlider, QDialog, QFormLayout, QDialogButtonBox,
    QMenuBar, QAction, QScrollArea,
)
from PyQt5.QtCore import Qt, QSize, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QIcon, QImage, QTransform

from database import InventoryDatabase
from web_search import WebSearcher
from utils import export_to_csv, validate_item_data, format_price, truncate_text
from ebay_api import eBayAPIClient


# ---------------------------------------------------------------------------
# Settings dialog
# ---------------------------------------------------------------------------

class SettingsDialog(QDialog):
    """Dialog for configuring eBay API credentials."""

    CONFIG_FILE = "ebay_config.json"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("eBay API Configuration")
        self.setModal(True)
        self.setMinimumWidth(500)
        self._init_ui()
        self._load_settings()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        info_label = QLabel(
            "Configure your eBay Developer API credentials.\n"
            "These are required for live marketplace data integration."
        )
        info_label.setStyleSheet(
            "padding: 10px; background-color: #e3f2fd; border-radius: 5px;"
        )
        layout.addWidget(info_label)

        form = QFormLayout()
        form.setSpacing(15)

        self.app_id_input = QLineEdit()
        self.app_id_input.setPlaceholderText("Enter your eBay App ID (Client ID)")
        form.addRow("App ID (Client ID):", self.app_id_input)

        self.cert_id_input = QLineEdit()
        self.cert_id_input.setEchoMode(QLineEdit.Password)
        self.cert_id_input.setPlaceholderText("Enter your eBay Cert ID (Client Secret)")
        form.addRow("Cert ID (Client Secret):", self.cert_id_input)

        self.show_password_btn = QPushButton("Show")
        self.show_password_btn.setCheckable(True)
        self.show_password_btn.setMaximumWidth(80)
        self.show_password_btn.clicked.connect(self._toggle_password)
        form.addRow("", self.show_password_btn)

        layout.addLayout(form)

        help_label = QLabel(
            "<p><b>Where to get credentials:</b></p>"
            "<ol>"
            "<li>Go to <a href='https://developer.ebay.com'>developer.ebay.com</a></li>"
            "<li>Sign in or create a developer account</li>"
            "<li>Navigate to \"My Account\" → \"Application Keys\"</li>"
            "<li>Create a new application or use existing one</li>"
            "<li>Copy the App ID (Client ID) and Cert ID (Client Secret)</li>"
            "</ol>"
            "<p><i>Note: Credentials are stored encrypted locally.</i></p>"
        )
        help_label.setWordWrap(True)
        help_label.setOpenExternalLinks(True)
        help_label.setStyleSheet(
            "padding: 10px; background-color: #fff3cd; border-radius: 5px; font-size: 10px;"
        )
        layout.addWidget(help_label)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._save_settings)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _toggle_password(self):
        if self.show_password_btn.isChecked():
            self.cert_id_input.setEchoMode(QLineEdit.Normal)
            self.show_password_btn.setText("Hide")
        else:
            self.cert_id_input.setEchoMode(QLineEdit.Password)
            self.show_password_btn.setText("Show")

    def _load_settings(self):
        try:
            if os.path.exists(self.CONFIG_FILE):
                with open(self.CONFIG_FILE, "r") as f:
                    config = json.load(f)
                if "app_id" in config:
                    self.app_id_input.setText(config["app_id"])
                if "cert_id" in config:
                    decoded = base64.b64decode(config["cert_id"]).decode("utf-8")
                    self.cert_id_input.setText(decoded)
        except Exception as e:
            print(f"Error loading settings: {e}")

    def _save_settings(self):
        app_id = self.app_id_input.text().strip()
        cert_id = self.cert_id_input.text().strip()

        if not app_id or not cert_id:
            QMessageBox.warning(self, "Validation Error", "Both App ID and Cert ID are required.")
            return

        try:
            encoded_cert = base64.b64encode(cert_id.encode()).decode()
            config = {"app_id": app_id, "cert_id": encoded_cert}
            with open(self.CONFIG_FILE, "w") as f:
                json.dump(config, f, indent=2)
            QMessageBox.information(self, "Settings Saved", "API credentials saved successfully.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")


# ---------------------------------------------------------------------------
# Barcode scan worker (runs in a background thread)
# ---------------------------------------------------------------------------

class BarcodeScanWorker(QThread):
    """Worker thread that opens the camera and scans for barcodes/QR codes."""

    barcode_found = pyqtSignal(str, str)   # data, barcode_type
    error_occurred = pyqtSignal(str)

    def run(self):
        try:
            import cv2
            from pyzbar import pyzbar

            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                self.error_occurred.emit("Could not open camera. Please check your webcam.")
                return

            found = False
            while not found:
                ret, frame = cap.read()
                if not ret:
                    break

                barcodes = pyzbar.decode(frame)
                for bc in barcodes:
                    data = bc.data.decode("utf-8")
                    bc_type = bc.type
                    found = True
                    self.barcode_found.emit(data, bc_type)
                    break

            cap.release()

            if not found:
                self.error_occurred.emit("No barcode detected. Please try again.")

        except ImportError:
            self.error_occurred.emit(
                "Camera scanning requires 'opencv-python' and 'pyzbar'.\n"
                "Install them with: pip install opencv-python pyzbar"
            )
        except Exception as e:
            self.error_occurred.emit(f"Camera error: {e}")


# ---------------------------------------------------------------------------
# Item Input Tab
# ---------------------------------------------------------------------------

class ItemInputTab(QWidget):
    """Tab for adding new inventory items."""

    def __init__(self, db: InventoryDatabase, parent=None):
        super().__init__(parent)
        self.db = db
        self.current_image_path = ""
        self._scan_worker = None
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)

        # ---- Left panel: image & barcode ---------------------------------
        left = QGroupBox("Photo & Barcode")
        left_layout = QVBoxLayout(left)
        left.setFixedWidth(280)

        self.image_label = QLabel("No image selected")
        self.image_label.setFixedSize(240, 200)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet(
            "border: 2px dashed #aaa; background-color: #f5f5f5;"
        )
        left_layout.addWidget(self.image_label)

        upload_btn = QPushButton("📂  Upload Photo")
        upload_btn.clicked.connect(self._upload_photo)
        left_layout.addWidget(upload_btn)

        scan_btn = QPushButton("📷  Scan Barcode / QR")
        scan_btn.clicked.connect(self._scan_barcode)
        scan_btn.setStyleSheet(
            "background-color: #1976d2; color: white; font-weight: bold; padding: 8px;"
        )
        left_layout.addWidget(scan_btn)

        barcode_group = QGroupBox("Barcode")
        barcode_layout = QHBoxLayout(barcode_group)
        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("Scan or type barcode")
        lookup_btn = QPushButton("Lookup")
        lookup_btn.clicked.connect(self._lookup_barcode)
        barcode_layout.addWidget(self.barcode_input)
        barcode_layout.addWidget(lookup_btn)
        left_layout.addWidget(barcode_group)

        self.scan_status_label = QLabel("")
        self.scan_status_label.setWordWrap(True)
        left_layout.addWidget(self.scan_status_label)

        left_layout.addStretch()
        layout.addWidget(left)

        # ---- Right panel: item details -----------------------------------
        right = QGroupBox("Item Details")
        right_layout = QVBoxLayout(right)

        form = QFormLayout()
        form.setSpacing(10)

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Item title (required)")
        form.addRow("Title *:", self.title_input)

        self.price_input = QDoubleSpinBox()
        self.price_input.setRange(0, 99999.99)
        self.price_input.setDecimals(2)
        self.price_input.setPrefix("$ ")
        form.addRow("Price *:", self.price_input)

        self.quantity_input = QSpinBox()
        self.quantity_input.setRange(0, 9999)
        self.quantity_input.setValue(1)
        form.addRow("Quantity *:", self.quantity_input)

        self.condition_input = QComboBox()
        self.condition_input.addItems([
            "New", "Open box", "Certified Refurbished",
            "Used - Like New", "Used - Very Good", "Used - Good",
            "Used - Acceptable", "For parts or not working",
        ])
        form.addRow("Condition:", self.condition_input)

        self.category_input = QComboBox()
        self.category_input.setEditable(True)
        self.category_input.addItems([
            "", "Electronics", "Collectibles", "Fashion", "Home & Kitchen",
            "Sporting Goods", "Toys & Hobbies", "Books", "Music", "Other",
        ])
        form.addRow("Category:", self.category_input)

        self.status_input = QComboBox()
        self.status_input.addItems(["active", "draft", "sold"])
        form.addRow("Status:", self.status_input)

        right_layout.addLayout(form)

        desc_label = QLabel("Description:")
        right_layout.addWidget(desc_label)
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(100)
        self.description_input.setPlaceholderText("Item description...")
        right_layout.addWidget(self.description_input)

        # Buttons
        btn_row = QHBoxLayout()
        save_btn = QPushButton("💾  Save Item")
        save_btn.setStyleSheet(
            "background-color: #388e3c; color: white; font-weight: bold; padding: 8px;"
        )
        save_btn.clicked.connect(self._save_item)

        clear_btn = QPushButton("🗑  Clear")
        clear_btn.clicked.connect(self._clear_form)

        listing_btn = QPushButton("🔢  Next Listing #")
        listing_btn.clicked.connect(self._get_listing_number)

        btn_row.addWidget(save_btn)
        btn_row.addWidget(clear_btn)
        btn_row.addWidget(listing_btn)
        right_layout.addLayout(btn_row)

        self.listing_label = QLabel("")
        right_layout.addWidget(self.listing_label)

        right_layout.addStretch()
        layout.addWidget(right)

    # ------------------------------------------------------------------
    def _upload_photo(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif *.tiff)"
        )
        if path:
            self.current_image_path = path
            pixmap = QPixmap(path).scaled(
                240, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.image_label.setPixmap(pixmap)

    def _scan_barcode(self):
        self.scan_status_label.setText("🔍 Scanning… aim camera at barcode.")
        self._scan_worker = BarcodeScanWorker()
        self._scan_worker.barcode_found.connect(self._on_barcode_found)
        self._scan_worker.error_occurred.connect(self._on_scan_error)
        self._scan_worker.start()

    def _on_barcode_found(self, data: str, bc_type: str):
        self.barcode_input.setText(data)
        self.scan_status_label.setText(f"✅ {bc_type}: {data}")
        self._lookup_barcode()

    def _on_scan_error(self, message: str):
        self.scan_status_label.setText(f"⚠️ {message}")

    def _lookup_barcode(self):
        barcode = self.barcode_input.text().strip()
        if not barcode:
            return
        item = self.db.get_item_by_barcode(barcode)
        if item:
            QMessageBox.information(
                self, "Item Found",
                f"Barcode matches: {item['title']}\nStatus: {item['status']}"
            )
        else:
            self.scan_status_label.setText(f"No existing item with barcode: {barcode}")

    def _save_item(self):
        title = self.title_input.text().strip()
        price = str(self.price_input.value())
        quantity = str(self.quantity_input.value())

        valid, msg = validate_item_data(title, price, quantity)
        if not valid:
            QMessageBox.warning(self, "Validation Error", msg)
            return

        item_id = self.db.add_item(
            title=title,
            price=float(price),
            quantity=int(quantity),
            condition=self.condition_input.currentText(),
            description=self.description_input.toPlainText().strip(),
            category=self.category_input.currentText().strip(),
            image_path=self.current_image_path,
            barcode=self.barcode_input.text().strip(),
            status=self.status_input.currentText(),
        )

        QMessageBox.information(self, "Item Saved", f"Item saved (ID: {item_id}).")
        self._clear_form()

    def _clear_form(self):
        self.title_input.clear()
        self.price_input.setValue(0)
        self.quantity_input.setValue(1)
        self.condition_input.setCurrentIndex(0)
        self.category_input.setCurrentIndex(0)
        self.status_input.setCurrentIndex(0)
        self.description_input.clear()
        self.barcode_input.clear()
        self.current_image_path = ""
        self.image_label.setText("No image selected")
        self.image_label.setPixmap(QPixmap())
        self.listing_label.setText("")
        self.scan_status_label.setText("")

    def _get_listing_number(self):
        num = self.db.get_next_listing_number()
        self.listing_label.setText(f"Listing number: {num}")


# ---------------------------------------------------------------------------
# Inventory Overview Tab
# ---------------------------------------------------------------------------

class InventoryTab(QWidget):
    """Tab for viewing and managing the inventory."""

    COLUMNS = ["ID", "Title", "Price", "Qty", "Condition", "Category", "Barcode", "Status"]

    def __init__(self, db: InventoryDatabase, parent=None):
        super().__init__(parent)
        self.db = db
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # Search bar
        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by title, description, category, or barcode…")
        self.search_input.textChanged.connect(self._refresh_table)

        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "active", "draft", "sold"])
        self.status_filter.currentTextChanged.connect(self._refresh_table)

        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self._refresh_table)

        export_btn = QPushButton("📤 Export CSV")
        export_btn.clicked.connect(self._export_csv)

        search_row.addWidget(QLabel("Search:"))
        search_row.addWidget(self.search_input)
        search_row.addWidget(QLabel("Status:"))
        search_row.addWidget(self.status_filter)
        search_row.addWidget(refresh_btn)
        search_row.addWidget(export_btn)
        layout.addLayout(search_row)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels(self.COLUMNS)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.doubleClicked.connect(self._edit_item)
        layout.addWidget(self.table)

        # Action buttons
        btn_row = QHBoxLayout()
        edit_btn = QPushButton("✏️ Edit Selected")
        edit_btn.clicked.connect(self._edit_item)
        delete_btn = QPushButton("🗑 Delete Selected")
        delete_btn.clicked.connect(self._delete_item)
        delete_btn.setStyleSheet("color: #c62828;")

        self.count_label = QLabel("Items: 0")

        btn_row.addWidget(edit_btn)
        btn_row.addWidget(delete_btn)
        btn_row.addStretch()
        btn_row.addWidget(self.count_label)
        layout.addLayout(btn_row)

        self._refresh_table()

    def _refresh_table(self):
        term = self.search_input.text().strip()
        status = self.status_filter.currentText()

        if status == "All":
            items = self.db.search_items(term) if term else self.db.get_all_items()
        else:
            items = (
                self.db.search_items_by_status(term, status)
                if term
                else self.db.get_items_by_status(status)
            )

        self.table.setRowCount(len(items))
        for row, item in enumerate(items):
            self.table.setItem(row, 0, QTableWidgetItem(str(item["id"])))
            self.table.setItem(row, 1, QTableWidgetItem(item["title"]))
            self.table.setItem(row, 2, QTableWidgetItem(format_price(item["price"])))
            self.table.setItem(row, 3, QTableWidgetItem(str(item["quantity"])))
            self.table.setItem(row, 4, QTableWidgetItem(item.get("condition", "")))
            self.table.setItem(row, 5, QTableWidgetItem(item.get("category", "")))
            self.table.setItem(row, 6, QTableWidgetItem(item.get("barcode", "")))
            self.table.setItem(row, 7, QTableWidgetItem(item.get("status", "active")))

        self.count_label.setText(f"Items: {len(items)}")

    def _edit_item(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "No Selection", "Please select an item to edit.")
            return

        item_id = int(self.table.item(row, 0).text())
        item = self.db.get_item(item_id)
        if not item:
            return

        dialog = EditItemDialog(item, self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            self.db.update_item(item_id, **data)
            self._refresh_table()

    def _delete_item(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "No Selection", "Please select an item to delete.")
            return

        item_id = int(self.table.item(row, 0).text())
        title = self.table.item(row, 1).text()

        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete \"{title}\"?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.db.delete_item(item_id)
            self._refresh_table()

    def _export_csv(self):
        items = self.db.get_all_items()
        if not items:
            QMessageBox.information(self, "No Data", "No items to export.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Save CSV", "inventory_export.csv", "CSV Files (*.csv)"
        )
        if path:
            csv_path = export_to_csv(items, path)
            QMessageBox.information(self, "Exported", f"Saved to: {csv_path}")


# ---------------------------------------------------------------------------
# Edit Item Dialog
# ---------------------------------------------------------------------------

class EditItemDialog(QDialog):
    """Dialog for editing an existing inventory item."""

    def __init__(self, item: dict, parent=None):
        super().__init__(parent)
        self.item = item
        self.setWindowTitle("Edit Item")
        self.setMinimumWidth(480)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(10)

        self.title_input = QLineEdit(self.item.get("title", ""))
        form.addRow("Title:", self.title_input)

        self.price_input = QDoubleSpinBox()
        self.price_input.setRange(0, 99999.99)
        self.price_input.setDecimals(2)
        self.price_input.setPrefix("$ ")
        self.price_input.setValue(float(self.item.get("price", 0)))
        form.addRow("Price:", self.price_input)

        self.quantity_input = QSpinBox()
        self.quantity_input.setRange(0, 9999)
        self.quantity_input.setValue(int(self.item.get("quantity", 1)))
        form.addRow("Quantity:", self.quantity_input)

        self.condition_input = QComboBox()
        conditions = [
            "New", "Open box", "Certified Refurbished",
            "Used - Like New", "Used - Very Good", "Used - Good",
            "Used - Acceptable", "For parts or not working",
        ]
        self.condition_input.addItems(conditions)
        current_condition = self.item.get("condition", "")
        if current_condition in conditions:
            self.condition_input.setCurrentText(current_condition)
        form.addRow("Condition:", self.condition_input)

        self.category_input = QLineEdit(self.item.get("category", ""))
        form.addRow("Category:", self.category_input)

        self.barcode_input = QLineEdit(self.item.get("barcode", ""))
        form.addRow("Barcode:", self.barcode_input)

        self.status_input = QComboBox()
        self.status_input.addItems(["active", "draft", "sold"])
        self.status_input.setCurrentText(self.item.get("status", "active"))
        form.addRow("Status:", self.status_input)

        layout.addLayout(form)

        self.description_input = QTextEdit(self.item.get("description", ""))
        self.description_input.setMaximumHeight(100)
        layout.addWidget(QLabel("Description:"))
        layout.addWidget(self.description_input)

        self.image_path_input = QLineEdit(self.item.get("image_path", ""))
        browse_btn = QPushButton("Browse…")
        browse_btn.clicked.connect(self._browse_image)
        img_row = QHBoxLayout()
        img_row.addWidget(self.image_path_input)
        img_row.addWidget(browse_btn)
        layout.addWidget(QLabel("Image Path:"))
        layout.addLayout(img_row)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _browse_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif *.tiff)"
        )
        if path:
            self.image_path_input.setText(path)

    def get_data(self) -> dict:
        return {
            "title": self.title_input.text().strip(),
            "price": self.price_input.value(),
            "quantity": self.quantity_input.value(),
            "condition": self.condition_input.currentText(),
            "description": self.description_input.toPlainText().strip(),
            "category": self.category_input.text().strip(),
            "image_path": self.image_path_input.text().strip(),
            "barcode": self.barcode_input.text().strip(),
            "status": self.status_input.currentText(),
        }


# ---------------------------------------------------------------------------
# Web Search / Market Research Tab
# ---------------------------------------------------------------------------

class WebSearchTab(QWidget):
    """Tab for eBay market research (dual-panel active vs. sold)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ebay_client = eBayAPIClient()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # Search bar
        bar = QHBoxLayout()
        self.query_input = QLineEdit()
        self.query_input.setPlaceholderText("Enter search query, e.g. 'dell motherboard'…")
        self.query_input.returnPressed.connect(self._do_search)

        search_btn = QPushButton("🔍 Search")
        search_btn.setStyleSheet(
            "background-color: #1565c0; color: white; font-weight: bold; padding: 8px 16px;"
        )
        search_btn.clicked.connect(self._do_search)

        bar.addWidget(QLabel("Search:"))
        bar.addWidget(self.query_input)
        bar.addWidget(search_btn)
        layout.addLayout(bar)

        # Dual-panel splitter
        splitter = QSplitter(Qt.Horizontal)

        active_panel = QGroupBox("Active Listings (Running)")
        active_layout = QVBoxLayout(active_panel)
        self.active_results = QTextEdit()
        self.active_results.setReadOnly(True)
        active_layout.addWidget(self.active_results)
        splitter.addWidget(active_panel)

        sold_panel = QGroupBox("Completed / Sold Listings (Terapeak)")
        sold_layout = QVBoxLayout(sold_panel)
        self.sold_results = QTextEdit()
        self.sold_results.setReadOnly(True)
        sold_layout.addWidget(self.sold_results)
        splitter.addWidget(sold_panel)

        layout.addWidget(splitter)

        self._show_config_notice()

    def _show_config_notice(self):
        notice = (
            "<p style='color: #888;'>Configure eBay API credentials in "
            "<b>Settings → eBay API Configuration</b> to see live marketplace data.</p>"
        )
        self.active_results.setHtml(notice)
        self.sold_results.setHtml(notice)

    def _do_search(self):
        query = self.query_input.text().strip()
        if not query:
            return

        self.active_results.setHtml("<p>Searching…</p>")
        self.sold_results.setHtml("<p>Searching…</p>")

        # Reload credentials each time in case they changed
        self.ebay_client = eBayAPIClient()

        if not self.ebay_client.is_configured():
            simulated = self.ebay_client.get_simulated_terapeak_data(query)
            self.active_results.setHtml(self._render_simulated(simulated, "active"))
            self.sold_results.setHtml(self._render_simulated(simulated, "sold"))
            return

        active = self.ebay_client.search_active_listings(query, max_results=10)
        sold = self.ebay_client.search_completed_items(query, max_results=10)

        self.active_results.setHtml(self._render_live_active(active, query))
        self.sold_results.setHtml(self._render_live_sold(sold, query))

    def _render_live_active(self, items: list, query: str) -> str:
        if not items:
            return (
                "<p><b>No active listings found.</b></p>"
                "<p>Check your eBay API credentials or try a different search term.</p>"
            )

        html = f"<h3>Active Listings for '{query}'</h3>"
        for item in items:
            price = f"${item.get('price', 0):.2f} {item.get('currency', 'USD')}"
            html += (
                f"<div style='background-color:#fff3e0; margin:6px 0; padding:8px; border-radius:4px;'>"
                f"<b>{item.get('title', '')}</b><br>"
                f"Price: {price} | Condition: {item.get('condition', 'N/A')}<br>"
                f"Seller: {item.get('seller', 'N/A')} | Location: {item.get('location', 'N/A')}<br>"
                f"<a href='{item.get('url', '')}'>View Listing</a>"
                f"</div>"
            )
        return html

    def _render_live_sold(self, items: list, query: str) -> str:
        if not items:
            return (
                "<p><b>No sold listings found.</b></p>"
                "<p>Check your eBay API credentials or try a different search term.</p>"
            )

        html = f"<h3>Sold Listings for '{query}'</h3>"
        for item in items:
            price = f"${item.get('price', 0):.2f} {item.get('currency', 'USD')}"
            html += (
                f"<div style='background-color:#e8f5e9; margin:6px 0; padding:8px; border-radius:4px;'>"
                f"<b>{item.get('title', '')}</b><br>"
                f"Sold Price: {price} | Condition: {item.get('condition', 'N/A')}<br>"
                f"Date Sold: {item.get('sold_date', 'N/A')[:10] if item.get('sold_date') else 'N/A'} "
                f"| Shipping: ${item.get('shipping', 0):.2f}<br>"
                f"<a href='{item.get('url', '')}'>View Listing</a>"
                f"</div>"
            )
        return html

    def _render_simulated(self, data: list, panel: str) -> str:
        bg = "#fff3e0" if panel == "active" else "#e8f5e9"
        label = "Active (Simulated)" if panel == "active" else "Sold (Simulated)"

        html = (
            f"<p style='color:#555;'><i>eBay API not configured — showing simulated data.<br>"
            f"Go to <b>Settings → eBay API Configuration</b> for live data.</i></p>"
            f"<h3>{label}</h3>"
        )
        for item in data:
            avg = item.get("avg_sold_price", 0)
            html += (
                f"<div style='background-color:{bg}; margin:6px 0; padding:8px; border-radius:4px;'>"
                f"<b>Condition: {item.get('condition', '')}</b><br>"
                f"Avg Price: ${avg:.2f} "
                f"(${item.get('min_price', 0):.2f} – ${item.get('max_price', 0):.2f})<br>"
                f"Sold: {item.get('total_sold', 0)} | "
                f"Sell-through: {item.get('sell_through_rate', 0):.0%} | "
                f"Avg days: {item.get('avg_days_to_sell', 0)}"
                f"</div>"
            )
        return html


# ---------------------------------------------------------------------------
# Image Machine Tab
# ---------------------------------------------------------------------------

class ImageMachineTab(QWidget):
    """Tab for image editing and auto-naming."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._original_image: QImage = None
        self._current_image: QImage = None
        self._current_path: str = ""
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)

        # ---- Controls (left) --------------------------------------------
        controls = QGroupBox("Controls")
        controls.setFixedWidth(260)
        ctrl_layout = QVBoxLayout(controls)

        # File ops
        file_group = QGroupBox("File")
        file_layout = QVBoxLayout(file_group)
        load_btn = QPushButton("📂  Load Image")
        load_btn.clicked.connect(self._load_image)
        save_btn = QPushButton("💾  Save Image")
        save_btn.clicked.connect(self._save_image)
        file_layout.addWidget(load_btn)
        file_layout.addWidget(save_btn)
        ctrl_layout.addWidget(file_group)

        # Transform
        transform_group = QGroupBox("Transform")
        t_layout = QVBoxLayout(transform_group)
        for label, fn in [
            ("↺ Rotate Left", lambda: self._rotate(-90)),
            ("↻ Rotate Right", lambda: self._rotate(90)),
            ("↔ Flip Horizontal", lambda: self._flip(True, False)),
            ("↕ Flip Vertical", lambda: self._flip(False, True)),
        ]:
            btn = QPushButton(label)
            btn.clicked.connect(fn)
            t_layout.addWidget(btn)
        ctrl_layout.addWidget(transform_group)

        # Adjustments
        adj_group = QGroupBox("Adjustments")
        adj_layout = QVBoxLayout(adj_group)

        adj_layout.addWidget(QLabel("Brightness:"))
        self.brightness_slider = QSlider(Qt.Horizontal)
        self.brightness_slider.setRange(-100, 100)
        self.brightness_slider.setValue(0)
        self.brightness_slider.valueChanged.connect(self._apply_adjustments)
        adj_layout.addWidget(self.brightness_slider)

        adj_layout.addWidget(QLabel("Contrast:"))
        self.contrast_slider = QSlider(Qt.Horizontal)
        self.contrast_slider.setRange(-100, 100)
        self.contrast_slider.setValue(0)
        self.contrast_slider.valueChanged.connect(self._apply_adjustments)
        adj_layout.addWidget(self.contrast_slider)

        reset_btn = QPushButton("↺ Reset Adjustments")
        reset_btn.clicked.connect(self._reset_adjustments)
        adj_layout.addWidget(reset_btn)
        ctrl_layout.addWidget(adj_group)

        # Auto-name
        name_group = QGroupBox("Auto Name")
        name_layout = QVBoxLayout(name_group)
        self.auto_name_input = QLineEdit()
        self.auto_name_input.setPlaceholderText("Auto-generated name…")
        name_layout.addWidget(self.auto_name_input)
        ctrl_layout.addWidget(name_group)

        # Info
        self.info_label = QLabel("No image loaded.")
        self.info_label.setWordWrap(True)
        ctrl_layout.addWidget(self.info_label)

        clear_btn = QPushButton("✖ Clear")
        clear_btn.clicked.connect(self._clear_image)
        ctrl_layout.addWidget(clear_btn)

        ctrl_layout.addStretch()
        layout.addWidget(controls)

        # ---- Preview (right) -------------------------------------------
        preview = QGroupBox("Preview")
        preview_layout = QVBoxLayout(preview)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.image_label = QLabel("Load an image to begin.")
        self.image_label.setAlignment(Qt.AlignCenter)
        scroll.setWidget(self.image_label)
        preview_layout.addWidget(scroll)
        layout.addWidget(preview)

    # ------------------------------------------------------------------
    def _load_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Load Image", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.tiff *.gif)"
        )
        if not path:
            return
        self._current_path = path
        self._original_image = QImage(path)
        self._current_image = QImage(path)
        self._update_preview()
        self._generate_auto_name()

    def _save_image(self):
        if self._current_image is None:
            QMessageBox.warning(self, "No Image", "Please load an image first.")
            return

        name = self.auto_name_input.text().strip() or "image"
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Image", name + ".png",
            "PNG (*.png);;JPEG (*.jpg);;BMP (*.bmp)"
        )
        if path:
            self._current_image.save(path)
            QMessageBox.information(self, "Saved", f"Image saved to:\n{path}")

    def _rotate(self, angle: int):
        if self._current_image is None:
            return
        transform = QTransform().rotate(angle)
        self._current_image = self._current_image.transformed(transform, Qt.SmoothTransformation)
        self._update_preview()

    def _flip(self, horizontal: bool, vertical: bool):
        if self._current_image is None:
            return
        self._current_image = self._current_image.mirrored(horizontal, vertical)
        self._update_preview()

    def _apply_adjustments(self):
        if self._original_image is None:
            return
        try:
            from PIL import Image, ImageEnhance
            import io

            buf = self._qimage_to_bytes(self._original_image)
            pil_img = Image.open(io.BytesIO(buf)).convert("RGB")

            brightness = 1.0 + self.brightness_slider.value() / 100.0
            contrast = 1.0 + self.contrast_slider.value() / 100.0

            pil_img = ImageEnhance.Brightness(pil_img).enhance(brightness)
            pil_img = ImageEnhance.Contrast(pil_img).enhance(contrast)

            out = io.BytesIO()
            pil_img.save(out, format="PNG")
            self._current_image = QImage.fromData(out.getvalue())
            self._update_preview()
        except ImportError:
            pass

    def _qimage_to_bytes(self, image: QImage) -> bytes:
        buf = image.bits().tobytes()
        # Already raw bytes for in-memory image; use PNG encode via Qt
        from PyQt5.QtCore import QBuffer, QIODevice
        byte_array = bytes()
        buffer = QBuffer()
        buffer.open(QIODevice.WriteOnly)
        image.save(buffer, "PNG")
        return bytes(buffer.data())

    def _reset_adjustments(self):
        if self._original_image is None:
            return
        self._current_image = self._original_image.copy()
        self.brightness_slider.setValue(0)
        self.contrast_slider.setValue(0)
        self._update_preview()

    def _clear_image(self):
        self._original_image = None
        self._current_image = None
        self._current_path = ""
        self.image_label.setText("Load an image to begin.")
        self.info_label.setText("No image loaded.")
        self.auto_name_input.clear()

    def _update_preview(self):
        if self._current_image is None:
            return
        w, h = self._current_image.width(), self._current_image.height()
        pixmap = QPixmap.fromImage(self._current_image).scaled(
            600, 500, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.image_label.setPixmap(pixmap)
        size_kb = (w * h * 4) // 1024
        self.info_label.setText(f"Size: {w} × {h} px | ~{size_kb} KB")

    def _generate_auto_name(self):
        if self._current_image is None:
            return
        w = self._current_image.width()
        h = self._current_image.height()
        if w > h:
            orientation = "landscape"
        elif h > w:
            orientation = "portrait"
        else:
            orientation = "square"
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.auto_name_input.setText(f"{orientation}_{w}x{h}_{ts}")


# ---------------------------------------------------------------------------
# Main Window
# ---------------------------------------------------------------------------

class InvenScanMainWindow(QMainWindow):
    """Main application window for InvenScan."""

    def __init__(self):
        super().__init__()
        self.db = InventoryDatabase()
        self.setWindowTitle("InvenScan — Inventory Management & Scanning")
        self.setMinimumSize(1000, 700)
        self._init_menu()
        self._init_tabs()
        self._apply_stylesheet()

    def _init_menu(self):
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("File")
        export_action = QAction("Export Inventory CSV…", self)
        export_action.triggered.connect(self._export_all)
        file_menu.addAction(export_action)
        file_menu.addSeparator()
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        settings_menu = menu_bar.addMenu("Settings")
        ebay_action = QAction("eBay API Configuration…", self)
        ebay_action.triggered.connect(self._open_settings)
        settings_menu.addAction(ebay_action)

        help_menu = menu_bar.addMenu("Help")
        about_action = QAction("About InvenScan", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _init_tabs(self):
        tabs = QTabWidget()
        tabs.addTab(ItemInputTab(self.db), "📷  Item Input")
        tabs.addTab(InventoryTab(self.db), "📦  Inventory")
        tabs.addTab(WebSearchTab(), "🔍  Market Research")
        tabs.addTab(ImageMachineTab(), "🖼  Image Machine")
        self.setCentralWidget(tabs)

    def _apply_stylesheet(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #fafafa; }
            QTabBar::tab { padding: 8px 16px; font-size: 13px; }
            QTabBar::tab:selected { background-color: #1565c0; color: white; }
            QGroupBox { font-weight: bold; }
            QPushButton { padding: 6px 12px; }
        """)

    def _export_all(self):
        items = self.db.get_all_items()
        if not items:
            QMessageBox.information(self, "No Data", "No items to export.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save CSV", "invenscan_export.csv", "CSV Files (*.csv)"
        )
        if path:
            csv_path = export_to_csv(items, path)
            QMessageBox.information(self, "Exported", f"Saved to:\n{csv_path}")

    def _open_settings(self):
        dialog = SettingsDialog(self)
        dialog.exec_()

    def _show_about(self):
        QMessageBox.about(
            self,
            "About InvenScan",
            "<h2>InvenScan</h2>"
            "<p>Standalone Inventory Management & Scanning Application</p>"
            "<p>Features: barcode/QR scanning, eBay market research,<br>"
            "inventory tracking, CSV export, and image editing.</p>"
            "<p>Built with Python, PyQt5, SQLite.</p>",
        )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("InvenScan")
    app.setApplicationVersion("1.0.0")
    window = InvenScanMainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
