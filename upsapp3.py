# -*- coding: utf-8 -*-
"""UPSapp3.ipynb

Original file is located at
    https://colab.research.google.com/drive/1ZVRyWcDU32Og3ObkcNpKvSELEcuBO1Zh
"""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import os
import sys
import numpy as np # New import for numerical operations
from scipy.optimize import linear_sum_assignment # New import for optimal assignment

# --- Constants for file paths ---
DRIVERS_FILE = 'drivers.csv'
TOURS_FILE = 'tours.csv'
ASSIGNMENTS_FILE = 'assignments.csv'
UNAVAILABLE_FILE = 'unavailable.csv'

# --- Helper functions for saving data ---
def save_drivers(drivers_list):
    pd.DataFrame(drivers_list).to_csv(DRIVERS_FILE, index=False, header=False)

def save_tours(tours_list):
    pd.DataFrame(tours_list).to_csv(TOURS_FILE, index=False, header=False)

def save_assignments(assignments_df):
    assignments_df.to_csv(ASSIGNMENTS_FILE, index=True)

# --- Helper function for loading data ---
def load_data():
    # Load drivers
    if os.path.exists(DRIVERS_FILE):
        drivers = pd.read_csv(DRIVERS_FILE, header=None).iloc[:, 0].tolist()
    else:
        drivers = []

    # Load tours
    if os.path.exists(TOURS_FILE):
        tours = pd.read_csv(TOURS_FILE, header=None).iloc[:, 0].tolist()
    else:
        tours = []

    # Load assignments
    if os.path.exists(ASSIGNMENTS_FILE):
        assignments_df = pd.read_csv(ASSIGNMENTS_FILE, index_col=0)
        # Ensure columns are treated as strings if they were saved as numbers (e.g., from empty df)
        assignments_df.columns = assignments_df.columns.astype(str)
        # Ensure index is treated as strings
        assignments_df.index = assignments_df.index.astype(str)
    else:
        assignments_df = pd.DataFrame(index=[], columns=[])

    return drivers, tours, assignments_df

def save_unavailable(unavail_dict):
    """Save unavailable drivers mapping (driver -> {tour:count}) to CSV."""
    if not unavail_dict:
        # Remove file if exists to avoid stale data
        try:
            if os.path.exists(UNAVAILABLE_FILE):
                os.remove(UNAVAILABLE_FILE)
        except Exception:
            pass
        return

    # Build DataFrame from dict
    df = pd.DataFrame.from_dict(unavail_dict, orient='index').fillna(0).astype(int)
    df.to_csv(UNAVAILABLE_FILE)

def load_unavailable():
    """Load unavailable drivers mapping from CSV file. Returns dict driver->dict(tour->count)."""
    if os.path.exists(UNAVAILABLE_FILE):
        df = pd.read_csv(UNAVAILABLE_FILE, index_col=0)
        df.columns = df.columns.astype(str)
        df.index = df.index.astype(str)
        # Convert to dict of dicts
        return {idx: row.dropna().to_dict() for idx, row in df.iterrows()}
    return {}

# --- Streamlit Application Setup ---
# If running as a frozen executable, launch via Streamlit bootstrap so it opens in a browser.
def _streamlit_script_path():
    if getattr(sys, "frozen", False):
        base_dir = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
        candidate = os.path.join(base_dir, "upsapp3.py")
        if os.path.exists(candidate):
            return candidate
    return os.path.abspath(__file__)

if getattr(sys, "frozen", False):
    from streamlit.web import bootstrap

    script_path = _streamlit_script_path()
    os.environ["STREAMLIT_GLOBAL_DEVELOPMENT_MODE"] = "false"
    bootstrap.run(
        script_path,
        "",
        [],
        flag_options={
            "server.headless": True,
            "browser.serverAddress": "localhost",
            "server.port": 8501,
            "global.developmentMode": False,
        },
    )
    raise SystemExit(0)
st.set_page_config(layout="wide")

# Arrange title, welcome message and image using columns for top-right placement
col1, col2 = st.columns([3, 1])
with col1:
    st.title('Driver and Tour Assignment Application')
    st.write("Welcome to the Driver and Tour Assignment Application!")
