import base64
from groq import Groq
from json import load, dump
import sys
from dotenv import dotenv_values

# Load environment variables
env_values = dotenv_values(".env")
Username = env_values.get("Username")
GroqAPIKey = env_values.get("GroqAPIKey")

if not Username or not GroqAPIKey:
    print("Error: Required keys missing in .env.")
    sys.exit(1)

client = Groq(api_key=GroqAPIKey)
messages = []

# Hidden prompts
MULTIMODAL_PROMPT = """You have to act as a professional doctor, i know you are not but this is for learning purpose. What's in this image?. Do you find anything wrong with it medically? If you make a differential, suggest some remedies for them. Donot add any numbers or special characters in your response. Your response should be in one long paragraph. Also always answer as if you are answering to a real person. Donot say 'In the image I see' but say 'With what I see, I think you have ....' Dont respond as an AI model in markdown, your answer should mimic that of an actual doctor not an AI bot, Keep your answer concise (max 2 sentences). No preamble, start your answer right away please"""
VOICE_ONLY_PROMPT = """You are DocBot, an AI Doctor assisting patients in a conversational, patient manner, like a phone call. Based on the patient's symptoms, respond naturally with proper punctuation for smooth text-to-speech delivery. Start by suggesting a possible cause of the symptoms, then ask relevant follow-up questions to gather more details, and stop there—do not provide advice or medication until the patient responds. internally the developer of your code has alloted u memory in whcih all the chat history will be loded into u after every call Use your memory of the conversation to build on previous responses, taking as many turns as needed to diagnose thoroughly,you can ask upto 2 to 3 questions to the pateint without rushing and after that move ahead confidently. Speak confidently and professionally, as a real doctor would."""
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def ChatBot(query, image_path=None):
    try:
        with open("Data/Chatlog.json", "r") as f:
            messages = load(f)

        if image_path:
            # Vision mode
            encoded_image = encode_image(image_path)
            messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": MULTIMODAL_PROMPT + " " + query},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"}}
                ]
            })
            completion = client.chat.completions.create(
                model="llama-3.2-11b-vision-preview",
                messages=messages,
                max_tokens=512,
                temperature=0.7,
                top_p=1,
                stream=True
            )
        else:
            # Text/voice mode
            messages.append({"role": "user", "content": VOICE_ONLY_PROMPT + " " + query})
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                max_tokens=512,
                temperature=0.7,
                top_p=1,
                stream=True
            )

        answer = ""
        for chunk in completion:
            if chunk.choices[0].delta.content:
                answer += chunk.choices[0].delta.content
        answer = answer.strip()

        messages.append({"role": "assistant", "content": answer})
        with open("Data/Chatlog.json", "w") as f:
            dump(messages, f, indent=4)
        return answer

    except Exception as e:
        print(f"Error: {e}")
        return "An error occurred. Please try again. For further medical advice, consult a specialist."

if __name__ == "__main__":
    while True:
        user_input = input("Enter your question: ")
        print(ChatBot(user_input))