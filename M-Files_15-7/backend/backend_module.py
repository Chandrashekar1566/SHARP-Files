import os
import json
from docx import Document
from reportlab.pdfgen import canvas
from PIL import Image, ImageDraw

BASE_DIR = "uploaded_documents"

def create_folder_structure(folders):
    """
    Creates required folder structure inside BASE_DIR.
    """
    try:
        os.makedirs(BASE_DIR, exist_ok=True)
        for folder in folders:
            os.makedirs(os.path.join(BASE_DIR, folder), exist_ok=True)
        print("Folder structure created successfully.")
    except Exception as e:
        print(f"[ERROR] Failed to create folder structure: {e}")

def save_uploaded_file(folder_path, uploaded_file):
    """
    Saves an uploaded file to the given folder path.
    """
    try:
        save_path = os.path.join(folder_path, uploaded_file.name)
        with open(save_path, "wb") as f:
            f.write(uploaded_file.read())
        print(f"File saved: {save_path}")
        return uploaded_file.name
    except Exception as e:
        print(f"[ERROR] Failed to save uploaded file: {e}")
        return None

def save_custom_metadata(file_path, metadata_dict):
    """
    Saves custom metadata as a JSON file associated with the given file.
    """
    try:
        meta_path = file_path + ".json"
        with open(meta_path, "w") as f:
            json.dump(metadata_dict, f, indent=4)
        print(f"Metadata saved: {meta_path}")
    except Exception as e:
        print(f"[ERROR] Failed to save metadata for {file_path}: {e}")

def get_file_metadata(file_path):
    """
    Returns a dictionary containing file stats and custom metadata if available.
    """
    metadata = {}
    try:
        stats = os.stat(file_path)
        metadata = {
            "File Name": os.path.basename(file_path),
            "Size (KB)": round(stats.st_size / 1024, 2),
            "Created": stats.st_ctime,
            "Modified": stats.st_mtime
        }
    except Exception as e:
        print(f"[ERROR] Failed to get file stats for {file_path}: {e}")
        return metadata

    # Load custom metadata if exists
    meta_path = file_path + ".json"
    if os.path.exists(meta_path):
        try:
            with open(meta_path, "r") as f:
                user_metadata = json.load(f)
            metadata.update(user_metadata)
        except Exception as e:
            print(f"[ERROR] Failed to read metadata for {file_path}: {e}")
    return metadata

def list_files(folder_path, query=None):
    """
    Lists files in a folder optionally filtered by filename query.
    """
    try:
        if not os.path.exists(folder_path):
            return []
        files = os.listdir(folder_path)
        if query:
            files = [f for f in files if query.lower() in f.lower()]
        return files
    except Exception as e:
        print(f"[ERROR] Failed to list files in {folder_path}: {e}")
        return []

def list_files_with_metadata_search(folder_path, search_query=None):
    """
    Returns list of files matching search_query in either filename or metadata content.
    """
    try:
        if not os.path.exists(folder_path):
            return []
        files = []
        for file in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file)
            if os.path.isfile(file_path) and not file.endswith(".json"):
                match = False
                # Check file name match
                if not search_query or search_query.lower() in file.lower():
                    match = True
                else:
                    # Check metadata match
                    meta_path = file_path + ".json"
                    if os.path.exists(meta_path):
                        try:
                            with open(meta_path, "r") as f:
                                metadata = json.load(f)
                            for key, value in metadata.items():
                                if isinstance(value, list):
                                    if any(search_query.lower() in str(v).lower() for v in value):
                                        match = True
                                        break
                                else:
                                    if search_query.lower() in str(value).lower():
                                        match = True
                                        break
                        except Exception as e:
                            print(f"[ERROR] Failed to read metadata for {file}: {e}")
                if match:
                    files.append(file)
        return files
    except Exception as e:
        print(f"[ERROR] Failed to search files in {folder_path}: {e}")
        return []

def delete_file(file_path):
    """
    Deletes a file and its associated metadata file.
    """
    try:
        print(f"Trying to delete: {file_path}")  # Log before deletion

        # Delete main file
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Deleted main file: {file_path}")
        else:
            print(f"Main file not found: {file_path}")

        # Delete metadata file if exists
        meta_path = file_path + ".json"
        if os.path.exists(meta_path):
            os.remove(meta_path)
            print(f"Deleted metadata: {meta_path}")
        else:
            print(f"Metadata file not found: {meta_path}")
    except Exception as e:
        print(f"[ERROR] Failed to delete file or metadata for {file_path}: {e}")
