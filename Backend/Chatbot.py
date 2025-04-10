import base64
from groq import Groq
from json import load, dump, loads
import sys
from dotenv import dotenv_values
import os
import json
import google.generativeai as genai
import re
import traceback

# Load environment variables
env_values = dotenv_values(".env")
Username = env_values.get("Username")
GroqAPIKey = env_values.get("GroqAPIKey")
GEMINI_API_KEY = env_values.get("GEMINI_API_KEY")

if not Username or not GroqAPIKey:
    print("Error: Required Groq keys missing in .env.")
    sys.exit(1)
    
# Check for Gemini API Key
if not GEMINI_API_KEY:
    print("Warning: GEMINI_API_KEY not found in .env. Symptom formatting will be basic.")
    # Optionally, set a flag to disable Gemini features or use a placeholder key if applicable
    # For now, we'll allow the script to continue but Gemini calls will fail later
else:
    try:
        # Initialize Gemini only if the key exists
        genai.configure(api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"Error configuring Gemini: {e}. Symptom formatting might be basic.")
        GEMINI_API_KEY = None # Disable Gemini if configuration fails

client = Groq(api_key=GroqAPIKey)
messages = []

# RAG integration - using both original and simplified versions
try:
    from connect_memory_to_llm import Rag as LangChainRag
    print("Successfully loaded LangChain RAG system")
    use_langchain_rag = True
except Exception as e:
    print(f"Warning: Could not load LangChain RAG system: {e}")
    print("Falling back to simplified RAG implementation")
    use_langchain_rag = False

# Import everything we need from the simplified RAG system
from connect_memory_to_llm_simple import (
    Rag as SimpleRag, 
    extract_symptoms_from_query, 
    find_matching_combination, 
    SYMPTOM_COMBINATIONS, 
    MEDICAL_DATA
)

# Initialize patient data
if not os.path.exists("Data/demographic.json"):
    with open("Data/demographic.json", "w") as f:
        json.dump({
            "symptoms": [],
            "diagnosis": "",
            "recommendations": [],
            "avoid": [],
            "follow_up": "",
            "recommended_specialist_type": "General Physician"
        }, f, indent=4)

# Hidden prompts
MULTIMODAL_PROMPT = """You have to act as a professional doctor, i know you are not but this is for learning purpose. What's in this image?. Do you find anything wrong with it medically? If you make a differential, suggest some remedies for them. Donot add any numbers or special characters in your response. Your response should be in one long paragraph. Also always answer as if you are answering to a real person. Donot say 'In the image I see' but say 'With what I see, I think you have ....' Dont respond as an AI model in markdown, your answer should mimic that of an actual doctor not an AI bot, Keep your answer concise (max 2 sentences). No preamble, start your answer right away please"""
VOICE_ONLY_PROMPT = """You are DocBot, an AI Doctor assisting patients in a conversational, patient manner. Based on the patient's symptoms, respond naturally with proper punctuation and NO formatting - NO asterisks, NO markdown symbols, NO bold text, NO italics.

Start by suggesting a possible cause of the symptoms, then ask relevant follow-up questions to gather more details, and stop there—do not provide advice or medication until the patient responds. 

Use your memory of the conversation to build on previous responses, taking as many turns as needed to diagnose thoroughly. You can ask up to 2 to 3 questions to the patient without rushing.

After gathering sufficient symptoms (generally 3-4 symptoms), ask if the patient would like you to conclude with a diagnosis and recommendations. If they agree, provide a clear, concise diagnosis along with recommendations. 

For recommendations, always format them in clear sections with simple dashes (-) for bullet points:
- Diagnosis: (clear, professional medical term for their condition)
- Recommendations: (list practical steps for treatment with dashes)
- Avoid: (list things to avoid with dashes)
- Follow-up: (when they should seek further medical care)

IMPORTANT: Never use asterisks (*), never use bold formatting, never use markdown symbols in your response. Use clear, direct language as a medical professional would. Speak confidently and professionally, as a real doctor would."""

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def get_conversation_count():
    """Count the number of user messages in the chat history"""
    try:
        with open("Data/Chatlog.json", "r") as f:
            messages = load(f)
            return sum(1 for msg in messages if msg["role"] == "user")
    except:
        return 0