with col2:
    st.image("https://www.logodesignlove.com/images/contentious/ups-logo.jpg", width=100)

# Custom CSS for brown and gold theme with black letters
st.markdown("""
    <style>
    /* Main app background */
    .stApp {
        background-color: #5C4033; /* Coffee Brown */
    }
    /* General text color */
    .stApp, .stText, .stMarkdown, p, label, .st-ck, .st-dd, .st-br, .st-bw { /* Selectors for various text elements */
        color: #000000; /* Black letters */
    }
    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        color: #000000; /* Black for headers */
    }
    /* Primary color for buttons */
    .stButton>button {
        background-color: #FFD700; /* Gold button background */
        color: #000000; /* Black text on gold button */
        border: none;
    }
    .stButton>button:hover {
        background-color: #DAA520; /* Darker  gold on hover */
        color: #000000;
    }
    /* Input fields and selectboxes */
    .stTextInput>div>div>input, .stSelectbox>div>div>div[data-baseweb="select"] { /* Target selectbox specifically */
        background-color: #7D5B4F; /* Lighter brown for input backgrounds */
        color: #000000; /* Black text in inputs */
    }
    /* Data editor */
    .stDataFrame {
        color: #000000; /* Black text for dataframe content */
    }
    /* Specific targeting for data editor cells and headers */
    .stDataFrame .data-grid-header, .stDataFrame .data-grid-row {
        background-color: #7D5B4F; /* Lighter brown for dataframe background */
    }
    .stDataFrame .data-grid-header .header-cell {
        color: #000000; /* Black header text for dataframe */
    }
    .stDataFrame .data-grid-row .grid-cell {
        color: #000000; /* Black text for data editor cells */
    }
    </style>
""", unsafe_allow_html=True)
components.html(
        """
        <div style="position:fixed;top:8px;left:12px;z-index:2147483647;pointer-events:none;">
            <span style="font-size:12px;color:#FFFFFF;opacity:0.9;font-family:Arial, sans-serif;">
                Made by Vitor de Almeida
            </span>
        </div>
        """,
        height=40,
        width=300,
)

# Load initial data on startup
drivers, tours, assignments_df = load_data()

# Initialize session state with loaded data
if 'drivers' not in st.session_state:
    st.session_state.drivers = drivers
if 'tours' not in st.session_state:
    st.session_state.tours = tours
if 'assignments_df' not in st.session_state:
    st.session_state.assignments_df = assignments_df.astype(int) # Ensure integer type for assignments
# Load unavailable drivers mapping and store in session state
if 'unavailable' not in st.session_state:
    st.session_state.unavailable = load_unavailable()

# --- New: Load Assignments from File ---
st.subheader("Load Assignments from File")
uploaded_file = st.file_uploader("Upload CSV or Excel file for Assignments", type=['csv', 'xlsx'])
load_file_button = st.button("Load Data From Uploaded File")

if load_file_button and uploaded_file is not None:
    try:
        # Determine file type and read accordingly
        if uploaded_file.name.endswith('.csv'):
            uploaded_df = pd.read_csv(uploaded_file, index_col=0) # Assuming first column is index (drivers)
        elif uploaded_file.name.endswith('.xlsx'):
            uploaded_df = pd.read_excel(uploaded_file, index_col=0) # Assuming first column is index (drivers)
        else:
            st.error("Unsupported file type. Please upload a CSV or Excel file.")
            uploaded_df = pd.DataFrame() # Empty DataFrame to prevent further processing

        if not uploaded_df.empty:
            # Ensure columns and index are string types
            uploaded_df.columns = uploaded_df.columns.astype(str)
            uploaded_df.index = uploaded_df.index.astype(str)
            # Ensure numeric values are integer type
            uploaded_df = uploaded_df.astype(int)

            # Update session state with new data
            st.session_state.assignments_df = uploaded_df
            st.session_state.drivers = uploaded_df.index.tolist()
            st.session_state.tours = uploaded_df.columns.tolist()

            # Save the newly loaded data for persistence
            save_assignments(st.session_state.assignments_df)
            save_drivers(st.session_state.drivers)
            save_tours(st.session_state.tours)

            st.success("Assignments, drivers, and tours loaded successfully from file!")
            st.rerun() # Rerun to update all components with new data
    except Exception as e:
        st.error(f"Error loading file: {e}")

