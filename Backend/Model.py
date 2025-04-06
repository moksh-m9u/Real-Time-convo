import cohere
from rich import print
import time

co = cohere.ClientV2("1t6dVGVJBcDYPn3ai4brm5G5K7aFWvxuBZ9M0CVG")

preamble = """
You are a Decision-Making Model for an AI Doctor. Decide whether a query is a symptom description or requires image analysis.
-> Respond with 'symptom (query)' for text/voice-based symptom descriptions (e.g., 'I have a cough' -> 'symptom I have a cough').
-> Respond with 'vision (query)' if the query involves an image (e.g., 'Analyze this blister' -> 'vision Analyze this blister').
-> Respond with 'exit' if the user says goodbye or wants to end the conversation (e.g., 'bye' -> 'exit').
-> Respond with 'symptom (query)' for any unclear or unclassified query.
"""

def FirstLayerDMM(prompt: str = "test"):
    conversation = [{"role": "system", "content": preamble}, {"role": "user", "content": prompt}]
    stream = co.chat_stream(
        model='command-r-plus',
        messages=conversation,
        temperature=0.7
    )
    response = ""
    for event in stream:
        if event.type == "content-delta":
            response += event.delta.message.content.text
    response = response.replace("\n", " ").strip()
    parts = [part.strip() for part in response.split(",") if part.strip()]
    if "(query)" in response:
        time.sleep(0.5)
        return FirstLayerDMM(prompt=prompt)
    return parts

if __name__ == "__main__":
    while True:
        user_input = input(">>> ")
        print(FirstLayerDMM(user_input))