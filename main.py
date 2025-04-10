import asyncio
from time import sleep
import threading
import json
import sys
import os
from dotenv import dotenv_values
from Frontend.GUI import (
    GraphicalUserInterface,
    SetAssistantStatus,
    ShowTextToScreen,
    TempDictonaryPath,
    SetMicrophoneStatus,
    AnswerModifier,
    QueryModifier,
    GetMicrophoneStatus,
    GetAssistantStatus,
    GetTextInput,  # Function for textbox
    SetTextInput   # For setting text input
)
from Backend.Model import FirstLayerDMM
from Backend.SpeechToText import SpeechRecognition
from Backend.Chatbot import ChatBot  # Now DocBot
from Backend.TextToSpeech import TTS
from PyQt5.QtCore import QTimer, QObject, pyqtSignal

# Load environment variables
env_vars = dotenv_values(".env")
username = env_vars.get("Username")
assistant_name = "DocBot"  # Fixed name for AI Doctor
default_message = f'''{username} : Hello, I am Moksh. I would like you to assist me with some health concerns.
{assistant_name} : Hello Moksh, I am you AI based doctor, i will give you a diagnosis in maximum of 3 coversation in which i will be asking your symptoms and things you have noticed. i will provide u a diagnosis along with some basic medication whcih you should be looking forward to take
'''

def initialize_json_files():
    """Initialize required JSON files with proper structure"""
    # Ensure Data directory exists
    os.makedirs("Data", exist_ok=True)
    
    # Initialize ChatLog.json to always start with just the initial welcome messages
    with open("Data/ChatLog.json", "w", encoding="utf-8") as f:
        json.dump([
            {
                "role": "user",
                "content": "Hello, I am Moksh. I would like you to assist me with some health concerns."
            },
            {
                "role": "assistant",
                "content": "Hello Moksh, I am you AI based doctor, i will give you a diagnosis in maximum of 3 coversation in which i will be asking your symptoms and things you have noticed. i will provide u a diagnosis along with some basic medication whcih you should be looking forward to take"
            }
        ], f, indent=4)
    
    # Always reset demographic.json to empty values at program start
    with open("Data/demographic.json", "w", encoding="utf-8") as f:
        json.dump({
            "symptoms": [],
            "diagnosis": "",
            "recommendations": [],
            "avoid": [],
            "follow_up": ""
        }, f, indent=4)
    
    # Create doctorsdata.json if it doesn't exist
    if not os.path.exists("Data/doctorsdata.json") or os.path.getsize("Data/doctorsdata.json") == 0:
        doctors = [
            {
                "id": 1,
                "name": "John Smith",
                "specialization": "General Physician",
                "specialties": ["flu", "fever", "cold", "cough", "general illness"],
                "experience": 12,
                "qualifications": ["MBBS", "MD"],
                "officeLocation": {"city": "New Delhi"},
                "workingHours": {"monday": {"start": "9:00", "end": "17:00"}}
            },
            {
                "id": 2,
                "name": "Sarah Johnson",
                "specialization": "Pulmonologist",
                "specialties": ["pneumonia", "asthma", "respiratory", "lung", "bronchitis"],
                "experience": 15,
                "qualifications": ["MBBS", "MD", "DM"],
                "officeLocation": {"city": "Mumbai"},
                "workingHours": {"monday": {"start": "10:00", "end": "18:00"}}
            },
            {
                "id": 3,
                "name": "Raj Patel",
                "specialization": "Cardiologist",
                "specialties": ["heart", "chest pain", "blood pressure", "cardiac"],
                "experience": 20,
                "qualifications": ["MBBS", "MD", "DM"],
                "officeLocation": {"city": "Bangalore"},
                "workingHours": {"monday": {"start": "8:00", "end": "16:00"}}
            },
            {
                "id": 4,
                "name": "Priya Sharma",
                "specialization": "ENT Specialist",
                "specialties": ["throat", "ear", "nose", "sinusitis", "tonsillitis"],
                "experience": 10,
                "qualifications": ["MBBS", "MS"],
                "officeLocation": {"city": "Hyderabad"},
                "workingHours": {"monday": {"start": "9:30", "end": "17:30"}}
            },
            {
                "id": 5,
                "name": "David Chen",
                "specialization": "Neurologist",
                "specialties": ["headache", "seizure", "migraine", "nerve pain", "tremor"],
                "experience": 18,
                "qualifications": ["MBBS", "MD", "DM"],
                "officeLocation": {"city": "Chennai"},
                "workingHours": {"monday": {"start": "8:30", "end": "16:30"}}
            },
            {
                "id": 6,
                "name": "Ananya Roy",
                "specialization": "Gastroenterologist",
                "specialties": ["abdominal pain", "acid reflux", "ulcer", "indigestion", "diarrhea"],
                "experience": 14,
                "qualifications": ["MBBS", "MD", "DM"],
                "officeLocation": {"city": "Kolkata"},
                "workingHours": {"monday": {"start": "9:00", "end": "17:00"}}
            },
            {
                "id": 7,
                "name": "Michael Wong",
                "specialization": "Dermatologist",
                "specialties": ["rash", "eczema", "acne", "skin infection", "psoriasis"],
                "experience": 16,
                "qualifications": ["MBBS", "MD"],
                "officeLocation": {"city": "Pune"},
                "workingHours": {"monday": {"start": "10:00", "end": "18:00"}}
            },
            {
                "id": 8,
                "name": "Aisha Khan",
                "specialization": "General Physician",
                "specialties": ["fever", "flu", "cold", "fatigue", "general checkup"],
                "experience": 10,
                "qualifications": ["MBBS", "MD"],
                "officeLocation": {"city": "Jaipur"},
                "workingHours": {"monday": {"start": "9:00", "end": "17:00"}}
            }
        ]
        with open("Data/doctorsdata.json", "w", encoding="utf-8") as f:
            json.dump(doctors, f, indent=4)

