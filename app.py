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

# Removed: 'edit_id' initialization

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

# Removed: set_edit_mode function
# Removed: cancel_edit function

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
            price = st.number_input("Unit Price (₱)", min_value=0.00, value=1.00, step=0.01, format="%.2f")
        with col3:
            threshold = st.number_input("Low Stock Threshold", min_value=1, value=5, step=1)
        
        submitted = st.form_submit_button("Add Item")
        
        if submitted:
            if name and quantity >= 0 and price >= 0 and threshold >= 1:
                add_item(name, quantity, price, threshold)
                st.session_state.next_item_id += 1 
            else:
                st.error("Please ensure all fields are valid: Name is not empty, Quantity/Price ≥ 0, Threshold ≥ 1.")

# Removed: render_edit_item_form function

def render_inventory_list():
    """Renders the main list of inventory items."""
    st.markdown("### Current Item")
    
    if not st.session_state.canteen_items:
        st.info("No items in stock. Add your first item using the form on the left!")
        return

    # Sort items: Low stock first, then by name
    sorted_items = sorted(st.session_state.canteen_items, 
                         key=lambda x: (x['quantity'] <= x['threshold'], x['name']))

    # Adjusted columns: [Name (4), Price (2), Threshold (2), Stock (2), Actions (3)]
    header_cols = st.columns([4, 2, 2, 2, 3])
    header_cols[0].markdown("**Item Name**")
    header_cols[1].markdown("**Price (₱)**")
    header_cols[2].markdown("**Threshold**")
    header_cols[3].markdown("**Stock**")
    header_cols[4].markdown("**Actions**")
    st.divider()

    for item in sorted_items:
        is_low_stock = item['quantity'] <= item['threshold']
        
        # Streamlit containers for styling
        with st.container(border=True):
            # Adjusted columns for item rows
            col_name, col_price, col_threshold, col_quantity, col_actions = st.columns([4, 2, 2, 2, 3])

            with col_name:
                prefix = "🚨 " if is_low_stock else ""
                st.markdown(f"**{prefix}{item['name']}**")

            with col_price:
                st.markdown(f"₱{item['price']:.2f}")

            with col_threshold:
                st.markdown(f"{item['threshold']}")

            with col_quantity:
                st.markdown(f"<p style='font-size: 1.5rem; font-weight: bold; color: {'red' if is_low_stock else 'green'};'>{item['quantity']}</p>", unsafe_allow_html=True)
            
            with col_actions:
                # Use a smaller column layout for the 3 remaining buttons (+, -, Del)
                btn_col1, btn_col2, btn_col3 = st.columns(3) 
                
                # Decrement button
                with btn_col1:
                    st.button("➖", key=f"dec_{item['id']}", on_click=update_quantity, args=(item['id'], -1), help="Decrement stock")
                
                # Increment button
                with btn_col2:
                    st.button("➕", key=f"inc_{item['id']}", on_click=update_quantity, args=(item['id'], 1), help="Increment stock")
                
                # Delete button with confirmation
                with btn_col3:
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

st.title("🧺 Canteen Item Tracker (Streamlit)")

# Create the two main columns for the layout
col_form, col_list = st.columns([1, 2], gap="large")

with col_form:
    # Removed conditional check for edit_id
    render_add_item_form()  

with col_list:
    total_value = calculate_total_value()
    
    # Display Total Item Value
    st.markdown(
        f"""
        <div style='background-color: #e0f2fe; padding: 15px; border-radius: 8px; border: 1px solid #90cdf4; display: flex; justify-content: space-between; align-items: center;'>
            <span style='font-size: 1.1rem; font-weight: 500; color: #1e40af;'>Total Item Value:</span>
            <span style='font-size: 1.8rem; font-weight: 700; color: #1d4ed8;'>₱{total_value:,.2f}</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")
    render_inventory_list()