def extract_symptoms_from_chat(messages):
    """Extract symptoms from the chat history more accurately"""
    # Join all user messages to analyze
    user_text = ""
    first_message_found = False
    
    for msg in messages:
        if msg["role"] == "user":
            # Extract actual user input from prompt
            content = msg["content"]
            
            # Special handling for first message - often has greeting with symptoms
            if not first_message_found:
                first_message_found = True
                # Check for common first message pattern like "Hi doctor I am having fever and cough"
                if "hi doctor" in content.lower() or "hello doctor" in content.lower():
                    # Try to extract symptoms from greeting-style first message
                    having_match = re.search(r'(?:i am|i\'m) having ([^\.]+)', content.lower())
                    if having_match:
                        symptom_text = having_match.group(1).strip()
                        # Further process to split combined symptoms
                        if "and" in symptom_text or "," in symptom_text:
                            parts = re.split(r',|\sand\s', symptom_text)
                            for part in parts:
                                specific_part = part.strip()
                                if specific_part and len(specific_part) > 3:
                                    user_text += f"I have {specific_part}. "
                        else:
                            user_text += f"I have {symptom_text}. "
            
            # Try to find just the user's actual symptoms by removing system instructions
            parts = content.split("Now, respond to the patient's latest query:")
            if len(parts) > 1:
                user_text += parts[1].strip() + " "
            else:
                # Find the actual query after the instructions
                match = re.search(r'real doctor would\.\s*(.*?)$', content, re.DOTALL)
                if match:
                    user_text += match.group(1).strip() + " "
                else:
                    # If no special processing was done above, add content normally
                    if not (first_message_found and "hi doctor" in content.lower()):
                        user_text += content + " "
    
    # Look for common symptom patterns
    symptoms = []
    
    # Pattern matching for symptoms
    symptom_patterns = [
        r'(pain|ache|discomfort) (in|on) (?:my|the) ([a-z\s]+)',  # pain in my abdomen
        r'([a-z\s]+) (pain|ache|discomfort)',  # abdominal pain
        r'(?:I have|I\'m having|experiencing|having|with) ([a-z\s]+)',  # I have fever
        r'(dark|cloudy|pink|red|clear) (urine|pee|urination)',  # dark urine
        r'(difficulty|trouble|problem) (with|in) ([a-z\s]+)',  # difficulty in breathing
        r'(fever|cough|headache|nausea|vomiting|dizziness|fatigue|cold|sore throat|runny nose|congestion|chills)',  # direct symptoms - added more terms
        r'(?:my|the) ([a-z\s]+) (?:is|are) ([a-z\s]+)',  # my urine is pink
        r'(?:been having|suffering from|troubled with) ([a-z\s]+)',  # been having fever
        r'(?:since|for) (?:last|past|about)? ?(\d+) (days?|weeks?|months?)', # time-based context for symptoms
    ]
    
    for pattern in symptom_patterns:
        matches = re.finditer(pattern, user_text.lower())
        for match in matches:
            if match.group():
                symptom = match.group().strip()
                # Clean up the symptom text
                symptom = re.sub(r'i have |i\'m having |experiencing |having |with ', '', symptom)
                # Format specific types of symptoms better
                if "pain in " in symptom:
                    parts = symptom.split("pain in ")
                    if len(parts) > 1:
                        symptom = f"{parts[1].strip()} pain"
                
                if symptom and symptom not in symptoms:
                    symptoms.append(symptom)
    
    # Do additional checks for specific symptoms
    if "urine" in user_text.lower() or "urination" in user_text.lower():
        if "pink" in user_text.lower() and "pink urine" not in symptoms:
            symptoms.append("pink urine")
        if "dark" in user_text.lower() and "dark urine" not in symptoms:
            symptoms.append("dark urine")
        if "pain" in user_text.lower() and "painful urination" not in symptoms:
            symptoms.append("painful urination")
    
    if "abdomen" in user_text.lower() and "pain" in user_text.lower():
        if "abdominal pain" not in symptoms:
            symptoms.append("abdominal pain")
    
    # Clean up symptoms
    cleaned_symptoms = []
    for symptom in symptoms:
        # Remove duplicates and refine wording
        clean_symptom = symptom.strip().lower()
        
        # Process compound symptoms like "fever and cough"
        if " and " in clean_symptom:
            parts = clean_symptom.split(" and ")
            for part in parts:
                part = part.strip()
                if part and len(part) > 2 and not any(s == part for s in cleaned_symptoms):
                    cleaned_symptoms.append(part)
        # Check if symptom contains multiple symptoms separated by commas
        elif "," in clean_symptom:
            parts = clean_symptom.split(",")
            for part in parts:
                part = part.strip()
                if part and len(part) > 2 and not any(s == part for s in cleaned_symptoms):
                    cleaned_symptoms.append(part)
        # Handle single symptom
        elif clean_symptom and not any(s == clean_symptom for s in cleaned_symptoms):
            cleaned_symptoms.append(clean_symptom)
    
    return cleaned_symptoms

def format_symptoms_with_gemini(symptoms):
    """Use Gemini to clean and format the symptoms into clear bullet points with both common and medical terms."""
    if not symptoms or len(symptoms) == 0:
        return []
    
    # Fallback formatting if Gemini is not available or fails
    def basic_formatting(symptom_list):
        return [symptom[0].upper() + symptom[1:] if symptom else "" for symptom in symptom_list]

    if not GEMINI_API_KEY:
        print("Gemini API Key not available. Using basic symptom formatting.")
        return basic_formatting(symptoms)
        
    try:
        # Format the prompt for Gemini
        prompt = f"""Given these raw patient symptoms extracted from conversation: {', '.join(symptoms)}
        
        Please reformat these into clear, understandable bullet points using BOTH common and medical terminology.
        
        Format each symptom as: "Common name (Medical term)" - for example "Headache (Cephalalgia)" or "Fever (Pyrexia)"
        If there is no specific medical term, just use the common name.
        
        Return ONLY the bullet points, one per line, without explanations or additional text.
        Please ensure the common name comes first, followed by the medical term in parentheses.
        
        Example Input: ['i feel feverish', 'coughing a lot', 'my throat hurts']
        Example Output:
        • Fever (Pyrexia)
        • Persistent cough (Tussis)
        • Sore throat (Pharyngitis)
        """
        
        # Configure Gemini model parameters
        generation_config = {
            "temperature": 0.2, # Slightly lower temperature for more focused output
            "top_p": 0.95,
            "top_k": 0,
            "max_output_tokens": 1024,
        }
        
        # Get Gemini's response
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash", # Use a cost-effective and fast model
            generation_config=generation_config
        )
        
        response = model.generate_content(prompt)
        
        # Parse the response to extract bullet points
        formatted_text = response.text
        bullet_points = []
        
        # Extract each bullet point
        for line in formatted_text.split('\n'):
            line = line.strip()
            if line and line.startswith('•'):
                # Clean up the bullet point text
                clean_point = line.lstrip('• ').strip()
                if clean_point:
                    bullet_points.append(clean_point)
            elif line and not line.startswith('Example'): # Handle cases where Gemini might not use bullets but gives points
                 clean_point = line.strip()
                 if clean_point and len(clean_point) > 3: # Basic check for valid point
                     bullet_points.append(clean_point)

        # If Gemini didn't return proper bullet points, use basic formatting
        if not bullet_points:
            print("Gemini did not return expected bullet points. Using basic formatting.")
            return basic_formatting(symptoms)
        
        return bullet_points
        
    except Exception as e:
        print(f"Error formatting symptoms with Gemini: {e}. Using basic formatting.")
        traceback.print_exc() # Print detailed traceback for debugging
        # Fall back to basic formatting if Gemini fails
        return basic_formatting(symptoms)

