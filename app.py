import streamlit as st
import json
import os
from typing import List, Dict, Union

# --- Configuration ---
DATA_FILE = "inventory.json"
ITEM_DTYPE = Dict[str, Union[str, int, float]]

# --- Persistence Functions (Adapted for Streamlit) ---

def load_items() -> List[ITEM_DTYPE]:
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
        st.error(f"Error loading {DATA_FILE}. Starting with empty inventory.")
        return []

def save_items(items: List[ITEM_DTYPE]):
    """Saves the current inventory items to the JSON data file."""
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(items, f, indent=4)
    except IOError:
        st.error(f"Error: Could not write data to {DATA_FILE}.")

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
            continue
    return max_id + 1

# --- State Management & Actions ---

def init_state():
    """Initializes session state variables."""
    if 'items' not in st.session_state:
        st.session_state.items = load_items()
    if 'next_id' not in st.session_state:
        st.session_state.next_id = get_next_id(st.session_state.items)
    if 'edit_id' not in st.session_state:
        st.session_state.edit_id = None
        
def update_inventory_and_save():
    """Saves the current session state items to the file."""
    save_items(st.session_state.items)

def add_item_action(name, quantity, price, threshold):
    """Adds a new item to the inventory."""
    new_item = {
        "id": str(st.session_state.next_id),
        "name": name,
        "quantity": quantity,
        "price": round(price, 2),
        "threshold": threshold,
    }
    st.session_state.items.append(new_item)
    st.session_state.next_id += 1
    update_inventory_and_save()
    st.success(f"Item '{name}' added successfully!")

def update_quantity_action(item_id: str, change: int):
    """Increases or decreases an item's quantity."""
    item_index = next((i for i, item in enumerate(st.session_state.items) if item['id'] == item_id), -1)
    
    if item_index != -1:
        item = st.session_state.items[item_index]
        new_quantity = item['quantity'] + change
        
        if new_quantity >= 0:
            item['quantity'] = new_quantity
            update_inventory_and_save()
        else:
            st.warning("Quantity cannot be negative.")

def set_edit_mode(item_id: str):
    """Sets the item ID for the edit form."""
    st.session_state.edit_id = item_id

def delete_item_action(item_id: str):
    """Deletes an item from the inventory."""
    st.session_state.items = [item for item in st.session_state.items if item['id'] != item_id]
    update_inventory_and_save()
    st.success("Item deleted.")

# --- UI Components ---

def render_add_item_form():
    """Renders the form for adding a new canteen item."""
    st.sidebar.header("Add New Item")
    with st.sidebar.form(key='add_form'):
        name = st.text_input("Item Name", key='new_name')
        quantity = st.number_input("Quantity in Stock", min_value=0, value=1, step=1, key='new_quantity')
        price = st.number_input("Unit Price (₱)", min_value=0.0, value=1.00, step=0.01, format="%.2f", key='new_price')
        threshold = st.number_input("Low Stock Threshold", min_value=1, value=5, step=1, key='new_threshold')
        
        submitted = st.form_submit_button("Add Item", type="primary")

        if submitted:
            if name:
                add_item_action(name, quantity, price, threshold)
            else:
                st.error("Item Name is required.")

def render_inventory_list():
    """Renders the main inventory table with controls."""
    items = st.session_state.items
    
    if not items:
        st.info("Inventory is empty. Add items using the form on the sidebar.")
        return

    # Sort items: Low stock first, then by name
    sorted_items = sorted(items, key=lambda x: (x['quantity'] <= x['threshold'], x['name']))

    st.subheader("Inventory List")

    # Create columns for the table header
    col_layout = [0.5, 2.5, 1, 1, 1, 2]
    cols = st.columns(col_layout)
    cols[0].write("**ID**")
    cols[1].write("**Item Name**")
    cols[2].write("**Quantity**")
    cols[3].write("**Price (₱)**")
    cols[4].write("**Threshold**")
    cols[5].write("**Actions**")
    st.markdown("---") # Separator line

    # Render items row by row
    for item in sorted_items:
        is_low_stock = item['quantity'] <= item['threshold']
        
        cols = st.columns(col_layout)
        
        # ID, Name, Quantity
        cols[0].write(item['id'])
        cols[1].markdown(f"**{'🚨' if is_low_stock else ''} {item['name']}**")
        cols[2].markdown(f"**{item['quantity']}**")
        
        # Price, Threshold
        cols[3].write(f"₱{item['price']:.2f}")
        cols[4].write(item['threshold'])

        # Action Buttons
        with cols[5]:
            # Use a container for better horizontal layout of small buttons
            btn_cols = st.columns([1, 1, 1.5, 1.5])
            
            # Decrement button
            btn_cols[0].button("–", key=f"dec_{item['id']}", 
                               on_click=update_quantity_action, args=(item['id'], -1), 
                               disabled=(item['quantity'] == 0), help="Decrement stock by 1")
            
            # Increment button
            btn_cols[1].button("+", key=f"inc_{item['id']}", 
                               on_click=update_quantity_action, args=(item['id'], 1), 
                               type="primary", help="Increment stock by 1")

            # Edit button
            btn_cols[2].button("Edit", key=f"edit_{item['id']}", 
                               on_click=set_edit_mode, args=(item['id'],), 
                               help="Edit item details", use_container_width=True)
            
            # Delete button
            btn_cols[3].button("Del", key=f"del_{item['id']}", 
                               on_click=delete_item_action, args=(item['id'],), 
                               help="Delete item permanently", type="secondary", use_container_width=True)

