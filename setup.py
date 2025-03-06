import os
import json

def initialize_data_directory():
    """
    Create the data directory and initialize default JSON files if they don't exist.
    This is a utility script for first-time setup.
    """
    data_folder = "data"
    
    # Create data folder if it doesn't exist
    if not os.path.exists(data_folder):
        os.makedirs(data_folder)
        print(f"Created {data_folder} directory")
    
    # Initialize default files
    files_to_create = {
        "trends.json": {
            "active_trend": None,
            "past_trends": [],
            "submissions": {}
        },
        "users.json": {
            "users": {}
        },
        "competitions.json": {
            "active_competition": None,
            "past_competitions": [],
            "votes": {}
        }
    }
    
    for filename, default_data in files_to_create.items():
        file_path = os.path.join(data_folder, filename)
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                json.dump(default_data, f, indent=4)
            print(f"Created default {filename}")
        else:
            print(f"{filename} already exists")

if __name__ == "__main__":
    initialize_data_directory()
    print("Setup complete. Data directory and files are ready.")
