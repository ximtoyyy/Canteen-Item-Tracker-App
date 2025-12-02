import streamlit as st
import pandas as pd
import uuid

# --- 1. CONFIGURATION ---
st.set_page_config(layout="wide", page_title="Canteen Stock Tracker")

# --- 2. STATE INITIALIZATION ---

# Initialize session state for items and ID counter if not present
if 'canteen_items' not in st.session_state:
    st.session_state['canteen_items'] = []

if 'next_item_id' not in st.session_state:
    st.session_state['next_item_id'] = 1

if 'edit_id' not in st.session_state:
    st.session_state['edit_id'] = None

# --- 3. CORE LOGIC FUNCTIONS ---

def add_item(name, quantity, price, threshold):
    """Adds a new item to the session state."""
    new_item = {
        'id': str(uuid.uuid4()), # Use UUID for robust unique IDs
        'name': name,
        'quantity': int(quantity),
        'price': round(float(price), 2),
        'threshold': int(threshold),
    }
    st.session_state.canteen_items.append(new_item)
    st.success(f"Added '{name}' to stock!")

def update_quantity(item_id, change):
    """Increments or decrements item quantity."""
    for item in st.session_state.canteen_items:
        if item['id'] == item_id:
            new_quantity = item['quantity'] + change
            item['quantity'] = max(0, new_quantity)
            break

def delete_item(item_id):
    """Deletes an item from the session state."""
    st.session_state.canteen_items = [item for item in st.session_state.canteen_items if item['id'] != item_id]
    st.success("Item deleted successfully.")

def set_edit_mode(item_id):
    """Sets the specific item ID to be edited."""
    st.session_state.edit_id = item_id

def cancel_edit():
    """Exits the edit mode."""
    st.session_state.edit_id = None

def calculate_total_value():
    """Calculates the total monetary value of all items in stock."""
    total_value = sum(item['quantity'] * item['price'] for item in st.session_state.canteen_items)
    return total_value

# --- 4. UI COMPONENTS ---

def render_add_item_form():
    """Renders the form for adding a new item."""
    st.markdown("### Add New Item")
    with st.form("add_item_form", clear_on_submit=True):
        name = st.text_input("Item Name", placeholder="e.g., Apple Juice")
        col1, col2, col3 = st.columns(3)
        with col1:
            quantity = st.number_input("Quantity in Stock", min_value=0, value=1, step=1)
        with col2:
            price = st.number_input("Unit Price ($)", min_value=0.00, value=1.00, step=0.01, format="%.2f")
        with col3:
            threshold = st.number_input("Low Stock Threshold", min_value=1, value=5, step=1)
        
        submitted = st.form_submit_button("Add Item")
        
        if submitted:
            if name and quantity >= 0 and price >= 0 and threshold >= 1:
                add_item(name, quantity, price, threshold)
                st.session_state.next_item_id += 1 # Only useful if using simple counter, but good practice.
            else:
                st.error("Please ensure all fields are valid: Name is not empty, Quantity/Price ≥ 0, Threshold ≥ 1.")

def render_edit_item_form():
    """Renders the modal/form for editing an existing item's details."""
    if st.session_state.edit_id:
        item_to_edit = next((item for item in st.session_state.canteen_items if item['id'] == st.session_state.edit_id), None)
        
        if item_to_edit:
            st.markdown("### Edit Item Details")
            with st.form("edit_item_form"):
                new_name = st.text_input("Item Name", value=item_to_edit['name'])
                col1, col2 = st.columns(2)
                with col1:
                    new_price = st.number_input("Unit Price ($)", min_value=0.00, value=item_to_edit['price'], step=0.01, format="%.2f")
                with col2:
                    new_threshold = st.number_input("Low Stock Threshold", min_value=1, value=item_to_edit['threshold'], step=1)
                
                col_b1, col_b2, col_b3 = st.columns([1, 1, 4])
                with col_b1:
                    save_button = st.form_submit_button("Update Item")
                with col_b2:
                    st.button("Cancel", on_click=cancel_edit)
                
                if save_button:
                    if new_name and new_price >= 0 and new_threshold >= 1:
                        item_to_edit['name'] = new_name
                        item_to_edit['price'] = round(float(new_price), 2)
                        item_to_edit['threshold'] = int(new_threshold)
                        st.success(f"Details for '{new_name}' updated.")
                        cancel_edit() # Exit edit mode
                        st.rerun()
                    else:
                        st.error("Please ensure Name is not empty, Price is non-negative, and Threshold is at least 1.")

