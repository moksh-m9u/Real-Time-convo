import os
import sys
import time
import subprocess

def check_environment():
    """Check if all required environment variables are set"""
    required_env_vars = [
        "COHERE_API_KEY", 
        "GroqAPIKey", 
        "GEMINI_API_KEY",
        "HUGGINGFACE_API_TOKEN"
    ]
    
    missing_vars = []
    from dotenv import dotenv_values
    env_values = dotenv_values(".env")
    
    for var in required_env_vars:
        if var not in env_values or not env_values[var]:
            missing_vars.append(var)
    
    if missing_vars:
        print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
        print("Please add them to your .env file.")
        return False
    
    return True

def check_vectorstore():
    """Check if the vector store exists, initialize if not"""
    if not os.path.exists("vectorstore/db_faiss"):
        print("Vector store not found. Initializing...")
        try:
            import initialize_vectorstore
            initialize_vectorstore.create_vectorstore()
        except Exception as e:
            print(f"Error initializing vector store: {e}")
            return False
    
    return True

def check_data_directories():
    """Ensure all required data directories exist"""
    required_dirs = ["Data", "Frontend/Files", "medical_data", "vectorstore"]
    
    for directory in required_dirs:
        os.makedirs(directory, exist_ok=True)
    
    # Initialize Frontend/Files with empty data files if they don't exist
    files_dir = "Frontend/Files"
    required_files = ["Database.data", "Responses.data", "Status.data", "Mic.data", "TextInput.data"]
    
    for filename in required_files:
        filepath = os.path.join(files_dir, filename)
        if not os.path.exists(filepath):
            with open(filepath, "w") as f:
                f.write("")
    
    return True

def install_requirements():
    """Install required packages"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing requirements: {e}")
        return False

def main():
    """Main function to run the application"""
    print("Starting DocBot initialization...")
    
    # Check and install requirements
    print("Checking requirements...")
    if not install_requirements():
        return
    
    # Check environment variables
    print("Checking environment variables...")
    if not check_environment():
        return
    
    # Check data directories
    print("Checking data directories...")
    if not check_data_directories():
        return
    
    # Check vector store
    print("Checking vector store...")
    if not check_vectorstore():
        return
    
    # Start the application
    print("Starting DocBot application...")
    time.sleep(1)
    try:
        subprocess.call([sys.executable, "main.py"])
    except Exception as e:
        print(f"Error starting application: {e}")

if __name__ == "__main__":
    main() 