def generate_rag_query(symptoms):
    """Generate a comprehensive query for the RAG system based on symptoms"""
    if not symptoms:
        return "Common cold symptoms and treatment"
    
    # Create a more detailed query based on the number of symptoms
    if len(symptoms) == 1:
        return f"{symptoms[0]}: causes, diagnosis, treatment, complications, prevention"
    
    # For multiple symptoms, generate a more specific query
    symptoms_text = ", ".join(symptoms[:5])  # Limit to first 5 symptoms to keep query focused
    
    # Format query based on symptom count
    if len(symptoms) <= 3:
        return f"Patient with {symptoms_text}. What conditions cause these symptoms? Diagnosis and treatment?"
    else:
        # For many symptoms, be more specific about potential serious conditions
        return f"Patient presenting with {symptoms_text}. Differential diagnosis including serious conditions. Treatment recommendations."

def update_demographic_file(symptoms, diagnosis_info):
    """Update the demographic.json file with patient information"""
    if not symptoms or not diagnosis_info:
        return
        
    try:
        with open("Data/demographic.json", "w") as f:
            json.dump({
                "symptoms": symptoms,
                "diagnosis": diagnosis_info.get("diagnosis", "Unknown"),
                "recommendations": diagnosis_info.get("recommendations", []),
                "avoid": diagnosis_info.get("avoid", []),
                "follow_up": diagnosis_info.get("follow_up", "")
            }, f, indent=4)
    except Exception as e:
        print(f"Error updating demographic file: {e}")

def format_diagnosis_for_display(diagnosis_info):
    """Format the diagnosis info for display in the chat"""
    if not diagnosis_info:
        return "No diagnosis available at this time."
    
    # Format each section
    diagnosis = diagnosis_info.get('diagnosis', 'Unknown')
    
    # Handle recommendations
    recommendations = diagnosis_info.get('recommendations', [])
    if recommendations:
        rec_text = "\nRecommendations:\n" + "\n".join(f"- {r}" for r in recommendations if r)
    else:
        rec_text = "\nRecommendations: None available at this time."
    
    # Handle things to avoid
    avoid_items = diagnosis_info.get('avoid', [])
    if avoid_items:
        avoid_text = "\nPlease avoid:\n" + "\n".join(f"- {a}" for a in avoid_items if a)
    else:
        avoid_text = "\nAvoid: No specific items to avoid at this time."
    
    # Handle follow-up
    follow_up = diagnosis_info.get('follow_up', '')
    if follow_up:
        follow_up_text = f"\nFollow-up: {follow_up}"
    else:
        follow_up_text = "\nFollow-up: Consult with a healthcare professional if symptoms persist or worsen."
    
    # Build the complete message
    message = f"Based on your symptoms, I believe you may have: {diagnosis}"
    message += rec_text
    message += avoid_text
    message += follow_up_text
    message += "\n\nNote: This is an AI-assisted diagnosis. Please consult with a healthcare professional for a definitive diagnosis."
    
    return message

def Rag(query):
    """Combined RAG function that tries LangChain RAG first, then falls back to simplified version"""
    try:
        if use_langchain_rag:
            # Try using the full LangChain RAG system first
            return LangChainRag(query)
        else:
            # Fall back to the simplified version
            return SimpleRag(query)
    except Exception as e:
        print(f"Error in combined RAG function: {e}")
        # Always fall back to simplified version if anything fails
        try:
            return SimpleRag(query)
        except Exception as e2:
            print(f"Error in fallback RAG function: {e2}")
            return "Unable to retrieve medical information at this time."