st.header("Add Drivers and Tours")

# Input fields and buttons for adding drivers
with st.form("add_driver_form", clear_on_submit=True):
    driver_name = st.text_input("Driver Name", key="driver_input")
    col3, col4 = st.columns([1,1])
    with col3:
        add_driver_button = st.form_submit_button("Add Driver")
    with col4:
        add_nothing_driver_button = st.form_submit_button("Add Nothing (Driver)")

    if add_driver_button and driver_name:
        st.session_state.drivers.append(driver_name)
        save_drivers(st.session_state.drivers) # Save after adding
        st.success(f"Driver '{driver_name}' added!")

# Input fields and buttons for adding tours
with st.form("add_tour_form", clear_on_submit=True):
    tour_name = st.text_input("Tour Name", key="tour_input")
    col5, col6 = st.columns([1,1])
    with col5:
        add_tour_button = st.form_submit_button("Add Tour")
    with col6:
        add_nothing_tour_button = st.form_submit_button("Add Nothing (Tour)")

    if add_tour_button and tour_name:
        st.session_state.tours.append(tour_name)
        save_tours(st.session_state.tours) # Save after adding
        st.success(f"Tour '{tour_name}' added!")

# Display current lists (for testing)
st.subheader("Current Drivers")
st.write(st.session_state.drivers)

st.subheader("Current Tours")
st.write(st.session_state.tours)

st.header("Driver and Tour Assignment Table")

# Get current drivers and tours from session state
current_drivers = st.session_state.drivers
current_tours = st.session_state.tours

# Update DataFrame based on current drivers and tours
def update_assignments_df_logic():
    df = st.session_state.assignments_df.copy()

    # Add new drivers as index rows
    new_drivers = [d for d in current_drivers if d not in df.index]
    if new_drivers:
        new_driver_df = pd.DataFrame(0, index=new_drivers, columns=df.columns)
        df = pd.concat([df, new_driver_df])

    # Add new tours as columns
    new_tours = [t for t in current_tours if t not in df.columns]
    if new_tours:
        for tour in new_tours:
            df[tour] = 0

    # Remove drivers no longer present (optional, depending on requirements, for now keeping all added)
    # df = df[df.index.isin(current_drivers)]

    # Remove tours no longer present (optional)
    # df = df[current_tours]

    # Ensure order is consistent (optional but good practice)
    df = df.reindex(index=current_drivers, columns=current_tours).fillna(0)

    st.session_state.assignments_df = df.astype(int) # Ensure integer type for assignments
    save_assignments(st.session_state.assignments_df) # Save after updating structure

# Trigger update if drivers or tours lists change or df index/columns don't match
if (set(st.session_state.drivers) != set(st.session_state.assignments_df.index) or \
    set(st.session_state.tours) != set(st.session_state.assignments_df.columns)):
    update_assignments_df_logic()

# Display the editable DataFrame
if not st.session_state.assignments_df.empty:
    edited_df = st.data_editor(
        st.session_state.assignments_df,
        column_config={
            col: st.column_config.NumberColumn(
                col,
                min_value=0,
                step=1,
                format="%d"
            )
            for col in st.session_state.assignments_df.columns
        },
        num_rows="dynamic", # Allows adding new rows directly in the editor (though we add via form)
        use_container_width=True,
        hide_index=False,
        key="assignment_data_editor"
    )
    # Check if the edited_df is different from the stored assignments_df
    if not st.session_state.assignments_df.equals(edited_df):
        st.session_state.assignments_df = edited_df
        save_assignments(st.session_state.assignments_df) # Save after user edits
        st.success("Assignments updated and saved!")
else:
    st.info("Add drivers and tours to start assigning.")

st.header("Manual Driver-Tour Assignment")

