import os
import sys
from pathlib import Path
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Create necessary directories
os.makedirs("Data", exist_ok=True)
os.makedirs("vectorstore", exist_ok=True)

def create_vectorstore():
    """Create an initial vector store with some medical information."""
    
    # Create a simple medical text file if none exists
    medical_data_dir = Path("medical_data")
    medical_data_dir.mkdir(exist_ok=True)
    
    # Create sample medical data if no files exist
    if not list(medical_data_dir.glob("*.txt")):
        print("Creating sample medical data files...")
        
        sample_data = {
            "common_cold.txt": """
            Common Cold
            
            The common cold is a viral infection of the upper respiratory tract. Symptoms usually include runny nose, sneezing, sore throat, cough, congestion, body aches, and sometimes a mild fever.
            
            Treatment:
            - Rest and stay hydrated
            - Over-the-counter pain relievers like acetaminophen (Tylenol) or ibuprofen (Advil)
            - Decongestants or antihistamines can help with symptoms
            - Throat lozenges or salt water gargle for sore throat
            
            Avoid:
            - Smoking and alcohol which can worsen symptoms
            - Spreading the virus by washing hands regularly
            
            When to see a doctor:
            - Fever above 101.3°F (38.5°C)
            - Symptoms lasting more than 10 days
            - Severe or unusual symptoms
            """,
            
            "fever.txt": """
            Fever
            
            Fever is a temporary increase in body temperature, often due to illness. A temperature above 100.4°F (38°C) is considered a fever.
            
            Treatment:
            - Rest and plenty of fluids
            - Over-the-counter medications like acetaminophen or ibuprofen to reduce fever
            - Light clothing and a comfortable room temperature
            - Cool, damp washcloth on the forehead
            
            Avoid:
            - Overdressing which can trap body heat
            - Cold baths which can cause shivering and raise temperature
            
            When to see a doctor:
            - Temperature above 103°F (39.4°C) in adults
            - Fever lasting more than three days
            - Fever with severe headache, rash, sensitivity to light, stiff neck
            """,
            
            "headache.txt": """
            Headache
            
            Headaches can be primary (not caused by another condition) or secondary (symptom of another condition). Tension headaches, migraines, and cluster headaches are common types.
            
            Treatment:
            - Over-the-counter pain relievers
            - Rest in a quiet, dark room
            - Hot or cold compresses to the head or neck
            - Massage and relaxation techniques
            
            Avoid:
            - Triggers such as stress, certain foods, alcohol
            - Irregular sleep patterns
            - Skipping meals
            
            When to see a doctor:
            - Severe or sudden-onset headache
            - Headache with fever, stiff neck, confusion
            - Headache after head injury
            - Headache that worsens despite treatment
            """,
            
            "sore_throat.txt": """
            Sore Throat
            
            A sore throat (pharyngitis) is pain, scratchiness or irritation of the throat that often worsens when swallowing. The most common cause is a viral infection or cold.
            
            Treatment:
            - Gargle with warm salt water
            - Drink warm liquids
            - Throat lozenges or sprays
            - Humidifier to moisten the air
            - Over-the-counter pain relievers
            
            Avoid:
            - Smoking and exposure to secondhand smoke
            - Acidic or spicy foods
            - Dry air
            
            When to see a doctor:
            - Sore throat lasting longer than a week
            - Difficulty swallowing or breathing
            - Fever higher than 101°F (38.3°C)
            - White patches on tonsils (may indicate strep throat)
            """
        }
        
        for filename, content in sample_data.items():
            with open(medical_data_dir / filename, "w") as f:
                f.write(content)
    
    # Load documents
    print("Loading medical data documents...")
    loader = DirectoryLoader(
        medical_data_dir.as_posix(),
        glob="**/*.txt",
        loader_cls=TextLoader
    )
    documents = loader.load()
    
    # Split documents
    print("Splitting documents into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    texts = text_splitter.split_documents(documents)
    
    # Create embeddings and vectorstore
    print("Creating vector store with medical data...")
    embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectorstore = FAISS.from_documents(texts, embedding_model)
    
    # Save the vectorstore
    print("Saving vector store...")
    vectorstore.save_local("vectorstore/db_faiss")
    
    print("Vector store initialization complete!")

if __name__ == "__main__":
    # Check if vectorstore exists
    if not os.path.exists("vectorstore/db_faiss"):
        print("Vector store not found. Creating new vector store...")
        create_vectorstore()
    else:
        print("Vector store already exists.")
        
        # Check if user wants to recreate it
        recreate = input("Do you want to recreate the vector store? (y/n): ").lower() == 'y'
        if recreate:
            print("Recreating vector store...")
            create_vectorstore() 