def ChatBot(Query, image_path=None):
    """Chat bot function with improved demographic tracking"""
    try:
        # Load the chat history
        with open("Data/ChatLog.json", "r", encoding="utf-8") as f:
            messages = json.load(f)
        
        # Add the new user message
        messages.append({"role": "user", "content": Query})
        
        # Get a response from the API
        if image_path:
            # For image processing, we'll use encoded image
            encoded_image = encode_image(image_path)
            
            # Since Groq has limited vision capabilities, we'll use LLaMA 3 vision model
            completion = client.chat.completions.create(
                model="llama-3.2-11b-vision-preview",  # Groq's vision model
                messages=[
                    {"role": "system", "content": "You are DocBot, an AI Doctor assisting patients. Do not use any markdown formatting like asterisks, bold, or italics in your responses."},
                    *[{"role": m["role"], "content": m["content"]} for m in messages[:-1]],
                    {
                        "role": "user", 
                        "content": [
                            {"type": "text", "text": MULTIMODAL_PROMPT + " " + Query},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"}}
                        ]
                    }
                ],
                max_tokens=512,
                temperature=0.7,
                top_p=1,
                stream=True
            )
            
            # Stream the response
            answer = ""
            for chunk in completion:
                if chunk.choices[0].delta.content:
                    answer += chunk.choices[0].delta.content
        else:
            # Process without image - use Groq's LLaMA model
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",  # Use Groq's powerful LLaMA model
                messages=[
                    {"role": "system", "content": "You are DocBot, an AI Doctor assisting patients. Do not use any markdown formatting like asterisks, bold, or italics in your responses."},
                    *[{"role": m["role"], "content": m["content"]} for m in messages],
                ],
                max_tokens=512,
                temperature=0.7,
                top_p=1,
                stream=True
            )
            
            # Stream the response
            answer = ""
            for chunk in completion:
                if chunk.choices[0].delta.content:
                    answer += chunk.choices[0].delta.content
        
        # Clean up the answer - remove all asterisks, markdown formatting
        answer = answer.strip()
        answer = re.sub(r'\*+', '', answer)  # Remove all asterisks
        answer = re.sub(r'#+\s+', '', answer)  # Remove markdown headers
        answer = re.sub(r'\n\s*-\s+', '\n- ', answer)  # Standardize bullet points
        
        # Add the assistant's response to the chat history
        messages.append({"role": "assistant", "content": answer})
        
        # Save the updated chat history
        with open("Data/ChatLog.json", "w", encoding="utf-8") as f:
            json.dump(messages, f, indent=4)
        
        # Update demographic information
        update_demographic_from_chat(messages)
        
        return answer
    
    except Exception as e:
        print(f"Error in ChatBot: {str(e)}")
        return f"I apologize, but I encountered an error: {str(e)}"

