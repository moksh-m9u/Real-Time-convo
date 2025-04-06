# Live_session
 
# Setup Instructions
Follow these steps to set up Doctor AI on your device:

## 1. Clone the Repository
Clone the project from GitHub to your local machine:

```bash
git clone https://github.com/moksh-m9u/Live_session.git
```
## 2. install requirements

Install the required Python packages listed in requirements.txt:
```bash
pip install -r requirements.txt
```

## 3. Create a File in the Main Directory Named .env

COHERE_API_KEY= 
Username=
Assistantname=DocBot
GroqAPIKey=
InputLanguage=en
Assistantvoice=en-IE-EmilyNeural
alternate_good_voice=en-CA-LiamNeural
 <br />
After creating this .env file, generate API keys from Cohere and Groq, and enter them in the .env file.
Save the .env file in the DoctorAI/ directory.

4. Running the Application
Start the application by running:

```bash
python main.py
```