def show_default_chat_if_no_chats():
    """Update the display with the default welcome messages"""
    with open(TempDictonaryPath("Database.data"), "w", encoding="utf-8") as db_file:
        db_file.write("")
    with open(TempDictonaryPath("Responses.data"), "w", encoding="utf-8") as response_file:
        # Use the welcome messages that are already in ChatLog.json
        response_file.write(default_message)

def read_chat_log_json():
    with open(r"Data\ChatLog.json", "r", encoding="utf-8") as file:
        chatlog_data = json.load(file)
    return chatlog_data

def integrate_chat_log():
    json_data = read_chat_log_json()
    formatted_chatlog = ""
    for entry in json_data:
        if entry["role"] == "user":
            formatted_chatlog += f"User: {entry['content']}\n"
        elif entry["role"] == "assistant":
            formatted_chatlog += f"Assistant: {entry['content']}\n"
    formatted_chatlog = formatted_chatlog.replace("User", f"{username} ")
    formatted_chatlog = formatted_chatlog.replace("Assistant", f"{assistant_name} ")
    with open(TempDictonaryPath("Database.data"), "w", encoding="utf-8") as file:
        file.write(AnswerModifier(formatted_chatlog))

def show_chats_on_gui():
    with open(TempDictonaryPath("Database.data"), "r", encoding="utf-8") as file:
        data = file.read()
    if len(str(data)) > 0:
        lines = data.split("\n")
        result = '\n'.join(lines)
        with open(TempDictonaryPath("Responses.data"), "w", encoding="utf-8") as response_file:
            response_file.write(result)

def initial_execution():
    # Initialize JSON files first
    initialize_json_files()
    
    SetMicrophoneStatus("False")
    ShowTextToScreen("")
    
    # Now that ChatLog.json always has content, we can directly integrate and show
    integrate_chat_log()
    show_chats_on_gui()

async def main_execution():
    # Check for text input from GUI first
    text_query = GetTextInput()
    if text_query:
        query = text_query
        SetAssistantStatus("Thinking...")
        SetTextInput("None")
    else:
        SetAssistantStatus("Listening...")
        query = SpeechRecognition()
        ShowTextToScreen(f"{username} : {query}")
        SetAssistantStatus("Thinking...")

    # Special handling for greeting messages with symptoms to fix first message issue
    if "hi doctor" in query.lower() or "hello doctor" in query.lower():
        # Check for key symptoms in the message
        common_symptoms = ["fever", "cough", "cold", "headache", "pain", "nausea", 
                          "sore throat", "runny nose", "congestion"]
        
        # If symptoms are found in the greeting, make sure to process with symptom command
        for symptom in common_symptoms:
            if symptom in query.lower():
                # Force process as symptom
                print(f"Detected symptom '{symptom}' in greeting - forcing symptom handling")
                decision = ["symptom " + query]
                break
        else:
            # Normal decision if no symptoms found
            decision = FirstLayerDMM(query)
    else:
        # Normal processing for non-greeting messages
        decision = FirstLayerDMM(query)
        
    print(f"Decision: {decision}")

    for command in decision:
        if "symptom " in command:
            SetAssistantStatus("Thinking...")
            final_query = command.replace("symptom ", "")
            answer = ChatBot(QueryModifier(final_query))  # Text/voice mode
            ShowTextToScreen(f"{assistant_name} : {answer}")
            SetAssistantStatus("Answering...")
            await TTS(answer)
            return True
        elif "exit" in command:
            final_query = "Goodbye, take care!"
            answer = ChatBot(QueryModifier(final_query))
            ShowTextToScreen(f"{assistant_name} : {answer}")
            SetAssistantStatus("Answering...")
            await TTS(answer)
            os._exit(1)

class AsyncWorker(QObject):
    finished = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
    def run(self):
        self.loop.run_until_complete(self.run_main_execution())
        self.finished.emit()
        
    async def run_main_execution(self):
        while True:
            current_status = GetMicrophoneStatus()
            text_input_exists = GetTextInput()
            
            if current_status == "True" or text_input_exists:
                await main_execution()
            else:
                ai_status = GetAssistantStatus()
                if "Available..." in ai_status:
                    await asyncio.sleep(0.1)
                else:
                    SetAssistantStatus("Available...")

def main():
    initial_execution()
    
    # Create a worker thread for async operations
    worker = AsyncWorker()
    worker_thread = threading.Thread(target=worker.run, daemon=True)
    worker_thread.start()
    
    # Start the GUI
    GraphicalUserInterface()

if __name__ == "__main__":
    main()