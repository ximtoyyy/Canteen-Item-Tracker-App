import json
import os
from typing import List, Dict, Union

# --- Configuration ---
DATA_FILE = "inventory.json"

# --- Data Structure ---
# Each item is a dictionary:
# {
#     "id": "1",
#     "name": "Bottled Water",
#     "quantity": 50,
#     "price": 15.00,
#     "threshold": 10
# }

# --- Persistence Functions ---

def load_items() -> List[Dict[str, Union[str, int, float]]]:
    """Loads inventory items from the JSON data file."""
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            # Ensure quantities, prices, and thresholds are numeric types
            for item in data:
                item['quantity'] = int(item.get('quantity', 0))
                item['price'] = float(item.get('price', 0.0))
                item['threshold'] = int(item.get('threshold', 1))
            return data
    except (IOError, json.JSONDecodeError):
        print(f"Warning: Could not read or parse {DATA_FILE}. Starting with empty inventory.")
        return []

def save_items(items: List[Dict[str, Union[str, int, float]]]):
    """Saves the current inventory items to the JSON data file."""
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(items, f, indent=4)
    except IOError:
        print(f"Error: Could not write data to {DATA_FILE}.")

def get_next_id(items: List) -> int:
    """Calculates the next unique ID based on existing items."""
    if not items:
        return 1
    # Find the maximum existing ID (converted to int) and add 1
    max_id = 0
    for item in items:
        try:
            max_id = max(max_id, int(item['id']))
        except ValueError:
            # Skip invalid IDs
            continue
    return max_id + 1

# --- Core Logic Functions ---

def display_items(items: List):
    """Displays the current inventory, highlighting low stock items and showing total value."""
    if not items:
        print("\n--- Inventory is Empty ---")
        return

    # Sort items: Low stock first, then by name
    items.sort(key=lambda x: (x['quantity'] <= x['threshold'], x['name']))

    print("\n" + "="*80)
    print("CANTEEN INVENTORY LIST".center(80))
    print("="*80)
    print(f"{'ID':<4} | {'Item Name':<30} | {'Quantity':<10} | {'Price (₱)':<12} | {'Threshold':<10} | {'Status':<8}")
    print("-" * 80)

    total_value = 0
    for item in items:
        is_low_stock = item['quantity'] <= item['threshold']
        status = "🚨 LOW" if is_low_stock else "OK"
        
        # Calculate individual item value and add to total
        total_value += item['quantity'] * item['price']

        # Format price with two decimal places
        price_str = f"₱{item['price']:.2f}"

        print(f"{item['id']:<4} | {item['name'][:30]:<30} | {item['quantity']:<10} | {price_str:<12} | {item['threshold']:<10} | {status:<8}")
    
    print("-" * 80)
    # Format total value with commas and two decimal places
    total_value_str = f"₱{total_value:,.2f}"
    print(f"Total Inventory Value: {total_value_str}")
    print("="*80 + "\n")


def add_item(items: List):
    """Prompts user for item details and adds a new item to the inventory."""
    print("\n--- Add New Item ---")
    name = input("Enter Item Name: ").strip()
    if not name:
        print("Item name cannot be empty.")
        return

    try:
        quantity = int(input("Enter Quantity in Stock (>= 0): "))
        price = float(input("Enter Unit Price (₱, >= 0.00): "))
        threshold = int(input("Enter Low Stock Threshold (>= 1): "))
    except ValueError:
        print("Invalid input for quantity, price, or threshold. Please use numbers.")
        return
    
    if quantity < 0 or price < 0 or threshold < 1:
        print("Invalid data: Quantity/Price must be >= 0, Threshold must be >= 1.")
        return

    new_id = str(get_next_id(items))
    new_item = {
        "id": new_id,
        "name": name,
        "quantity": quantity,
        "price": round(price, 2), # Round price to 2 decimal places
        "threshold": threshold,
    }
    
    items.append(new_item)
    save_items(items)
    print(f"Successfully added item: {name} (ID: {new_id})")