with st.form("manual_assignment_form", clear_on_submit=True):
    st.subheader("Assign a Driver to a Tour")

    # Select Driver dropdown
    drivers_list = ["Select Driver"] + st.session_state.drivers
    selected_driver = st.selectbox("Driver", options=drivers_list, key="manual_driver_select")

    # Select Tour dropdown
    tours_list = ["Select Tour"] + st.session_state.tours
    selected_tour = st.selectbox("Tour", options=tours_list, key="manual_tour_select")

    # Assignment Count input
    assignment_count = st.number_input("Assignment Count", min_value=1, step=1, key="manual_assignment_count")

    col7, col8 = st.columns([1,1])
    with col7:
        assign_button = st.form_submit_button("Assign")
    with col8:
        no_change_button = st.form_submit_button("No Change")

    if assign_button:
        if selected_driver == "Select Driver" or selected_tour == "Select Tour":
            st.warning("Please select both a driver and a tour.")
        else:
            if selected_driver not in st.session_state.assignments_df.index:
                st.session_state.assignments_df.loc[selected_driver] = 0 # Add new driver row if not present
            if selected_tour not in st.session_state.assignments_df.columns:
                st.session_state.assignments_df[selected_tour] = 0 # Add new tour column if not present

            st.session_state.assignments_df.loc[selected_driver, selected_tour] += assignment_count
            save_assignments(st.session_state.assignments_df)
            st.success(f"Assigned {assignment_count} tours to driver '{selected_driver}' for tour '{selected_tour}'.")
            # Rerun to update the data_editor immediately
            st.rerun()
    # 'No Change' button does nothing explicitly, form clears on submit automatically

st.header("Automatic 'Best Driver' Assignment")

with st.form("auto_assign_form", clear_on_submit=True):
    st.subheader("Automatically Assign to Best Driver for a Tour")

    # Select Tour dropdown for automatic assignment
    auto_assign_tours_list = ["Select Tour"] + st.session_state.tours
    selected_tour_auto = st.selectbox("Select Tour for Automatic Assignment", options=auto_assign_tours_list, key="auto_tour_select")

    auto_assign_button = st.form_submit_button("Assign Best Driver")

    if auto_assign_button:
        if selected_tour_auto == "Select Tour":
            st.warning("Please select a tour for automatic assignment.")
        elif not st.session_state.drivers:
            st.warning("No drivers available to assign.")
        else:
            # Find the best driver for the selected tour
            best_driver = None
            max_assignments = -1

            # Ensure the selected tour exists as a column in the assignments_df
            if selected_tour_auto not in st.session_state.assignments_df.columns:
                st.session_state.assignments_df[selected_tour_auto] = 0 # Add the column if it doesn't exist

            # Filter out drivers that might not be in the current assignments_df index
            available_drivers_in_df = [d for d in st.session_state.drivers if d in st.session_state.assignments_df.index]

            if not available_drivers_in_df:
                # If there are no drivers in the DataFrame yet, assign to the first available driver
                if st.session_state.drivers:
                    best_driver = st.session_state.drivers[0]
                    if best_driver not in st.session_state.assignments_df.index:
                        st.session_state.assignments_df.loc[best_driver] = 0 # Add new driver row if not present
                else:
                    st.warning("No drivers available for assignment.")
                    st.stop() # Stop execution if no drivers

            else:
                # Iterate through drivers to find the one with most assignments for this tour
                for driver in available_drivers_in_df:
                    if driver in st.session_state.assignments_df.index and selected_tour_auto in st.session_state.assignments_df.columns:
                        assignments_for_tour = st.session_state.assignments_df.loc[driver, selected_tour_auto]
                        if assignments_for_tour > max_assignments:
                            max_assignments = assignments_for_tour
                            best_driver = driver

                # Handle case where all current drivers have 0 assignments for this tour
                if best_driver is None:
                    # Assign to the first driver alphabetically or simply the first in the list
                    if st.session_state.drivers:
                        best_driver = sorted(st.session_state.drivers)[0]
                        if best_driver not in st.session_state.assignments_df.index:
                            st.session_state.assignments_df.loc[best_driver] = 0 # Add new driver row if not present

            if best_driver:
                st.session_state.assignments_df.loc[best_driver, selected_tour_auto] += 1
                save_assignments(st.session_state.assignments_df)
                st.success(f"Automatically assigned tour '{selected_tour_auto}' to '{best_driver}'.")
                st.rerun()
            else:
                st.error("Could not determine a best driver for automatic assignment.")