def update_demographic_from_chat(messages):
    """Update demographic.json with information extracted from the chat"""
    try:
        # Extract symptoms from the chat
        raw_symptoms = extract_symptoms_from_chat(messages)
        
        # Use Gemini to format the symptoms nicely
        symptoms = format_symptoms_with_gemini(raw_symptoms)
        
        # Ensure demographic.json exists with default structure
        if not os.path.exists("Data/demographic.json"):
            with open("Data/demographic.json", "w", encoding="utf-8") as f:
                json.dump({
                    "symptoms": [],
                    "diagnosis": "",
                    "recommendations": [],
                    "avoid": [],
                    "follow_up": "",
                    "recommended_specialist_type": "General Physician"
                }, f, indent=4)
        
        # Load current demographic data
        with open("Data/demographic.json", "r", encoding="utf-8") as f:
            demographic = json.load(f)
        
        # Update symptoms (add new ones, don't duplicate)
        # Only update if new formatted symptoms are different or demographic file was empty
        if symptoms and (not demographic.get("symptoms") or set(symptoms) != set(demographic.get("symptoms", []))):
            demographic["symptoms"] = symptoms  # Replace with cleaned and formatted symptoms
            print(f"Updated demographic symptoms: {symptoms}") # Debug print
            
            # Get a precise diagnosis from our simplified RAG system using the updated symptoms
            precise_diagnosis = get_precise_diagnosis_from_rag(symptoms)
            demographic["diagnosis"] = precise_diagnosis
            print(f"Updated diagnosis from RAG: {precise_diagnosis}")
        elif not symptoms and demographic.get("symptoms"): # If Gemini fails but we had symptoms before, keep old ones
            pass # Keep existing symptoms
        else: # If symptoms haven't changed or Gemini returned empty
             print("Symptoms unchanged or empty, not updating.")
        
        # Check for recommendations in the latest assistant message
        last_assistant_msg = None
        for msg in reversed(messages):
            if msg["role"] == "assistant":
                last_assistant_msg = msg["content"]
                break
        
        if last_assistant_msg:
            # Remove asterisks from the message
            last_assistant_msg = last_assistant_msg.replace("*", "")
            
            # Look for recommendations with improved patterns
            recommendations = []
            recommendation_patterns = [
                r"Recommendations?:?\s*(.*?)(?:Avoid|Follow-up|When to see|$)",
                r"(?:I recommend|You should|It's advisable to|Consider)\s+([^\.]+)",
                r"Treatment(?:\s+includes|\s+options)?:?\s*(.*?)(?:Avoid|Follow-up|When to see|$)"
            ]
            
            for pattern in recommendation_patterns:
                matches = re.finditer(pattern, last_assistant_msg, re.DOTALL | re.IGNORECASE)
                for match in matches:
                    if match.groups():
                        rec_text = match.group(1).strip()
                        # Split by bullet points or new lines with dashes
                        bullet_points = re.findall(r"[-•]([^-•]+)", rec_text)
                        if bullet_points:
                            for point in bullet_points:
                                point = point.strip()
                                if point and point not in recommendations and len(point) > 5:
                                    recommendations.append(point.capitalize())
                        else:
                            # Try to split by sentences if no bullet points
                            sentences = re.split(r'\.(?=\s|$)', rec_text)
                            for sentence in sentences:
                                sentence = sentence.strip()
                                if sentence and len(sentence) > 10:  # Avoid very short sentences
                                    recommendations.append(sentence.capitalize())
            
            # If no recommendations found, add common recommendations based on diagnosis
            if not recommendations and demographic["diagnosis"]:
                diagnosis = demographic["diagnosis"].lower()
                if "urinary tract infection" in diagnosis or "uti" in diagnosis:
                    recommendations = [
                        "Drink plenty of water to help flush out bacteria",
                        "Take antibiotics as prescribed by your doctor",
                        "Consider taking over-the-counter pain relievers like ibuprofen for pain"
                    ]
                elif "flu" in diagnosis or "cold" in diagnosis or "viral" in diagnosis:
                    recommendations = [
                        "Get plenty of rest to help your body recover",
                        "Drink fluids to stay hydrated",
                        "Take over-the-counter medications to reduce fever and alleviate symptoms"
                    ]
            
            # Update recommendations if found
            # Decision: Always try to get refined recommendations if diagnosis is present
            current_diagnosis_for_recs = demographic.get("diagnosis", "")
            if current_diagnosis_for_recs and current_diagnosis_for_recs.lower() != "unknown":
                print(f"Diagnosis '{current_diagnosis_for_recs}' found, reformatting recommendations for better presentation.")
                current_symptoms_for_recs = demographic.get("symptoms", [])
                # Just using Gemini to enhance and reformat DocBot's recommendations
                reformatted_recs = get_refined_recommendations_with_gemini(current_symptoms_for_recs, current_diagnosis_for_recs)
                # Only overwrite if reformatted recs are actually generated and non-empty
                if reformatted_recs: 
                    demographic["recommendations"] = reformatted_recs
                else:
                    # If reformatting fails, keep whatever was extracted earlier (if anything)
                    print("Reformatting recommendations failed, keeping original DocBot recommendations.")
                    if "recommendations" not in demographic: # Ensure key exists even if empty
                        demographic["recommendations"] = [] 
            else:
                # If no diagnosis yet, keep recommendations extracted from chat (if any)
                if recommendations: # recommendations variable from earlier extraction
                     demographic["recommendations"] = recommendations
                elif "recommendations" not in demographic: # Ensure key exists
                    demographic["recommendations"] = []

            # Look for things to avoid with improved patterns
            avoid = []
            avoid_patterns = [
                r"Avoid:?\s*(.*?)(?:Follow-up|When to see|$)",
                r"(?:Don't|Do not|Avoid|Stay away from|Limit)\s+([^\.]+)",
                r"It's best to avoid\s+([^\.]+)"
            ]
            
            for pattern in avoid_patterns:
                matches = re.finditer(pattern, last_assistant_msg, re.DOTALL | re.IGNORECASE)
                for match in matches:
                    if match.groups():
                        avoid_text = match.group(1).strip()
                        bullet_points = re.findall(r"[-•]([^-•]+)", avoid_text)
                        if bullet_points:
                            for point in bullet_points:
                                point = point.strip()
                                if point and point not in avoid and len(point) > 5:
                                    avoid.append(point.capitalize())
                        else:
                            sentences = re.split(r'\.(?=\s|$)', avoid_text)
                            for sentence in sentences:
                                sentence = sentence.strip()
                                if sentence and len(sentence) > 10:
                                    avoid.append(sentence.capitalize())
            
            # If no avoid items found, add common ones based on diagnosis
            if not avoid and demographic["diagnosis"]:
                diagnosis = demographic["diagnosis"].lower()
                if "urinary tract infection" in diagnosis or "uti" in diagnosis:
                    avoid = [
                        "Avoid caffeine, alcohol, and spicy foods which can irritate the bladder",
                        "Avoid delaying urination",
                        "Avoid using douches or feminine hygiene sprays"
                    ]
                elif "flu" in diagnosis or "cold" in diagnosis or "viral" in diagnosis:
                    avoid = [
                        "Avoid strenuous activities until symptoms improve",
                        "Avoid contact with others to prevent spreading the infection",
                        "Avoid alcohol and smoking"
                    ]
            
            # Update avoid section if found
            if avoid:
                demographic["avoid"] = avoid
            
            # Look for follow-up with improved patterns
            follow_up = ""
            follow_up_patterns = [
                r"Follow-up:?\s*(.*?)(?:$)",
                r"(?:See|Consult|Visit) (?:a|your) doctor\s+([^\.]+)",
                r"If symptoms (?:persist|worsen|continue)\s+([^\.]+)"
            ]
            
            for pattern in follow_up_patterns:
                match = re.search(pattern, last_assistant_msg, re.DOTALL | re.IGNORECASE)
                if match:
                    follow_up = match.group(1).strip()
                    if follow_up:
                        break
            
            # If no follow-up found, add a common one based on diagnosis
            if not follow_up and demographic["diagnosis"]:
                diagnosis = demographic["diagnosis"].lower()
                if "urinary tract infection" in diagnosis or "uti" in diagnosis:
                    follow_up = "If symptoms don't improve within 48 hours or worsen, consult a doctor for further evaluation and treatment."
                elif "flu" in diagnosis or "cold" in diagnosis or "viral" in diagnosis:
                    follow_up = "If symptoms persist for more than a week or worsen significantly, consult a healthcare provider."
                else:
                    follow_up = "If symptoms persist or worsen, consult a healthcare provider for further evaluation."
            
            # Update follow-up if found
            if follow_up:
                demographic["follow_up"] = follow_up.capitalize()
        
        # --- Get Specialist Recommendation from Gemini --- 
        # Use the potentially updated symptoms and diagnosis
        current_symptoms = demographic.get("symptoms", [])
        current_diagnosis = demographic.get("diagnosis", "")
        recommended_specialist = get_specialist_recommendation_with_gemini(current_symptoms, current_diagnosis)
        demographic["recommended_specialist_type"] = recommended_specialist
        # --- End Specialist Recommendation ---

        # Save updated demographic data
        with open("Data/demographic.json", "w", encoding="utf-8") as f:
            json.dump(demographic, f, indent=4)

    except Exception as e:
        print(f"Error updating demographic information: {e}")
        traceback.print_exc()

