import streamlit as st
import pandas as pd
import os

# --- Constants for file paths ---
DRIVERS_FILE = 'drivers.csv'
TOURS_FILE = 'tours.csv'
ASSIGNMENTS_FILE = 'assignments.csv'

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

# --- Streamlit Application Setup ---
st.set_page_config(layout="wide")
st.title('Driver and Tour Assignment Application')
st.write("Welcome to the Driver and Tour Assignment Application!")

# Load initial data on startup
drivers, tours, assignments_df = load_data()

# Initialize session state with loaded data
if 'drivers' not in st.session_state:
    st.session_state.drivers = drivers
if 'tours' not in st.session_state:
    st.session_state.tours = tours
if 'assignments_df' not in st.session_state:
    st.session_state.assignments_df = assignments_df.astype(int) # Ensure integer type for assignments

st.header("Add Drivers and Tours")

# Input fields and buttons for adding drivers
with st.form("add_driver_form", clear_on_submit=True):
    driver_name = st.text_input("Driver Name", key="driver_input")
    col1, col2 = st.columns([1,1])
    with col1:
        add_driver_button = st.form_submit_button("Add Driver")
    with col2:
        add_nothing_driver_button = st.form_submit_button("Add Nothing (Driver)")

    if add_driver_button and driver_name:
        st.session_state.drivers.append(driver_name)
        save_drivers(st.session_state.drivers) # Save after adding
        st.success(f"Driver '{driver_name}' added!")

# Input fields and buttons for adding tours
with st.form("add_tour_form", clear_on_submit=True):
    tour_name = st.text_input("Tour Name", key="tour_input")
    col3, col4 = st.columns([1,1])
    with col3:
        add_tour_button = st.form_submit_button("Add Tour")
    with col4:
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

    col5, col6 = st.columns([1,1])
    with col5:
        assign_button = st.form_submit_button("Assign")
    with col6:
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
            st.experimental_rerun()
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
                st.experimental_rerun()
            else:
                st.error("Could not determine a best driver for automatic assignment.")

st.header("Data Persistence")

# Global Save All Data button
if st.button("Save All Data"): # No form needed as it's a global action
    save_drivers(st.session_state.drivers)
    save_tours(st.session_state.tours)
    save_assignments(st.session_state.assignments_df)
    st.success("All driver, tour, and assignment data saved successfully to CSV files!")