# --- New: Automatic Optimal Assignment (Hungarian Algorithm) ---
st.header("Automatic Optimal Assignment")

with st.form("auto_optimal_assign_form", clear_on_submit=True):
    st.subheader("Perform Optimal One-to-One Driver-Tour Assignment")
    st.info("This will try to assign each driver to a unique tour and each tour to a unique driver, maximizing the sum of past assignment counts. Existing assignments will be overwritten for this optimal set.")

    perform_optimal_assign_button = st.form_submit_button("Perform Optimal Assignment")

    if perform_optimal_assign_button:
        current_drivers = st.session_state.drivers
        current_tours = st.session_state.tours

        if not current_drivers or not current_tours:
            st.warning("Please add drivers and tours before attempting optimal assignment.")
        else:
            n_drivers = len(current_drivers)
            n_tours = len(current_tours)

            # Warn if counts are different, as perfect one-to-one won't be possible for all
            if n_drivers != n_tours:
                st.warning(f"Number of drivers ({n_drivers}) does not match number of tours ({n_tours}). Optimal assignment will match up to the minimum (which is {min(n_drivers, n_tours)}), leaving the remaining {'drivers' if n_drivers > n_tours else 'tours'} unassigned in this optimal set.")

            # Create a base matrix from current assignments, filling missing with 0
            base_matrix = st.session_state.assignments_df.reindex(index=current_drivers, columns=current_tours, fill_value=0)

            # Get the raw values and convert to negative for minimization by linear_sum_assignment
            cost_values = -base_matrix.values

            # Determine the maximum dimension for the square matrix required by linear_sum_assignment
            max_dim = max(n_drivers, n_tours)

            # Pad the cost_values array to make it square with zeros
            padded_cost_matrix = np.zeros((max_dim, max_dim))
            padded_cost_matrix[:n_drivers, :n_tours] = cost_values

            # Apply Hungarian algorithm
            row_ind, col_ind = linear_sum_assignment(padded_cost_matrix)

            # Construct the new optimal assignments DataFrame
            new_optimal_assignments_df = pd.DataFrame(0, index=current_drivers, columns=current_tours)
            successful_assignments = 0
            # Collect assigned pairs so we can present a simple mapping table
            assigned_pairs = []
            for r, c in zip(row_ind, col_ind):
                # Ensure we are not assigning dummy drivers/tours by checking indices against original dimensions
                if r < n_drivers and c < n_tours:
                    driver = current_drivers[r]
                    tour = current_tours[c]
                    # Record the optimal pairing (even if past count is zero)
                    new_optimal_assignments_df.loc[driver, tour] = base_matrix.loc[driver, tour]
                    successful_assignments += 1
                    assigned_pairs.append((driver, tour))

            # Save the optimal assignment matrix
            st.session_state.assignments_df = new_optimal_assignments_df.astype(int)
            save_assignments(st.session_state.assignments_df)

            # Build a dataframe mapping each driver to their assigned tour (or 'Unassigned')
            assigned_map = {d: 'Unassigned' for d in current_drivers}
            for d, t in assigned_pairs:
                assigned_map[d] = t

            assigned_df = pd.DataFrame(
                [{'Driver': d, 'Assigned Tour': assigned_map[d]} for d in current_drivers]
            )

            # Store the result in session state so it persists across reruns and can be displayed
            st.session_state['last_optimal_pairs'] = assigned_df

            st.success(f"Successfully performed optimal assignment: {successful_assignments} unique driver-tour pairs assigned.")
            st.rerun()

st.header("Data Persistence")

# Global Save All Data button
if st.button("Save All Data"): # No form needed as it's a global action
    save_drivers(st.session_state.drivers)
    save_tours(st.session_state.tours)
    save_assignments(st.session_state.assignments_df)
    st.success("All driver, tour, and assignment data saved successfully to CSV files!")

