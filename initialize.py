"""
Initialization script for DocBot
This script ensures all necessary files and directories exist
"""

import os
import json

def initialize():
    """Initialize all required files and directories"""
    print("Initializing DocBot...")
    
    # Create directories
    directories = [
        "Data",
        "Frontend/Files",
        "medical_data",
        "vectorstore"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✓ Directory created/verified: {directory}")
    
    # Create empty files in Frontend/Files
    files = [
        "Database.data",
        "Responses.data",
        "Status.data",
        "Mic.data",
        "TextInput.data"
    ]
    
    for filename in files:
        filepath = os.path.join("Frontend", "Files", filename)
        with open(filepath, "w") as f:
            f.write("")
        print(f"✓ File created/verified: {filepath}")
    
    # Initialize ChatLog.json
    chatlog_path = os.path.join("Data", "ChatLog.json")
    with open(chatlog_path, "w") as f:
        json.dump([], f)
    print(f"✓ File created/verified: {chatlog_path}")
    
    # Initialize demographic.json
    demographic_path = os.path.join("Data", "demographic.json")
    with open(demographic_path, "w") as f:
        json.dump({
            "symptoms": [],
            "diagnosis": "",
            "recommendations": [],
            "avoid": [],
            "follow_up": ""
        }, f, indent=4)
    print(f"✓ File created/verified: {demographic_path}")
    
    print("Initialization complete!")

if __name__ == "__main__":
    initialize() 