def render_inventory_summary():
    """Calculates and displays the total inventory value."""
    total_value = sum(item['quantity'] * item['price'] for item in st.session_state.items)
    total_items = len(st.session_state.items)
    low_stock_count = sum(1 for item in st.session_state.items if item['quantity'] <= item['threshold'])

    col1, col2, col3 = st.columns(3)
    
    col1.metric(
        label="Total Inventory Value", 
        value=f"₱{total_value:,.2f}", 
        delta="Calculated based on current stock"
    )
    col2.metric(
        label="Total Unique Items",
        value=total_items,
    )
    col3.metric(
        label="Low Stock Alerts",
        value=low_stock_count,
        delta_color="inverse"
    )
    
    st.markdown("---")

def render_edit_form():
    """Renders the edit form if an item is selected for editing."""
    item_id = st.session_state.edit_id
    if item_id is None:
        return
    
    try:
        item_to_edit = next(item for item in st.session_state.items if item['id'] == item_id)
    except StopIteration:
        st.session_state.edit_id = None # Item not found, reset state
        return

    st.header(f"✏️ Edit Item: {item_to_edit['name']}")
    
    # Use a container for the edit form
    with st.container(border=True):
        with st.form(key='edit_form', clear_on_submit=False):
            st.markdown(f"Editing Item ID: `{item_id}`")
            
            # Pre-populate fields with current values
            new_name = st.text_input("Item Name", value=item_to_edit['name'], key='edit_name')
            
            col_q, col_p, col_t = st.columns(3)
            new_quantity = col_q.number_input("Quantity", min_value=0, value=item_to_edit['quantity'], step=1, key='edit_quantity')
            new_price = col_p.number_input("Unit Price (₱)", min_value=0.0, value=item_to_edit['price'], step=0.01, format="%.2f", key='edit_price')
            new_threshold = col_t.number_input("Threshold", min_value=1, value=item_to_edit['threshold'], step=1, key='edit_threshold')

            col_submit, col_cancel = st.columns([1, 4])
            
            save_button = col_submit.form_submit_button("Save Changes", type="primary")
            col_cancel.button("Cancel", on_click=lambda: st.session_state.__setitem__('edit_id', None))
            
            if save_button:
                item_to_edit['name'] = new_name
                item_to_edit['quantity'] = new_quantity
                item_to_edit['price'] = round(new_price, 2)
                item_to_edit['threshold'] = new_threshold
                
                update_inventory_and_save()
                st.session_state.edit_id = None # Exit edit mode
                st.rerun() # Rerun to refresh the list

# --- Main App Execution ---

def main_app():
    """Runs the main Streamlit application."""
    st.set_page_config(layout="wide", page_title="Canteen Inventory Tracker", page_icon="📝")

    st.title("📝 Canteen Inventory Tracker (Streamlit)")
    st.caption("Data is persisted in `inventory.json` locally.")

    init_state()

    # 1. Sidebar for Adding Items
    render_add_item_form()

    # 2. Main Content Area
    
    # If an item is selected for editing, show the edit form
    if st.session_state.edit_id is not None:
        render_edit_form()
    else:
        # Otherwise, show the summary and the main list
        render_inventory_summary()
        render_inventory_list()

if __name__ == '__main__':
    main_app()