# Define specialist categories and associated keywords
SPECIALIST_KEYWORDS = {
    "Cardiologist": ["heart", "chest pain", "blood pressure", "cardiac", "palpitations", "dizziness", "shortness of breath with exertion"],
    "Dermatologist": ["rash", "itching", "acne", "skin lesion", "eczema", "psoriasis", "mole", "hives", "skin infection"],
    "Orthopedic Surgeon": ["bone", "joint", "fracture", "sprain", "back pain", "neck pain", "knee pain", "shoulder pain", "sports injury"],
    "Pediatrician": ["child", "infant", "baby", "childhood illness", "development", "growth", "vaccination", "children"],
    "Neurologist": ["headache", "migraine", "dizziness", "seizure", "tremor", "numbness", "memory loss", "balance problems", "nerve pain"],
    "Gynecologist": ["menstrual", "pregnancy", "vaginal", "uterine", "ovarian", "women's health", "pelvic pain", "contraception"],
    "Psychiatrist": ["anxiety", "depression", "mood", "mental health", "insomnia", "stress", "panic attacks", "phobia"],
    "Endocrinologist": ["diabetes", "thyroid", "hormone imbalance", "weight gain", "weight loss", "fatigue", "excessive thirst", "frequent urination"],
    "Pulmonologist": ["lung", "respiratory", "breathing difficulty", "persistent cough", "wheezing", "asthma", "pneumonia", "bronchitis"],
    "Ophthalmologist": ["eye pain", "vision changes", "blurry vision", "double vision", "redness in eye", "dry eyes", "cataracts", "glaucoma"],
    "Gastroenterologist": ["stomach pain", "abdominal pain", "nausea", "vomiting", "diarrhea", "constipation", "heartburn", "acid reflux", "indigestion"],
    "Nephrologist": ["kidney disease", "renal failure", "hypertension related to kidney", "dialysis", "proteinuria", "swelling in legs/ankles", "electrolyte imbalance"],
    "ENT Specialist": ["ear", "nose", "throat", "sinus", "tonsillitis", "sore throat", "ear pain", "hearing loss", "nasal congestion", "voice change"],
    "Dentist": ["tooth", "teeth", "gum", "dental pain", "cavity", "mouth sore", "jaw pain", "oral health"],
    "Urologist": ["urinary tract infection", "uti", "kidney stones", "bladder", "prostate", "painful urination", "blood in urine", "frequent urination"],
    "Rheumatologist": ["joint pain", "arthritis", "inflammation", "stiffness", "swelling", "autoimmune", "lupus", "rheumatoid arthritis"],
    "Oncologist": ["cancer", "tumor", "mass", "lump", "chemotherapy", "radiation", "unexplained weight loss"],
    "Diabetologist": ["diabetes", "blood sugar", "insulin", "glucose", "excessive thirst", "frequent urination", "diabetic"],
    "Geriatrician": ["elderly", "aging", "dementia", "elderly care", "falls", "geriatric", "senior health"],
    "Hematologist": ["anemia", "blood disorder", "bleeding", "bruising", "clotting", "leukemia", "blood test abnormalities"],
    "Allergist": ["allergy", "food allergy", "hay fever", "hives", "eczema", "asthma", "allergic reaction", "sinus"]
}

def get_specialist_recommendation_with_gemini(symptoms, diagnosis):
    """Use Gemini to classify symptoms/diagnosis into a specialist category."""
    if not symptoms and not diagnosis:
        return "Cardiologist" # Default if no info (using Cardiologist as fallback since no General Physician)

    # If very common symptoms that don't indicate anything specific, use a common specialist
    if symptoms and all(s.lower() in ["fever", "headache", "cold", "cough", "sore throat", "fatigue"] for s in symptoms):
        if not diagnosis or diagnosis.lower() in ["common cold", "flu", "viral infection"]:
            print("Common cold/flu symptoms detected, recommending Pulmonologist")
            return "Pulmonologist" # Since we don't have General Physician

    if not GEMINI_API_KEY:
        print("Gemini API Key not available. Using rule-based specialist determination instead.")
        return rule_based_specialist_determination(symptoms, diagnosis)
        
    available_specialists = list(SPECIALIST_KEYWORDS.keys())
    
    try:
        symptoms_str = "\n".join([f"• {s}" for s in symptoms])
        # Construct the description of categories for the prompt
        category_descriptions = "\n".join([f"- {spec}: Associated with { ', '.join(keywords[:4]) }..." for spec, keywords in SPECIALIST_KEYWORDS.items()])

        prompt = f"""Analyze the following patient information:
Patient Symptoms:
{symptoms_str}

Patient Diagnosis (if available): {diagnosis if diagnosis else "Not yet determined"}

Consider these specialist categories and their typical focus areas:
{category_descriptions}

Based *only* on the patient's symptoms and diagnosis provided, which *single specialist category* from the list [{ ', '.join(available_specialists) }] best describes the medical area needing attention?

Important guidelines:
1. Choose the most specific specialist that directly relates to the main symptoms
2. For general symptoms like fever, headache, fatigue ONLY, default to Pulmonologist
3. For respiratory symptoms like cough, sore throat, nasal congestion, consider ENT Specialist or Pulmonologist depending on severity
4. Only recommend Cardiologist for clear heart/chest/cardiac issues
5. For abdominal issues, prefer Gastroenterologist
6. For skin issues, always prefer Dermatologist
7. For bone/joint issues, prefer Orthopedic Surgeon

Return *only* the category name (e.g., "Neurologist", "Pulmonologist", "Cardiologist") exactly as written in the list. No explanation.
"""
        
        generation_config = {
            "temperature": 0.1, # Lower temperature for more consistent recommendations
            "top_p": 0.95,
            "top_k": 3,
            "max_output_tokens": 50,
        }
        
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config=generation_config
        )
        
        response = model.generate_content(prompt)
        # Clean the response - remove potential quotes or markdown
        recommended_type = response.text.strip().replace("'", "").replace("\"", "").replace("`", "")
        
        # Validate the response is one of the available types (dictionary keys)
        if recommended_type in SPECIALIST_KEYWORDS:
            print(f"Gemini classified symptoms under specialist: {recommended_type}")
            return recommended_type
        else:
            print(f"Gemini returned an invalid specialist type key: '{recommended_type}'. Attempting fallback match.")
            # More robust fallback matching
            for key in SPECIALIST_KEYWORDS:
                # Try to find the closest match
                if key.lower() == recommended_type.lower():
                    print(f"Exact case-insensitive match to: {key}")
                    return key
                elif key.lower() in recommended_type.lower() or recommended_type.lower() in key.lower():
                    print(f"Partial match found to key: {key}")
                    return key
            
            # If no match found, use rule-based determination
            print("No matching specialist found from Gemini's response, using rule-based determination.")
            return rule_based_specialist_determination(symptoms, diagnosis)
            
    except Exception as e:
        print(f"Error getting specialist recommendation from Gemini: {e}. Using rule-based fallback.")
        traceback.print_exc()
        return rule_based_specialist_determination(symptoms, diagnosis)

