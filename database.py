"""
Database module for inventory management.
Handles SQLite database operations for inventory items and listing numbers.
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple


class InventoryDatabase:
    """Manages inventory database operations."""
    
    def __init__(self, db_path: str = "inventory.db"):
        """Initialize database connection and create tables if needed."""
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self) -> sqlite3.Connection:
        """Create and return a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Create database tables if they don't exist."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Create inventory items table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                price REAL NOT NULL,
                quantity INTEGER NOT NULL,
                condition TEXT,
                description TEXT,
                category TEXT,
                image_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create listing number table for synchronization
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS listing_counter (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                next_listing_number INTEGER NOT NULL DEFAULT 1
            )
        """)
        
        # Initialize listing counter if not exists
        cursor.execute("INSERT OR IGNORE INTO listing_counter (id, next_listing_number) VALUES (1, 1)")
        
        conn.commit()
        conn.close()
    
    def add_item(self, title: str, price: float, quantity: int, condition: str = "",
                 description: str = "", category: str = "", image_path: str = "") -> int:
        """Add a new item to inventory."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO inventory (title, price, quantity, condition, description, category, image_path)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (title, price, quantity, condition, description, category, image_path))
        
        item_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return item_id
    
    def update_item(self, item_id: int, title: str, price: float, quantity: int,
                   condition: str = "", description: str = "", category: str = "",
                   image_path: str = "") -> bool:
        """Update an existing inventory item."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE inventory
            SET title = ?, price = ?, quantity = ?, condition = ?, 
                description = ?, category = ?, image_path = ?, 
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (title, price, quantity, condition, description, category, image_path, item_id))
        
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        return affected > 0
    
    def delete_item(self, item_id: int) -> bool:
        """Delete an inventory item."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM inventory WHERE id = ?", (item_id,))
        
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        return affected > 0
    
    def get_item(self, item_id: int) -> Optional[Dict]:
        """Get a single inventory item by ID."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM inventory WHERE id = ?", (item_id,))
        row = cursor.fetchone()
        
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def get_all_items(self) -> List[Dict]:
        """Get all inventory items."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM inventory ORDER BY created_at DESC")
        rows = cursor.fetchall()
        
        conn.close()
        
        return [dict(row) for row in rows]
    
    def search_items(self, search_term: str) -> List[Dict]:
        """Search inventory items by title, description, or category."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        search_pattern = f"%{search_term}%"
        cursor.execute("""
            SELECT * FROM inventory 
            WHERE title LIKE ? OR description LIKE ? OR category LIKE ?
            ORDER BY created_at DESC
        """, (search_pattern, search_pattern, search_pattern))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_next_listing_number(self) -> int:
        """Get the next listing number and increment it."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT next_listing_number FROM listing_counter WHERE id = 1")
        row = cursor.fetchone()
        next_num = row['next_listing_number']
        
        cursor.execute("UPDATE listing_counter SET next_listing_number = ? WHERE id = 1", 
                      (next_num + 1,))
        
        conn.commit()
        conn.close()
        
        return next_num
    
    def get_current_listing_number(self) -> int:
        """Get the current listing number without incrementing."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT next_listing_number FROM listing_counter WHERE id = 1")
        row = cursor.fetchone()
        
        conn.close()
        
        return row['next_listing_number']