def update_quantity(items: List, change: int):
    """Prompts user for an item ID and updates its quantity by the specified change (+1 or -1)."""
    item_id = input("Enter ID of item to update: ").strip()
    try:
        item = next(item for item in items if item['id'] == item_id)
    except StopIteration:
        print(f"Error: Item with ID '{item_id}' not found.")
        return

    new_quantity = item['quantity'] + change
    if new_quantity < 0:
        print("Cannot decrement quantity below 0.")
        return

    item['quantity'] = new_quantity
    save_items(items)
    action = "Increased" if change > 0 else "Decreased"
    print(f"{action} quantity of {item['name']} to {new_quantity}.")


def edit_item(items: List):
    """Prompts user for an item ID and allows editing all its details."""
    item_id = input("Enter ID of item to edit: ").strip()
    try:
        item = next(item for item in items if item['id'] == item_id)
    except StopIteration:
        print(f"Error: Item with ID '{item_id}' not found.")
        return

    print(f"\n--- Editing Item: {item['name']} (ID: {item['id']}) ---")
    print("Enter new values (leave blank to keep current value).")

    new_name = input(f"New Name [{item['name']}]: ").strip() or item['name']
    
    # Use existing value as default in prompt
    new_quantity_str = input(f"New Quantity [{item['quantity']}]: ").strip()
    new_price_str = input(f"New Price (₱) [{item['price']:.2f}]: ").strip()
    new_threshold_str = input(f"New Threshold [{item['threshold']}]: ").strip()

    try:
        # Parse inputs, defaulting to current value if blank
        new_quantity = int(new_quantity_str) if new_quantity_str else item['quantity']
        new_price = float(new_price_str) if new_price_str else item['price']
        new_threshold = int(new_threshold_str) if new_threshold_str else item['threshold']
    except ValueError:
        print("Invalid number entered. Edit cancelled.")
        return

    if new_quantity < 0 or new_price < 0 or new_threshold < 1:
        print("Invalid data: Quantity/Price must be >= 0, Threshold must be >= 1. Edit cancelled.")
        return

    # Update item properties
    item['name'] = new_name
    item['quantity'] = new_quantity
    item['price'] = round(new_price, 2)
    item['threshold'] = new_threshold

    save_items(items)
    print(f"\nSuccessfully updated item: {item['name']}.")


def delete_item(items: List):
    """Prompts user for an item ID and deletes it after confirmation."""
    item_id = input("Enter ID of item to delete: ").strip()
    
    try:
        item_index = next(i for i, item in enumerate(items) if item['id'] == item_id)
    except StopIteration:
        print(f"Error: Item with ID '{item_id}' not found.")
        return
    
    item_name = items[item_index]['name']
    confirm = input(f"Are you sure you want to delete '{item_name}' (ID: {item_id})? (yes/no): ").lower().strip()
    
    if confirm == 'yes':
        del items[item_index]
        save_items(items)
        print(f"Item '{item_name}' deleted.")
    else:
        print("Deletion cancelled.")

# --- Main Application Loop ---

def main():
    """Main function to run the Canteen Tracker CLI."""
    items = load_items()
    
    while True:
        display_items(items)
        print("\n--- Menu ---")
        print("1. Add New Item")
        print("2. Increase Stock (+1)")
        print("3. Decrease Stock (-1)")
        print("4. Edit Item Details")
        print("5. Delete Item")
        print("6. Exit")
        
        choice = input("Enter your choice (1-6): ").strip()

        if choice == '1':
            add_item(items)
        elif choice == '2':
            update_quantity(items, 1)
        elif choice == '3':
            update_quantity(items, -1)
        elif choice == '4':
            edit_item(items)
        elif choice == '5':
            delete_item(items)
        elif choice == '6':
            print("Exiting Canteen Tracker. Goodbye!")
            break
        else:
            print("Invalid choice. Please enter a number between 1 and 6.")
        
        input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()