def rule_based_specialist_determination(symptoms, diagnosis):
    """Simple rule-based specialist determination as fallback"""
    # Convert symptoms and diagnosis to lowercase
    lower_symptoms = [s.lower() for s in symptoms]
    lower_diagnosis = diagnosis.lower() if diagnosis else ""
    
    # Check for keywords in symptoms and diagnosis
    for specialist, keywords in SPECIALIST_KEYWORDS.items():
        # Check diagnosis first (higher priority)
        if lower_diagnosis:
            for keyword in keywords:
                if keyword in lower_diagnosis:
                    print(f"Rule-based match by diagnosis '{lower_diagnosis}' to {specialist}")
                    return specialist
        
        # Then check symptoms
        matches = 0
        for symptom in lower_symptoms:
            for keyword in keywords:
                if keyword in symptom or symptom in keyword:
                    matches += 1
                    break  # Move to next symptom once a match is found
        
        # If more than half of symptoms match, return this specialist
        if matches >= max(1, len(lower_symptoms) // 2):
            print(f"Rule-based match by symptoms to {specialist} with {matches} matches")
            return specialist
    
    # For common symptoms, default to ENT or Pulmonologist
    common_symptoms = ["fever", "cold", "cough", "sore throat", "headache"]
    for symptom in lower_symptoms:
        if any(common in symptom for common in common_symptoms):
            print("Rule-based match found common symptoms, defaulting to Pulmonologist")
            return "Pulmonologist"
    
    # Default to Cardiologist if no clear match (since we don't have General Physician)
    print("No rule-based match found, defaulting to Cardiologist")
    return "Cardiologist"

def get_refined_recommendations_with_gemini(symptoms, diagnosis):
    """Use Gemini to reformat and enhance the existing recommendations from DocBot, not to generate new ones."""
    if not diagnosis or diagnosis.lower() == "unknown":
        return ["Consult with a healthcare professional for specific recommendations."] # Default if no diagnosis

    if not GEMINI_API_KEY:
        print("Gemini API Key not available. Skipping refinement of recommendations.")
        return [] # Return empty if Gemini is not available
        
    try:
        symptoms_str = "\n".join([f"• {s}" for s in symptoms])
        prompt = f"""You are NOT acting as a medical assistant. You are ONLY formatting and enhancing the presentation of recommendations for a {diagnosis} based on the following symptoms. Do NOT generate new medical advice or diagnoses - only reformat and structure information.

Symptoms:
{symptoms_str}

Context: A separate medical model has already diagnosed the patient with: {diagnosis}

Please ONLY FORMAT these typical recommendations for {diagnosis} with improved structure and clarity:
1. Format OTC medications with clear NAME and BASIC DOSAGE - use the format "Medication Name: dosage information"
2. Ensure practical lifestyle advice is clear and actionable
3. Include brief warning signs for seeking medical attention

IMPORTANT: 
- You are NOT providing medical advice, only formatting it
- Keep each point extremely concise, maximum 1-2 lines
- DO NOT use asterisks or any special formatting
- No preamble or conclusion, just the formatted bullet points
- Keep total output to 2-3 brief recommendations only
- Avoid phrases like "This is not a prescription" or "Follow package instructions"
- Your role is ONLY to make the existing recommendations clearer and more structured
"""
        
        generation_config = {
            "temperature": 0.3, # Lower temperature for more consistent formatting
            "top_p": 0.95,
            "top_k": 0,
            "max_output_tokens": 200, # Shorter limit to force conciseness
        }
        
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config=generation_config
        )
        
        response = model.generate_content(prompt)
        recommendations_text = response.text.strip()
        
        # Extract bullet points from the response
        recommendations = []
        for line in recommendations_text.split('\n'):
            line = line.strip()
            if line.startswith('•'):
                clean_point = line.lstrip('• ').strip()
                if clean_point:
                    # Look for medication names and format consistently, removing any asterisks
                    clean_point = clean_point.replace("*", "")
                    medication_match = re.search(r'([A-Za-z\s\(\)]+):\s+(.+)', clean_point)
                    if medication_match:
                        med_name = medication_match.group(1).strip()
                        dosage_info = medication_match.group(2).strip()
                        # Format consistently for the GUI to parse properly and remove prescription disclaimers
                        dosage_info = re.sub(r'this is not a prescription[^.]*\.', '', dosage_info, flags=re.IGNORECASE).strip()
                        dosage_info = re.sub(r'follow package instructions[^.]*\.', '', dosage_info, flags=re.IGNORECASE).strip()
                        recommendations.append(f"{med_name}: {dosage_info}")
                    else:
                        recommendations.append(clean_point)
            elif line: # Capture lines even without bullet if Gemini misses formatting
                if len(line) > 10: # Basic filter for meaningful lines
                    # Remove any asterisks and disclaimers
                    clean_line = line.replace("*", "")
                    clean_line = re.sub(r'this is not a prescription[^.]*\.', '', clean_line, flags=re.IGNORECASE).strip()
                    clean_line = re.sub(r'follow package instructions[^.]*\.', '', clean_line, flags=re.IGNORECASE).strip()
                    recommendations.append(clean_line)
        
        # Limit to 3 most important recommendations
        recommendations = recommendations[:3]
        
        if recommendations:
             print(f"Gemini refined formatting of recommendations (concise): {recommendations}")
             return recommendations
        else:
             print("Gemini did not return formatted recommendations in the expected structure.")
             return [] # Return empty list if parsing fails

    except Exception as e:
        print(f"Error refining recommendations with Gemini: {e}")
        traceback.print_exc()
        return [] # Return empty list on error

