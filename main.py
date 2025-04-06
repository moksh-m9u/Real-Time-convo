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
    GetTextInput  # New function for textbox
)
from Backend.Model import FirstLayerDMM
from Backend.SpeechToText import SpeechRecognition
from Backend.Chatbot import ChatBot  # Now DocBot
from Backend.TextToSpeech import TTS

# Load environment variables
env_vars = dotenv_values(".env")
username = env_vars.get("Username")
assistant_name = "DocBot"  # Fixed name for AI Doctor
default_message = f'''{username} : Hello {assistant_name}! How can I assist you today?
{assistant_name} : Hello {username}, I'm here to help with your medical concerns. What’s on your mind?
'''

def show_default_chat_if_no_chats():
    with open(r"Data\ChatLog.json", "r", encoding="utf-8") as file:
        if len(file.read()) < 5:
            with open(TempDictonaryPath("Database.data"), "w", encoding="utf-8") as db_file:
                db_file.write("")
            with open(TempDictonaryPath("Responses.data"), "w", encoding="utf-8") as response_file:
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
    SetMicrophoneStatus("False")
    ShowTextToScreen("")
    show_default_chat_if_no_chats()
    integrate_chat_log()
    show_chats_on_gui()

initial_execution()

async def main_execution():
    vision_execution = False
    image_path = None

    # Check for text input from GUI first
    text_query = GetTextInput()
    if text_query:
        query = text_query
        SetAssistantStatus("Thinking...")
    else:
        SetAssistantStatus("Listening...")
        query = SpeechRecognition()
        ShowTextToScreen(f"{username} : {query}")
        SetAssistantStatus("Thinking...")

    # Check for image input
    with open(r"Frontend\Files\ImageUpload.data", "r") as f:
        image_data = f.read().strip()
        if image_data and image_data != "None":
            image_path = image_data
            vision_execution = True

    decision = FirstLayerDMM(query)
    print(f"Decision: {decision}")

    if vision_execution:
        SetAssistantStatus("Analyzing...")
        answer = ChatBot(query, image_path=image_path)  # Vision mode
        ShowTextToScreen(f"{assistant_name} : {answer}")
        SetAssistantStatus("Answering...")
        await TTS(answer)
        with open(r"Frontend\Files\ImageUpload.data", "w") as f:
            f.write("None")  # Reset image path
    else:
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

async def first_thread():
    while True:
        current_status = GetMicrophoneStatus()
        if current_status == "True" or GetTextInput():  # Check text input too
            await main_execution()
        else:
            ai_status = GetAssistantStatus()
            if "Available..." in ai_status:
                sleep(0.1)
            else:
                SetAssistantStatus("Available...")

def second_thread():
    GraphicalUserInterface()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    thread1 = threading.Thread(target=lambda: loop.run_until_complete(first_thread()), daemon=True)
    thread1.start()
    second_thread()