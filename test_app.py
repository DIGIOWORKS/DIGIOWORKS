"""
Test script to verify all components and add sample data.
"""

import os
import sys
import tempfile

def test_database():
    """Test database functionality."""
    print("Testing database module...")
    from database import InventoryDatabase
    
    # Clean up test database if exists
    if os.path.exists("test_inventory.db"):
        os.remove("test_inventory.db")
    
    db = InventoryDatabase("test_inventory.db")
    
    # Add sample items
    items_data = [
        ("iPhone 12 Pro", 599.99, 3, "Used - Like New", "Excellent condition, minimal wear", "Electronics", ""),
        ("Vintage Watch", 199.50, 1, "Used - Good", "Classic timepiece, working condition", "Collectibles", ""),
        ("Gaming Laptop", 899.00, 2, "Refurbished", "High-performance laptop with warranty", "Electronics", ""),
        ("Designer Handbag", 350.00, 1, "New", "Brand new with tags", "Fashion", ""),
        ("Camera Lens", 275.00, 2, "Used - Like New", "Canon 50mm f/1.8 lens", "Electronics", ""),
    ]
    
    for title, price, qty, condition, desc, category, img in items_data:
        item_id = db.add_item(title, price, qty, condition, desc, category, img)
        print(f"  Added: {title} (ID: {item_id})")
    
    # Test retrieval
    all_items = db.get_all_items()
    print(f"  Total items: {len(all_items)}")
    
    # Test search
    search_results = db.search_items("Electronics")
    print(f"  Electronics items: {len(search_results)}")
    
    # Test listing counter
    next_num = db.get_next_listing_number()
    print(f"  Next listing number: {next_num}")
    
    # Clean up
    os.remove("test_inventory.db")
    print("✓ Database tests passed!\n")
    
    return True


def test_web_search():
    """Test web search functionality."""
    print("Testing web search module...")
    from web_search import WebSearcher
    
    searcher = WebSearcher()
    
    # Test suggestions
    suggestions = searcher.generate_search_suggestions("iPhone")
    print(f"  Generated {len(suggestions)} suggestions")
    
    # Test market research
    results = searcher.simulate_terapeak_search("iPhone 12")
    print(f"  Market research: {len(results)} condition variants")
    
    # Test price recommendation
    rec = searcher.get_price_recommendation("Laptop", "Used - Good")
    print(f"  Price recommendation: ${rec['recommended_price']:.2f}")
    
    print("✓ Web search tests passed!\n")
    
    return True


def test_utils():
    """Test utility functions."""
    print("Testing utility functions...")
    from utils import export_to_csv, validate_item_data, format_price
    
    # Test validation
    valid, msg = validate_item_data("Test", "29.99", "5")
    assert valid, "Validation should pass"
    
    valid, msg = validate_item_data("", "29.99", "5")
    assert not valid, "Validation should fail for empty title"
    
    valid, msg = validate_item_data("Test", "invalid", "5")
    assert not valid, "Validation should fail for invalid price"
    
    # Test CSV export
    test_items = [
        {
            'title': 'test item',
            'price': 29.99,
            'quantity': 5,
            'condition': 'New',
            'description': 'Test description',
            'category': 'Test',
            'image_path': ''
        }
    ]
    
    csv_path = export_to_csv(test_items, os.path.join(tempfile.gettempdir(), "test_utils.csv"))
    assert os.path.exists(csv_path), "CSV file should be created"
    
    # Verify capitalization
    import csv
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        row = next(reader)
        assert row['Title'] == 'TEST ITEM', "Title should be capitalized"
    
    # Test format_price
    formatted = format_price(29.99)
    assert formatted == "$29.99", "Price should be formatted correctly"
    
    os.remove(csv_path)
    print("✓ Utility tests passed!\n")
    
    return True


def test_imports():
    """Test all module imports."""
    print("Testing module imports...")
    
    try:
        from PyQt5.QtWidgets import QApplication
        print("  ✓ PyQt5 imported")
        
        from database import InventoryDatabase
        print("  ✓ Database module imported")
        
        from web_search import WebSearcher
        print("  ✓ Web search module imported")
        
        from utils import export_to_csv
        print("  ✓ Utils module imported")
        
        import inventory_app
        print("  ✓ Main app module imported")
        
        print("✓ All imports successful!\n")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}\n")
        return False


def add_sample_data():
    """Add sample data to the main database."""
    print("Adding sample data to inventory...")
    from database import InventoryDatabase
    
    db = InventoryDatabase("inventory.db")
    
    # Clear existing data (optional)
    # This is just for demonstration
    
    sample_items = [
        ("Apple iPhone 13 Pro Max", 799.99, 5, "Used - Like New", 
         "128GB, Pacific Blue, includes original box and accessories", "Electronics", ""),
        ("Sony WH-1000XM4 Headphones", 249.50, 3, "New", 
         "Wireless noise-cancelling headphones, black color", "Electronics", ""),
        ("Vintage Rolex Watch", 3500.00, 1, "Used - Good", 
         "Classic Submariner, serviced and authenticated", "Collectibles", ""),
        ("Canon EOS R6 Camera", 1899.00, 2, "New", 
         "Full-frame mirrorless camera with 24-105mm lens", "Electronics", ""),
        ("Nike Air Jordan 1 Retro", 175.00, 4, "New", 
         "Size 10, Chicago colorway, deadstock", "Fashion", ""),
        ("Dell XPS 15 Laptop", 1299.00, 2, "Refurbished", 
         "i7-11800H, 16GB RAM, 512GB SSD, 6 months warranty", "Electronics", ""),
        ("Vintage Star Wars Figure", 89.99, 1, "Used - Good", 
         "Original 1978 Luke Skywalker, on card", "Collectibles", ""),
        ("KitchenAid Stand Mixer", 299.00, 3, "New", 
         "Professional 600 series, 6-quart bowl", "Home & Kitchen", ""),
        ("PlayStation 5", 499.99, 1, "New", 
         "Disc version with controller", "Electronics", ""),
        ("Ray-Ban Aviator Sunglasses", 149.00, 5, "New", 
         "Classic style, multiple lens options", "Fashion", ""),
    ]
    
    for title, price, qty, condition, desc, category, img in sample_items:
        item_id = db.add_item(title, price, qty, condition, desc, category, img)
        print(f"  Added: {title} (ID: {item_id})")
    
    total_items = len(db.get_all_items())
    print(f"\n✓ Sample data added! Total items in database: {total_items}\n")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Inventory Management System - Component Tests")
    print("=" * 60)
    print()
    
    all_passed = True
    
    # Run tests
    all_passed &= test_imports()
    all_passed &= test_database()
    all_passed &= test_web_search()
    all_passed &= test_utils()
    
    if all_passed:
        print("=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)
        print()
        
        # Ask if user wants sample data
        try:
            response = input("Add sample data to inventory? (y/n): ").lower()
            if response == 'y':
                add_sample_data()
        except:
            pass
        
        print("\nYou can now run the application with:")
        print("  python inventory_app.py")
        print()
        return 0
    else:
        print("=" * 60)
        print("Some tests failed! ✗")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