# If an optimal-assignment mapping exists from the last run, display it as a table
if 'last_optimal_pairs' in st.session_state:
    st.subheader("Optimal Assignment Results")
    st.table(st.session_state['last_optimal_pairs'])

# --- Temporarily Unavailable Drivers ---
st.header("Temporarily Unavailable Drivers")

with st.form("mark_unavailable_form", clear_on_submit=True):
    st.subheader("Mark a Driver Unavailable")
    available_drivers = st.session_state.drivers.copy()
    if available_drivers:
        selected_unavail = st.selectbox("Select driver to mark unavailable", options=["Select Driver"] + available_drivers, key="mark_unavail_select")
        mark_unavail_btn = st.form_submit_button("Mark Unavailable")
    else:
        st.info("No available drivers to mark unavailable.")
        selected_unavail = None
        mark_unavail_btn = False

    if mark_unavail_btn:
        if not selected_unavail or selected_unavail == "Select Driver":
            st.warning("Please select a driver to mark unavailable.")
        else:
            driver = selected_unavail
            # Snapshot assignments for this driver (or zeros if not present)
            if driver in st.session_state.assignments_df.index:
                snapshot = st.session_state.assignments_df.loc[driver].to_dict()
            else:
                snapshot = {t: 0 for t in st.session_state.tours}

            # Save to unavailable mapping
            st.session_state.unavailable[driver] = snapshot
            save_unavailable(st.session_state.unavailable)

            # Remove driver from active drivers and assignments
            if driver in st.session_state.drivers:
                st.session_state.drivers.remove(driver)
            if driver in st.session_state.assignments_df.index:
                st.session_state.assignments_df = st.session_state.assignments_df.drop(index=driver)

            save_drivers(st.session_state.drivers)
            save_assignments(st.session_state.assignments_df)
            st.success(f"Driver '{driver}' marked unavailable and snapshot saved.")
            st.rerun()

# Display list/table of unavailable drivers
if st.session_state.unavailable:
    st.subheader("Unavailable Drivers List")
    unavail_df = pd.DataFrame.from_dict(st.session_state.unavailable, orient='index').fillna(0).astype(int)
    unavail_df.index.name = 'Driver'
    st.table(unavail_df)

    # Form to restore drivers
    with st.form("restore_driver_form", clear_on_submit=True):
        st.subheader("Restore an Unavailable Driver")
        unavail_list = list(st.session_state.unavailable.keys())
        selected_restore = st.selectbox("Select driver to restore", options=["Select Driver"] + unavail_list, key="restore_select")
        restore_btn = st.form_submit_button("Make Available")

        if restore_btn:
            if not selected_restore or selected_restore == "Select Driver":
                st.warning("Please select a driver to restore.")
            else:
                driver = selected_restore
                saved_counts = st.session_state.unavailable.get(driver, {})

                # Ensure tours from saved_counts exist in current tours; add missing tours
                missing_tours = [t for t in saved_counts.keys() if t not in st.session_state.tours]
                if missing_tours:
                    for t in missing_tours:
                        st.session_state.tours.append(t)
                        # add column with zeros for existing drivers
                        st.session_state.assignments_df[t] = 0
                    save_tours(st.session_state.tours)

                # Ensure assignments_df has all current tours as columns
                st.session_state.assignments_df = st.session_state.assignments_df.reindex(columns=st.session_state.tours, fill_value=0)

                # Insert restored driver's row with exact saved counts (fill missing with 0)
                row_values = {t: int(saved_counts.get(t, 0)) for t in st.session_state.tours}
                st.session_state.assignments_df.loc[driver] = pd.Series(row_values)

                # Add driver back to active drivers list
                if driver not in st.session_state.drivers:
                    st.session_state.drivers.append(driver)

                # Remove from unavailable mapping and save
                st.session_state.unavailable.pop(driver, None)
                save_unavailable(st.session_state.unavailable)

                save_drivers(st.session_state.drivers)
                save_assignments(st.session_state.assignments_df)
                st.success(f"Driver '{driver}' restored with original assignment counts.")
                st.rerun()
else:
    st.info("No drivers are currently marked unavailable.")