def render_inventory_list():
    """Renders the main list of inventory items."""
    st.markdown("### Current Inventory")
    
    if not st.session_state.canteen_items:
        st.info("No items in stock. Add your first item using the form on the left!")
        return

    # Sort items: Low stock first, then by name
    sorted_items = sorted(st.session_state.canteen_items, 
                         key=lambda x: (x['quantity'] <= x['threshold'], x['name']))

    header_cols = st.columns([1, 3, 2, 2, 2, 2])
    header_cols[1].markdown("**Item Name**")
    header_cols[2].markdown("**Price ($)**")
    header_cols[3].markdown("**Threshold**")
    header_cols[4].markdown("**Stock**")
    header_cols[5].markdown("**Actions**")
    st.divider()

    for item in sorted_items:
        is_low_stock = item['quantity'] <= item['threshold']
        
        # Streamlit containers for styling
        with st.container(border=True):
            col_alert, col_name, col_price, col_threshold, col_quantity, col_actions = st.columns([1, 3, 2, 2, 2, 2])

            with col_alert:
                if is_low_stock:
                    st.error("🚨 Low")

            with col_name:
                st.markdown(f"**{item['name']}**")

            with col_price:
                st.markdown(f"${item['price']:.2f}")

            with col_threshold:
                st.markdown(f"{item['threshold']}")

            with col_quantity:
                st.markdown(f"<p style='font-size: 1.5rem; font-weight: bold; color: {'red' if is_low_stock else 'green'};'>{item['quantity']}</p>", unsafe_allow_html=True)
            
            with col_actions:
                # Use a smaller column layout for the buttons
                btn_col1, btn_col2, btn_col3, btn_col4 = st.columns(4)
                
                # Decrement button
                with btn_col1:
                    st.button("➖", key=f"dec_{item['id']}", on_click=update_quantity, args=(item['id'], -1), help="Decrement stock")
                
                # Increment button
                with btn_col2:
                    st.button("➕", key=f"inc_{item['id']}", on_click=update_quantity, args=(item['id'], 1), help="Increment stock")
                
                # Edit button
                with btn_col3:
                    st.button("✏️", key=f"edit_{item['id']}", on_click=set_edit_mode, args=(item['id'],), help="Edit item details")

                # Delete button with confirmation
                with btn_col4:
                    if st.button("🗑️", key=f"del_{item['id']}", help="Delete item"):
                        # Streamlit confirmation: use a temporary session state variable
                        st.session_state[f'confirm_delete_{item["id"]}'] = True
                
                # Deletion Confirmation Logic
                if st.session_state.get(f'confirm_delete_{item["id"]}'):
                    st.warning(f"Confirm deletion of **{item['name']}**?", icon="⚠️")
                    confirm_col1, confirm_col2 = st.columns(2)
                    with confirm_col1:
                        st.button("Yes, Delete", key=f"confirm_{item['id']}", on_click=delete_item, args=(item['id'],), type="primary")
                    with confirm_col2:
                        st.button("Cancel", key=f"cancel_{item['id']}", on_click=lambda: st.session_state.pop(f'confirm_delete_{item["id"]}'), type="secondary")
                        st.stop() # Stop execution to wait for confirmation

# --- 5. MAIN APP EXECUTION ---

st.title("🧺 Canteen Inventory Tracker (Streamlit)")

# Create the two main columns for the layout
col_form, col_list = st.columns([1, 2], gap="large")

with col_form:
    if st.session_state.edit_id:
        render_edit_item_form()
    else:
        render_add_item_form()

with col_list:
    total_value = calculate_total_value()
    
    # Display Total Inventory Value
    st.markdown(
        f"""
        <div style='background-color: #e0f2fe; padding: 15px; border-radius: 8px; border: 1px solid #90cdf4; display: flex; justify-content: space-between; align-items: center;'>
            <span style='font-size: 1.1rem; font-weight: 500; color: #1e40af;'>Total Inventory Value:</span>
            <span style='font-size: 1.8rem; font-weight: 700; color: #1d4ed8;'>${total_value:,.2f}</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")
    render_inventory_list()