def get_precise_diagnosis_from_rag(symptoms):
    """Get a precise diagnosis name from the simplified RAG system based on symptoms."""
    if not symptoms or len(symptoms) < 1:
        return "Insufficient symptom information"
    
    try:
        # Convert symptom strings to just the common names (without medical terms in parentheses)
        simplified_symptoms = []
        for symptom in symptoms:
            # Extract just the common name if in format "Common name (Medical term)"
            if "(" in symptom and ")" in symptom:
                common_name = symptom.split("(")[0].strip().lower()
                simplified_symptoms.append(common_name)
            else:
                simplified_symptoms.append(symptom.lower())
        
        # Try to find a matching symptom combination first
        if len(simplified_symptoms) >= 2:
            combination_match = find_matching_combination(simplified_symptoms)
            if combination_match and "diagnosis" in combination_match:
                return combination_match["diagnosis"]
        
        # If no combination match, check individual conditions
        best_match = None
        best_match_score = 0
        
        for condition, condition_data in MEDICAL_DATA.items():
            # Skip if no diagnosis info
            if "diagnosis" not in condition_data:
                continue
                
            # Check how many symptoms match this condition
            score = 0
            condition_lower = condition.lower()
            
            for symptom in simplified_symptoms:
                if symptom in condition_lower:
                    score += 2  # Higher weight for symptom in condition name
                
                # Check if symptom is in specialties keywords
                for specialist, keywords in SPECIALIST_KEYWORDS.items():
                    if symptom in keywords:
                        for keyword in keywords:
                            if keyword in condition_lower:
                                score += 1
            
            if score > best_match_score:
                best_match_score = score
                best_match = condition_data["diagnosis"]
        
        # Return the best match if found, otherwise a general diagnosis
        if best_match and best_match_score > 1:
            return best_match
        
        # Default diagnoses based on common symptom patterns
        if "fever" in simplified_symptoms and "headache" in simplified_symptoms:
            return "Viral Infection"
        elif "cough" in simplified_symptoms and "congestion" in simplified_symptoms:
            return "Upper Respiratory Infection"
        elif "headache" in simplified_symptoms:
            return "Tension Headache"
        elif "nausea" in simplified_symptoms and "vomiting" in simplified_symptoms:
            return "Gastroenteritis"
        elif "rash" in simplified_symptoms:
            return "Dermatitis"
        
        # Very generic fallback
        return "Common Viral Infection"
        
    except Exception as e:
        print(f"Error getting precise diagnosis: {e}")
        traceback.print_exc()
        return "Undetermined Condition"

if __name__ == "__main__":
    # Initialize demographic file for testing if it doesn't exist
    if not os.path.exists("Data/demographic.json"):
        with open("Data/demographic.json", "w", encoding="utf-8") as f:
            json.dump({"symptoms": [], "diagnosis": "", "recommendations": [], "avoid": [], "follow_up": "", "recommended_specialist_type": "General Physician"}, f, indent=4)
            
    # Example test with Gemini formatting
    # test_symptoms_raw = ['i have a bad cough', 'feeling hot', 'temp is 101', 'runny nose too']
    # formatted_symptoms = format_symptoms_with_gemini(test_symptoms_raw)
    # print("\n--- Gemini Formatting Test ---")
    # print(f"Raw: {test_symptoms_raw}")
    # print(f"Formatted: {formatted_symptoms}")
    # print("----------------------------\n")

    Query = input("User: ")
    print(f"Assistant: {ChatBot(Query)}")