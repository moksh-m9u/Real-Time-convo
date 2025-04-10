# DocBot - AI Medical Assistant

DocBot is an AI-powered medical assistant that combines conversational AI with knowledge retrieval to provide more accurate medical information and diagnoses.

## Features

- **Conversational Medical Assistant**: Speaks naturally like a real doctor
- **RAG (Retrieval-Augmented Generation)**: Uses medical knowledge to inform responses
- **Image Analysis**: Analyzes medical images for potential issues
- **Symptom Tracking**: Automatically extracts and tracks patient symptoms
- **AI Diagnosis**: Provides preliminary diagnoses based on symptoms and medical knowledge
- **Treatment Recommendations**: Suggests potential treatments and things to avoid
- **Modern UI**: Clean, intuitive interface with patient diagnosis panel

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Create a `.env` file with your API keys:
   ```
   COHERE_API_KEY=your_cohere_key
   Username=YourName
   Assistantname=DocBot
   GroqAPIKey=your_groq_key
   GEMINI_API_KEY=your_gemini_key
   InputLanguage=en
   Assistantvoice=en-IE-EmilyNeural
   HUGGINGFACE_API_TOKEN=your_huggingface_token
   ```

3. Run the application using the simplified run script:
   ```
   python run.py
   ```

   This script will:
   - Install required dependencies
   - Check if all environment variables are properly set
   - Create necessary directories
   - Initialize the vector store for RAG if it doesn't exist
   - Start the DocBot application

   Alternatively, you can run just the main application directly:
   ```
   python main.py
   ```

## How It Works

1. **Initial Conversation**: DocBot will ask questions about your symptoms
2. **Knowledge Retrieval**: After 2-3 exchanges, DocBot analyzes the conversation to extract symptoms
3. **Medical Research**: The system uses RAG to search for relevant medical information
4. **Diagnosis Generation**: Based on symptoms and retrieved information, DocBot formulates a diagnosis
5. **Treatment Recommendations**: DocBot provides treatment recommendations and things to avoid
6. **Diagnosis Display**: The diagnosis panel shows a summary of the medical consultation

## Components

- **Conversational AI**: Uses Groq's advanced LLMs for natural conversation
- **Knowledge Retrieval**: Uses RAG to query a medical knowledge base
- **Symptom Analysis**: Uses Google's Gemini to extract symptoms and formulate queries
- **Image Analysis**: Uses multimodal capabilities to analyze medical images

## Troubleshooting

If you encounter any issues:

1. Make sure all API keys in your `.env` file are valid
2. Run `python initialize_vectorstore.py` to rebuild the vector store
3. Check the `Frontend/Files` directory exists with all necessary data files
4. Ensure you have all required Python packages installed

## Notes

- This application is for educational purposes only and not intended to replace professional medical advice
- Always consult with a qualified healthcare provider for medical concerns