import sys
import os

# Add backend folder to system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

import backend_module

import streamlit as st
import re
import uuid
import datetime
import json

# --- Configuration ---
SECTIONS = [
    "Documents", "Manage Customers", "Manage Projects",
    "Manage Employees", "Advanced Sample Views"
]
DOCUMENT_CATEGORIES = [
    "Other Documents", "Purchase Invoice",
    "By Project", "Pending Proposal", "Pictures"
]

# --- Setup folders ---
try:
    backend_module.create_folder_structure(["Documents/" + cat for cat in DOCUMENT_CATEGORIES] + ["Documents"] +
                                           ["Customers", "Employees", "Projects", "AdvancedSampleViews"])
except Exception as e:
    st.error(f"Failed to create folder structure: {e}")

# --- Page Setup ---
st.set_page_config(page_title="SHARP-Files", layout="wide")

# --- Session State Setup ---
if "search_query" not in st.session_state:
    st.session_state["search_query"] = ""
if "search_mode" not in st.session_state:
    st.session_state["search_mode"] = "Search Current Section"

# --- Top Red Header ---
st.markdown("""
    <div style="background-color: red; padding: 10px;">
        <h1 style="color: white; text-align: left;">SHARP-Files</h1>
    </div>
""", unsafe_allow_html=True)

# --- Sidebar for Common Views ---
st.sidebar.title("Common Views")
selected_section = st.sidebar.radio("Navigate", SECTIONS)

# --- Search Bar ---
col_mode, col_search, col_clear = st.columns([2, 5, 1])

with col_mode:
    st.session_state["search_mode"] = st.selectbox(
        "Search Mode",
        ["Search Current Section", "Search Entire Vault"],
        index=0 if st.session_state["search_mode"] == "Search Current Section" else 1
    )

def clear_search():
    st.session_state["search_query"] = ""
    st.session_state["search_box"] = ""

with col_search:
    search_input = st.text_input(
        "Search",
        value=st.session_state["search_query"],
        placeholder="Search for files or metadata...",
        key="search_box"
    )

with col_clear:
    st.button("Clear", help="Clear search", on_click=clear_search)

st.session_state["search_query"] = st.session_state["search_box"]
search_query = st.session_state["search_query"]
search_mode = st.session_state["search_mode"]

# --- Helper Functions ---
def generate_safe_key(prefix, section, filename, idx):
    safe_file = re.sub(r'\W+', '_', filename)
    safe_section = re.sub(r'\W+', '_', section)
    return f"{prefix}_{safe_section}_{safe_file}_{idx}"

def display_metadata(file_path, metadata, edit_key):
    try:
        meta_path = file_path + ".json"
        edit_state_key = f"edit_mode_{edit_key}"
        if edit_state_key not in st.session_state:
            st.session_state[edit_state_key] = False

        with st.expander("Metadata"):
            if not st.session_state[edit_state_key]:
                for key, value in metadata.items():
                    if key not in ["Created", "Modified"]:  # Removed Created and Modified fields from display
                        st.write(f"**{key}:** {value}")
                if st.button("Edit Metadata", key=f"{edit_key}_edit"):
                    st.session_state[edit_state_key] = True
            else:
                updated_metadata = {}
                for key, value in metadata.items():
                    if key in ["File Name", "Size (KB)"]:
                        st.write(f"**{key}:** {value}")
                    elif key not in ["Created", "Modified"]:
                        updated_metadata[key] = st.text_input(f"{key}", value=str(value), key=f"{edit_key}_{key}")
                col_save, col_cancel = st.columns([1,1])
                with col_save:
                    if st.button("Save", key=f"{edit_key}_save"):
                        if "Tags" in updated_metadata:
                            updated_metadata["Tags"] = [tag.strip() for tag in updated_metadata["Tags"].split(",") if tag.strip()]
                        try:
                            with open(meta_path, "w") as f:
                                json.dump(updated_metadata, f, indent=4)
                            st.success("Metadata updated successfully.")
                        except Exception as e:
                            st.error(f"Failed to save metadata: {e}")
                        st.session_state[edit_state_key] = False
                        st.rerun()
                with col_cancel:
                    if st.button("❌ Cancel", key=f"{edit_key}_cancel"):
                        st.session_state[edit_state_key] = False
    except Exception as e:
        st.error(f"Failed to display metadata: {e}")

def display_files(folder_path, prefix, section_name):
    try:
        files = backend_module.list_files_with_metadata_search(folder_path, search_query) if search_query else backend_module.list_files(folder_path)
        if not files:
            st.info("No files found.")
            return
        for idx, file in enumerate(files):
            file_path = os.path.join(folder_path, file)
            if not os.path.isfile(file_path) or file.endswith(".json"):
                continue
            key_base = generate_safe_key(prefix, section_name, file, idx)
            col1, col2, col3 = st.columns([5, 1, 1])
            col1.markdown(f"**{file}**")
            with col2:
                try:
                    with open(file_path, "rb") as f:
                        st.download_button("⬇️", f, file_name=file, key=f"dl_{key_base}")
                except Exception as e:
                    st.error(f"Failed to prepare download: {e}")
            with col3:
                if st.button("Delete", key=f"del_{key_base}"):
                    try:
                        backend_module.delete_file(file_path)
                        st.success(f"Deleted '{file}' successfully.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to delete file: {e}")
            metadata = backend_module.get_file_metadata(file_path)
            display_metadata(file_path, metadata, key_base)
    except Exception as e:
        st.error(f"Failed to display files: {e}")

def upload_with_metadata(folder_path, upload_key, label):
    try:
        uploaded_file = st.file_uploader(label, key=upload_key)
        if uploaded_file:
            with st.expander("Enter Metadata", expanded=True):
                author = st.text_input("Author")
                customer_name = st.text_input("Customer Name")
                project_name = st.text_input("Project Name")
                owner = st.text_input("Owner")
                tags = st.text_input("Tags (comma-separated)")
            if st.button("Save Upload", key=f"save_{upload_key}"):
                filename = backend_module.save_uploaded_file(folder_path, uploaded_file)
                if filename:
                    metadata = {
                        "Author": author,
                        "Customer Name": customer_name,
                        "Project Name": project_name,
                        "Owner": owner,
                        "Tags": [tag.strip() for tag in tags.split(",") if tag.strip()]
                    }
                    backend_module.save_custom_metadata(os.path.join(folder_path, filename), metadata)
                    st.success(f"Uploaded '{filename}' with metadata.")
                    st.rerun()
                else:
                    st.error("File upload failed.")
    except Exception as e:
        st.error(f"Failed to upload file: {e}")

def search_entire_vault():
    try:
        st.markdown("### Entire Vault Search Results")
        found = False
        all_sections = [("Documents", "Documents")] + \
                       [(cat, os.path.join("Documents", cat)) for cat in DOCUMENT_CATEGORIES] + \
                       [("Customers", "Customers"), ("Projects", "Projects"),
                        ("Employees", "Employees"), ("AdvancedSampleViews", "AdvancedSampleViews")]

        for section_label, folder in all_sections:
            folder_path = os.path.join(backend_module.BASE_DIR, folder)
            files = backend_module.list_files_with_metadata_search(folder_path, search_query)
            if files:
                found = True
                st.markdown(f"#### {section_label}")
                display_files(folder_path, "entire", section_label)
        if not found:
            st.info("No matching files found in entire vault.")
    except Exception as e:
        st.error(f"Failed to perform entire vault search: {e}")

# --- Section Logic ---
try:
    if search_mode == "Search Entire Vault" and search_query:
        search_entire_vault()
    else:
        if selected_section == "Documents":
            selected_category = st.selectbox("Select Document Category", DOCUMENT_CATEGORIES)
            folder_path = os.path.join(backend_module.BASE_DIR, "Documents", selected_category)
            upload_with_metadata(folder_path, f"upload_{selected_category}", "Upload File")
            display_files(folder_path, "doc", selected_category)

        elif selected_section == "Manage Customers":
            folder_path = os.path.join(backend_module.BASE_DIR, "Customers")
            upload_with_metadata(folder_path, "upload_customer", "Upload Customer File")
            display_files(folder_path, "cust", "Customers")

        elif selected_section == "Manage Projects":
            folder_path = os.path.join(backend_module.BASE_DIR, "Projects")
            upload_with_metadata(folder_path, "upload_project", "Upload Project File")
            display_files(folder_path, "proj", "Projects")

        elif selected_section == "Manage Employees":
            folder_path = os.path.join(backend_module.BASE_DIR, "Employees")
            upload_with_metadata(folder_path, "upload_employee", "Upload Employee File")
            display_files(folder_path, "emp", "Employees")

        elif selected_section == "Advanced Sample Views":
            folder_path = os.path.join(backend_module.BASE_DIR, "AdvancedSampleViews")
            upload_with_metadata(folder_path, "upload_advanced", "Upload Advanced File")
            display_files(folder_path, "adv", "AdvancedSampleViews")
except Exception as e:
    st.error(f"An unexpected error occurred: {e}")
