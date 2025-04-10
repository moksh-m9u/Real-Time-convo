"""
Simplified version of RAG system that uses a dictionary-based approach
instead of vector embeddings. This avoids TensorFlow dependencies.
"""

import os
import json
import re
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

# Enhanced medical data with diagnoses included
MEDICAL_DATA = {
    "common cold": {
        "info": """
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
        "diagnosis": "Common Cold",
        "recommendations": [
            "Taking over-the-counter decongestants can help relieve nasal congestion",
            "Drinking hot tea with honey can soothe a sore throat"
        ],
        "avoid": [
            "Smoking and alcohol which can worsen symptoms",
            "Exposure to cold air which may irritate the throat"
        ],
        "follow_up": "If symptoms worsen after 7 days, consult a doctor"
    },
    
    "fever": {
        "info": """
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
        "diagnosis": "Fever of Unknown Origin",
        "recommendations": [
            "Taking acetaminophen or ibuprofen can help reduce fever",
            "Staying hydrated with plenty of fluids is essential"
        ],
        "avoid": [
            "Overdressing which can trap body heat",
            "Cold baths which can cause shivering and raise temperature"
        ],
        "follow_up": "If fever persists more than 3 days or exceeds 103°F, seek medical attention immediately"
    },
    
    "headache": {
        "info": """
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
        "diagnosis": "Tension Headache",
        "recommendations": [
            "Over-the-counter pain relievers like ibuprofen can provide relief",
            "Regular breaks from screen time to reduce eye strain"
        ],
        "avoid": [
            "Known trigger foods such as aged cheese or processed meats",
            "Skipping meals which can trigger headaches"
        ],
        "follow_up": "If headaches persist or worsen, consult with a neurologist"
    },
    
    "sore throat": {
        "info": """
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
        """,
        "diagnosis": "Viral Pharyngitis",
        "recommendations": [
            "Gargling with warm salt water every few hours",
            "Drinking warm herbal tea with honey for soothing relief"
        ],
        "avoid": [
            "Acidic or spicy foods that can irritate the throat",
            "Dry air - consider using a humidifier"
        ],
        "follow_up": "If white patches appear on tonsils or fever develops, consult a doctor for possible strep throat"
    },
    
    "cough": {
        "info": """
        Cough
        
        Coughing is a reflex that helps clear your airways of irritants. Coughs can be acute (lasting less than three weeks) or chronic (lasting more than eight weeks).
        
        Treatment:
        - Stay hydrated to thin mucus
        - Use cough drops or lozenges to soothe the throat
        - Try honey (for adults and children over 1 year)
        - Use a humidifier to add moisture to the air
        - Over-the-counter cough suppressants for dry coughs
        
        Avoid:
        - Smoking and exposure to irritants
        - Dry air
        - Lying flat, which can worsen coughing at night
        
        When to see a doctor:
        - Cough lasting more than three weeks
        - Coughing up blood or thick, discolored mucus
        - Accompanied by high fever, shortness of breath, wheezing
        """,
        "diagnosis": "Acute Bronchitis",
        "recommendations": [
            "Using a humidifier to add moisture to the air",
            "Taking honey (for adults) to soothe the throat and reduce coughing"
        ],
        "avoid": [
            "Smoking and exposure to secondhand smoke",
            "Lying flat immediately after eating which may worsen coughing at night"
        ],
        "follow_up": "If coughing persists beyond three weeks or produces colored phlegm, consult a doctor"
    },
    
    "flu": {
        "info": """
        Influenza (Flu)
        
        Influenza is a contagious respiratory illness caused by influenza viruses. Symptoms include fever, cough, sore throat, body aches, fatigue, and sometimes vomiting and diarrhea.
        
        Treatment:
        - Rest and stay hydrated
        - Over-the-counter pain relievers for fever and aches
        - Antiviral medications if prescribed early
        - Use a humidifier to ease breathing
        
        Avoid:
        - Contact with others to prevent spreading
        - Alcohol and tobacco
        - Strenuous activities until recovery
        
        When to see a doctor:
        - Difficulty breathing or shortness of breath
        - Persistent chest pain or pressure
        - Confusion or inability to arouse
        - Severe or persistent vomiting
        """,
        "diagnosis": "Influenza (Flu)",
        "recommendations": [
            "Taking ibuprofen can help reduce fever and pain",
            "Rest and adequate hydration are essential for recovery"
        ],
        "avoid": [
            "Having cold food and drinks",
            "Contact with others to prevent spreading the virus"
        ],
        "follow_up": "If symptoms persist or worsen after a week, consult a doctor"
    },
    
    "allergies": {
        "info": """
        Allergies
        
        Allergies occur when your immune system reacts to a foreign substance. Symptoms include sneezing, itching, runny nose, and watery eyes.
        
        Treatment:
        - Over-the-counter antihistamines
        - Nasal corticosteroids
        - Decongestants for short-term relief
        - Allergy shots (immunotherapy)
        
        Avoid:
        - Known allergens (pollen, dust, pet dander)
        - Outdoor activities during high pollen count
        - Carpeting and upholstered furniture that collect allergens
        
        When to see a doctor:
        - Symptoms persist despite treatment
        - Allergic reactions interfere with daily activities
        - Signs of asthma (wheezing, shortness of breath)
        """,
        "diagnosis": "Seasonal Allergic Rhinitis",
        "recommendations": [
            "Over-the-counter antihistamines can provide relief from symptoms",
            "Using a HEPA filter in your bedroom can reduce allergen exposure"
        ],
        "avoid": [
            "Outdoor activities during high pollen counts",
            "Keeping windows open during allergy season"
        ],
        "follow_up": "If symptoms don't improve with over-the-counter medications, consult an allergist"
    },
    
    "migraine": {
        "info": """
        Migraine
        
        Migraines are intense headaches that can cause throbbing pain, usually on one side of the head, often accompanied by nausea, vomiting, and sensitivity to light and sound.
        
        Treatment:
        - Rest in a quiet, dark room
        - Apply cold packs to the forehead
        - Take migraine-specific medications (triptans)
        - Over-the-counter pain relievers
        
        Avoid:
        - Known triggers (certain foods, stress, bright lights)
        - Skipping meals
        - Irregular sleep patterns
        - Excessive caffeine
        
        When to see a doctor:
        - Severe headache that comes on suddenly
        - Headache with fever, stiff neck, confusion, seizures
        - Headache after a head injury
        - Chronic headaches that worsen after coughing or exertion
        """,
        "diagnosis": "Migraine Headache",
        "recommendations": [
            "Resting in a quiet, dark room during attacks",
            "Applying cold compresses to the forehead"
        ],
        "avoid": [
            "Known trigger foods like chocolate, aged cheese, or red wine",
            "Bright lights and loud noises during episodes"
        ],
        "follow_up": "Consider consulting a neurologist if migraines are frequent or debilitating"
    },
    
    "pneumonia": {
        "info": """
        Pneumonia
        
        Pneumonia is an infection that inflames the air sacs in one or both lungs. The air sacs may fill with fluid or pus, causing cough with phlegm, fever, chills, and difficulty breathing.
        
        Treatment:
        - Antibiotics if the cause is bacterial
        - Antiviral medications if the cause is viral
        - Pain relievers and fever reducers
        - Cough medicine to help you rest
        - Plenty of fluids to prevent dehydration
        
        Avoid:
        - Smoking and secondhand smoke
        - Exposure to people with respiratory infections
        - Alcohol which can interfere with antibiotics
        
        When to seek emergency care:
        - Difficulty breathing or shortness of breath
        - Chest pain that worsens when you breathe or cough
        - Persistent high fever greater than 102°F (39°C)
        - Confusion or changes in mental awareness
        """,
        "diagnosis": "Pneumonia",
        "recommendations": [
            "Complete the full course of antibiotics if prescribed",
            "Rest and stay hydrated to help your body recover"
        ],
        "avoid": [
            "Smoking and exposure to secondhand smoke",
            "Strenuous activity until fully recovered"
        ],
        "follow_up": "If symptoms worsen or don't improve with treatment, seek medical attention immediately"
    },
    
    "heart attack": {
        "info": """
        Heart Attack (Myocardial Infarction)
        
        A heart attack occurs when blood flow to part of the heart is blocked, causing damage to heart muscle. Symptoms include chest pain or pressure, pain spreading to jaw/neck/back, nausea, shortness of breath, and cold sweat.
        
        Treatment:
        - EMERGENCY MEDICAL CARE IS REQUIRED
        - Aspirin to prevent further blood clotting
        - Clot-busting medications or surgical procedures
        - Various medications including blood thinners, beta blockers, ACE inhibitors
        
        Avoid:
        - Delay in seeking medical attention
        - Physical exertion until cleared by a doctor
        - Smoking and secondhand smoke
        
        When to seek emergency care:
        - ANY suspected heart attack symptoms - CALL 911 IMMEDIATELY
        """,
        "diagnosis": "Possible Heart Attack - MEDICAL EMERGENCY",
        "recommendations": [
            "Call 911 or emergency services immediately",
            "Take aspirin if available and not allergic"
        ],
        "avoid": [
            "Delay in seeking emergency care",
            "Physical exertion of any kind"
        ],
        "follow_up": "This is a life-threatening emergency requiring immediate hospital care"
    },
    
    "stroke": {
        "info": """
        Stroke
        
        A stroke occurs when blood flow to part of the brain is blocked or when a blood vessel in the brain bursts. Brain tissue deprived of oxygen begins to die within minutes. Remember FAST: Face drooping, Arm weakness, Speech difficulty, Time to call 911.
        
        Treatment:
        - EMERGENCY MEDICAL CARE IS REQUIRED
        - Clot-busting medications if given within 3-4.5 hours
        - Endovascular procedures to remove clot
        - Surgery to stop bleeding for hemorrhagic stroke
        
        Avoid:
        - Delay in seeking medical attention
        - Taking medications before medical evaluation
        
        When to seek emergency care:
        - ANY suspected stroke symptoms - CALL 911 IMMEDIATELY
        """,
        "diagnosis": "Possible Stroke - MEDICAL EMERGENCY",
        "recommendations": [
            "Call 911 or emergency services immediately",
            "Note the time symptoms began"
        ],
        "avoid": [
            "Delay in seeking emergency care",
            "Taking medications before medical evaluation"
        ],
        "follow_up": "This is a time-sensitive emergency requiring immediate hospital care"
    },
    
    "appendicitis": {
        "info": """
        Appendicitis
        
        Appendicitis is inflammation of the appendix that can lead to rupture if untreated. Symptoms typically begin with pain near the navel that moves to the lower right abdomen, along with nausea, vomiting, and low-grade fever.
        
        Treatment:
        - Surgery to remove the appendix (appendectomy)
        - Antibiotics before and after surgery
        - Pain medications
        
        Avoid:
        - Laxatives or enemas which can cause rupture
        - Pain medications before medical evaluation which can mask symptoms
        - Food and drink which may worsen symptoms
        
        When to seek emergency care:
        - Sudden pain that begins on the right side of the lower abdomen
        - Pain that worsens if you cough, walk or make jarring movements
        - Nausea and vomiting
        - Loss of appetite
        """,
        "diagnosis": "Possible Appendicitis - REQUIRES MEDICAL ATTENTION",
        "recommendations": [
            "Seek immediate medical evaluation",
            "Do not take pain medications before medical evaluation"
        ],
        "avoid": [
            "Taking laxatives or using heating pads on the abdomen",
            "Eating or drinking until evaluated by a doctor"
        ],
        "follow_up": "This condition may require emergency surgery"
    },
    
    "meningitis": {
        "info": """
        Meningitis
        
        Meningitis is inflammation of the membranes surrounding the brain and spinal cord. Viral meningitis may improve without treatment, but bacterial meningitis is serious and can be life-threatening requiring immediate antibiotic treatment.
        
        Treatment:
        - EMERGENCY MEDICAL CARE IS REQUIRED
        - Antibiotics if bacterial
        - Antiviral medications if viral
        - Corticosteroids to reduce inflammation
        - Anticonvulsants for seizures
        
        Avoid:
        - Delay in seeking medical attention
        - Taking medications that might mask symptoms
        
        When to seek emergency care:
        - Sudden high fever
        - Severe headache with stiff neck
        - Confusion or difficulty concentrating
        - Seizures
        - Sensitivity to light
        - Skin rash (especially non-blanching)
        """,
        "diagnosis": "Possible Meningitis - MEDICAL EMERGENCY",
        "recommendations": [
            "Seek emergency medical care immediately",
            "This is a potentially life-threatening condition"
        ],
        "avoid": [
            "Any delay in seeking emergency care",
            "Taking medications that might mask symptoms"
        ],
        "follow_up": "This requires immediate hospital evaluation and treatment"
    },
    
    "asthma": {
        "info": """
        Asthma
        
        Asthma is a condition in which your airways narrow, swell and produce extra mucus, making breathing difficult and triggering coughing, wheezing and shortness of breath.
        
        Treatment:
        - Quick-relief medications (rescue inhalers)
        - Long-term control medications
        - Breathing exercises
        - Identifying and avoiding triggers
        
        Avoid:
        - Known triggers such as allergens, smoke, pollution
        - Extreme cold air
        - Exercise in cold, dry air
        
        When to seek emergency care:
        - Severe shortness of breath or difficulty breathing
        - No improvement after using rescue inhaler
        - Shortness of breath when walking or talking
        - Bluish tint to lips or fingernails
        """,
        "diagnosis": "Asthma",
        "recommendations": [
            "Use rescue inhaler as prescribed for acute symptoms",
            "Identify and avoid personal triggers"
        ],
        "avoid": [
            "Known triggers such as allergens, smoke, or pollution",
            "Extreme cold air which can trigger symptoms"
        ],
        "follow_up": "Work with a doctor to develop an asthma action plan"
    },
    
    "urinary tract infection": {
        "info": """
        Urinary Tract Infection (UTI)
        
        A UTI is an infection in any part of the urinary system, including kidneys, bladder, ureters and urethra. Most infections involve the lower urinary tract — the bladder and urethra.
        
        Treatment:
        - Antibiotics
        - Pain relievers
        - Plenty of water
        
        Avoid:
        - Alcohol and caffeine
        - Spicy foods
        - Holding urine
        
        When to seek medical care:
        - Blood in urine
        - Back pain near kidneys
        - High fever
        - Nausea and vomiting
        """,
        "diagnosis": "Urinary Tract Infection",
        "recommendations": [
            "See a doctor for antibiotics which are typically needed",
            "Drink plenty of water to help flush bacteria"
        ],
        "avoid": [
            "Caffeine, alcohol, and spicy foods which can irritate the bladder",
            "Delaying urination when you feel the need to go"
        ],
        "follow_up": "Complete the full course of antibiotics if prescribed"
    },
    
    "kidney infection": {
        "info": """
        Kidney Infection (Pyelonephritis)
        
        A kidney infection is a type of urinary tract infection that begins in the urethra or bladder and travels up to one or both kidneys. Symptoms include high fever, abdominal and back pain, and painful urination.
        
        Treatment:
        - Antibiotics
        - Hospitalization for severe cases
        - Pain relievers
        - Plenty of fluids
        
        Avoid:
        - Delaying treatment
        - Alcohol and caffeine
        
        When to seek medical care:
        - Fever above 101°F (38.3°C)
        - Persistent pain
        - Inability to keep down fluids
        - Blood in urine
        """,
        "diagnosis": "Kidney Infection - REQUIRES PROMPT ATTENTION",
        "recommendations": [
            "Seek medical attention promptly",
            "Stay hydrated with water while awaiting medical care"
        ],
        "avoid": [
            "Delaying medical treatment which can lead to serious complications",
            "Alcohol and caffeine which can worsen dehydration"
        ],
        "follow_up": "This condition typically requires antibiotics and possibly hospitalization"
    },
    
    "diabetes": {
        "info": """
        Diabetes
        
        Diabetes is a disease that occurs when your blood glucose (blood sugar) is too high. Insulin, a hormone made by the pancreas, helps glucose get into your cells to be used for energy. With diabetes, your body either doesn't make enough insulin or can't effectively use the insulin it makes.
        
        Treatment:
        - Monitoring blood sugar levels
        - Insulin therapy (for Type 1 and some Type 2)
        - Oral or injectable medications (for Type 2)
        - Healthy diet and exercise
        
        Avoid:
        - High sugar foods and beverages
        - Smoking
        - Sedentary lifestyle
        
        When to seek emergency care:
        - Very high blood sugar with symptoms like extreme thirst, frequent urination
        - Very low blood sugar with confusion, dizziness, or unconsciousness
        - Ketoacidosis symptoms including fruity breath, vomiting, abdominal pain
        """,
        "diagnosis": "Possible Diabetes",
        "recommendations": [
            "See a doctor for proper evaluation and blood testing",
            "Stay hydrated with water"
        ],
        "avoid": [
            "Sugary foods and beverages",
            "Delaying medical evaluation"
        ],
        "follow_up": "This condition requires proper medical diagnosis and management"
    },
    
    "food poisoning": {
        "info": """
        Food Poisoning
        
        Food poisoning is illness caused by eating contaminated food. Symptoms often include nausea, vomiting, and diarrhea, which may be severe in some cases.
        
        Treatment:
        - Rest and let your stomach settle
        - Try sucking on ice chips or taking small sips of water
        - Gradually return to eating with bland, easy-to-digest foods
        - Avoid dairy, fatty, spicy and highly seasoned foods
        
        Avoid:
        - Dairy products
        - Caffeine and alcohol
        - Nicotine
        - Fatty or highly seasoned foods
        
        When to seek medical care:
        - Frequent vomiting for more than two days
        - Blood in vomit or stool
        - Diarrhea for more than three days
        - Extreme pain or severe abdominal cramping
        - An oral temperature higher than 100.4°F (38°C)
        - Signs of dehydration
        """,
        "diagnosis": "Food Poisoning",
        "recommendations": [
            "Stay hydrated with clear fluids sipped slowly",
            "Rest and let your digestive system recover"
        ],
        "avoid": [
            "Dairy products, caffeine, and alcohol",
            "Solid foods until vomiting stops"
        ],
        "follow_up": "If symptoms persist more than 3 days or include bloody diarrhea, see a doctor"
    },
    
    "pulmonary embolism": {
        "info": """
        Pulmonary Embolism
        
        A pulmonary embolism is a blockage in one of the pulmonary arteries in your lungs, most commonly caused by blood clots that travel from the legs or other parts of the body to the lungs.
        
        Treatment:
        - EMERGENCY MEDICAL CARE IS REQUIRED
        - Blood thinners (anticoagulants)
        - Clot-dissolving medications (thrombolytics) for severe cases
        - Surgical removal or filter for very large clots
        
        Avoid:
        - Delay in seeking medical attention
        - Physical activity before medical evaluation
        
        When to seek emergency care:
        - Sudden shortness of breath
        - Chest pain that worsens when you breathe in
        - Coughing up blood
        - Rapid or irregular heartbeat
        - Lightheadedness or fainting
        """,
        "diagnosis": "Possible Pulmonary Embolism - MEDICAL EMERGENCY",
        "recommendations": [
            "Seek emergency medical care immediately - call 911/ambulance",
            "Remain calm and try to maintain steady breathing if possible"
        ],
        "avoid": [
            "Any delay in seeking emergency care",
            "Physical exertion of any kind"
        ],
        "follow_up": "This is a life-threatening emergency requiring immediate hospital care"
    },
    
    "shingles": {
        "info": """
        Shingles (Herpes Zoster)
        
        Shingles is a viral infection that causes a painful rash. It is caused by the varicella-zoster virus, the same virus that causes chickenpox. After you've had chickenpox, the virus lies inactive in nerve tissue. Years later, the virus may reactivate as shingles.
        
        Treatment:
        - Antiviral medications (most effective if started within 72 hours)
        - Pain medications
        - Topical antibiotics if blisters become infected
        - Calamine lotion and cool compresses for itching
        
        Avoid:
        - Scratching the rash
        - Contact with pregnant women or immunocompromised people
        - Touching the rash and then touching other parts of your body
        
        When to seek medical care:
        - Rash near the eyes, which can cause eye damage
        - Widespread rash
        - Pain or rash accompanied by fever, headache, or sensitivity to light
        - Swelling, warmth, or redness near the rash
        """,
        "diagnosis": "Shingles",
        "recommendations": [
            "See a doctor promptly - antiviral medication works best if started early",
            "Keep the rash clean and covered to prevent spreading to others"
        ],
        "avoid": [
            "Scratching the rash which can lead to infection",
            "Contact with pregnant women, infants, and those with weakened immune systems"
        ],
        "follow_up": "Complete the full course of any prescribed medications"
    },
    
    "bronchitis": {
        "info": """
        Bronchitis
        
        Bronchitis is inflammation of the lining of the bronchial tubes, which carry air to and from the lungs. People with bronchitis often cough up thickened mucus, which can be discolored.
        
        Treatment:
        - Rest and plenty of fluids
        - Over-the-counter pain relievers
        - Humidifier to ease breathing
        - Antibiotics if the cause is bacterial
        
        Avoid:
        - Smoking and secondhand smoke
        - Air pollution and lung irritants
        - Cold, dry air
        
        When to seek medical care:
        - Fever above 100.4°F (38°C)
        - Cough with bloody or discolored mucus
        - Shortness of breath or wheezing
        - Symptoms lasting more than 3 weeks
        """,
        "diagnosis": "Bronchitis",
        "recommendations": [
            "Rest and drink plenty of fluids to thin mucus secretions",
            "Use a humidifier or steam to help loosen congestion"
        ],
        "avoid": [
            "Smoking and exposure to secondhand smoke or other respiratory irritants",
            "Cold, dry air which can aggravate symptoms"
        ],
        "follow_up": "If symptoms persist longer than 3 weeks or include high fever, see a doctor"
    },
    
    "anxiety": {
        "info": """
        Anxiety Disorders
        
        Anxiety disorders are a group of mental health conditions characterized by significant feelings of anxiety and fear. These feelings are strong enough to interfere with one's daily activities.
        
        Treatment:
        - Psychotherapy (especially cognitive behavioral therapy)
        - Medications (antidepressants, anti-anxiety medications)
        - Stress management techniques
        - Regular exercise
        
        Self-help strategies:
        - Deep breathing exercises
        - Progressive muscle relaxation
        - Mindfulness meditation
        - Regular physical activity
        
        When to seek medical care:
        - Anxiety interferes with daily activities
        - You have suicidal thoughts or behaviors
        - You have trouble with alcohol or drug use
        - You have other mental health concerns along with anxiety
        """,
        "diagnosis": "Anxiety Disorder",
        "recommendations": [
            "Practice deep breathing exercises when feeling anxious",
            "Consider speaking with a mental health professional for proper evaluation"
        ],
        "avoid": [
            "Caffeine and alcohol which can worsen anxiety",
            "Avoiding feared situations, which can reinforce anxiety"
        ],
        "follow_up": "A mental health professional can help develop an effective treatment plan"
    },
    
    "depression": {
        "info": """
        Depression
        
        Depression is a common and serious medical illness that negatively affects how you feel, the way you think and how you act. It causes feelings of sadness and/or a loss of interest in activities you once enjoyed.
        
        Treatment:
        - Psychotherapy (especially cognitive behavioral therapy)
        - Medications (antidepressants)
        - Lifestyle changes (exercise, sleep hygiene, nutrition)
        - In severe cases, treatments like ECT or TMS
        
        Self-help strategies:
        - Regular physical activity
        - Setting small, achievable goals
        - Social connection and support
        - Sleep hygiene
        
        When to seek emergency care:
        - Suicidal thoughts or behaviors
        - Inability to care for yourself
        - Psychotic symptoms
        """,
        "diagnosis": "Depression",
        "recommendations": [
            "Consider speaking with a mental health professional for proper evaluation",
            "Regular physical activity can help improve mood"
        ],
        "avoid": [
            "Social isolation which can worsen symptoms",
            "Alcohol and drugs which can worsen depression"
        ],
        "follow_up": "A mental health professional can help develop an effective treatment plan"
    },
    
    "back pain": {
        "info": """
        Back Pain
        
        Back pain is one of the most common reasons people seek medical care or miss work. Back pain can range from a muscle aching to a shooting, burning or stabbing sensation.
        
        Treatment:
        - Over-the-counter pain relievers
        - Hot or cold packs
        - Gentle activity and stretching
        - Physical therapy
        - In some cases, prescription medications
        
        Avoid:
        - Prolonged bed rest
        - Heavy lifting or activities that strain the back
        - Poor posture while sitting or standing
        
        When to seek medical care:
        - Pain following trauma like a fall or car accident
        - Pain accompanied by fever
        - Pain causing neurological symptoms like weakness or numbness
        - Pain accompanied by loss of bladder or bowel control
        - Pain that doesn't improve with rest
        """,
        "diagnosis": "Lower Back Pain/Strain",
        "recommendations": [
            "Apply ice for the first 48-72 hours, then switch to heat",
            "Over-the-counter pain relievers can help manage pain and inflammation"
        ],
        "avoid": [
            "Prolonged bed rest which can weaken muscles",
            "Heavy lifting and twisting movements"
        ],
        "follow_up": "If pain persists more than two weeks or is severe, consult a doctor"
    },
    
    "arthritis": {
        "info": """
        Arthritis
        
        Arthritis is inflammation of one or more joints, causing pain and stiffness that can worsen with age. The most common types are osteoarthritis and rheumatoid arthritis.
        
        Treatment:
        - Pain medications
        - Physical therapy
        - Assistive devices
        - In some cases, surgery
        - Weight management
        
        Self-management:
        - Regular exercise to maintain joint flexibility
        - Heat and cold therapy
        - Assistive devices to reduce strain on joints
        - Balanced diet and healthy weight
        
        When to seek medical care:
        - Severe pain that interferes with daily activities
        - Joint deformity
        - Symptoms accompanied by fever
        - Rapid onset of symptoms
        """,
        "diagnosis": "Arthritis",
        "recommendations": [
            "Over-the-counter anti-inflammatory medications can reduce pain and swelling",
            "Gentle exercises like swimming can help maintain joint mobility"
        ],
        "avoid": [
            "High-impact activities that can stress affected joints",
            "Remaining in one position for too long"
        ],
        "follow_up": "A doctor can determine the specific type of arthritis and recommend appropriate treatment"
    }
}

# Additional condition combinations for common symptom groups
SYMPTOM_COMBINATIONS = {
    # Common Cold & Flu
    ("fever", "cough", "sore throat", "body aches"): {
        "diagnosis": "Common Flu",
        "recommendations": [
            "Taking ibuprofen can help reduce fever and pain",
            "Rest and staying hydrated are essential for recovery"
        ],
        "avoid": [
            "Having cold food and drinks",
            "Going to work/school and spreading the infection"
        ],
        "follow_up": "If the symptoms persist beyond a week, consult a doctor"
    },
    ("fever", "headache", "sore throat", "body aches"): {
        "diagnosis": "Common Flu",
        "recommendations": [
            "Taking ibuprofen can help reduce fever and pain",
            "Getting plenty of rest helps your immune system fight the infection"
        ],
        "avoid": [
            "Having cold food and drinks",
            "Strenuous activity until recovery"
        ],
        "follow_up": "If the symptoms persist, consult a doctor"
    },
    ("runny nose", "sneezing", "congestion", "cough"): {
        "diagnosis": "Common Cold",
        "recommendations": [
            "Using over-the-counter decongestants can relieve congestion",
            "Drinking warm fluids to soothe the throat and thin mucus"
        ],
        "avoid": [
            "Alcohol and smoking which can worsen symptoms",
            "Sharing personal items like towels or utensils"
        ],
        "follow_up": "If symptoms worsen after a week or include high fever, see a doctor"
    },
    
    # Allergies and Respiratory Issues
    ("headache", "runny nose", "sneezing", "watery eyes"): {
        "diagnosis": "Seasonal Allergies",
        "recommendations": [
            "Over-the-counter antihistamines can provide relief",
            "Nasal irrigation with saline solution may help clear allergens"
        ],
        "avoid": [
            "Known allergens such as pollen or dust",
            "Outdoor activities during high pollen count"
        ],
        "follow_up": "If symptoms persist beyond a few weeks, consider allergy testing"
    },
    ("wheezing", "shortness of breath", "chest tightness", "coughing"): {
        "diagnosis": "Possible Asthma",
        "recommendations": [
            "Avoid known triggers like allergens or exercise if they worsen symptoms",
            "Use a rescue inhaler if prescribed by your doctor"
        ],
        "avoid": [
            "Smoking and exposure to secondhand smoke",
            "Environmental irritants such as strong perfumes or cleaning chemicals"
        ],
        "follow_up": "This condition requires proper medical evaluation and management plan"
    },
    
    # Serious Respiratory Conditions
    ("cough", "fever", "shortness of breath", "chest pain"): {
        "diagnosis": "Possible Pneumonia",
        "recommendations": [
            "Seek medical attention promptly - this could be serious",
            "Rest and stay hydrated in the meantime"
        ],
        "avoid": [
            "Delay in seeking medical care",
            "Over-exertion which can strain breathing"
        ],
        "follow_up": "This condition requires urgent professional medical evaluation"
    },
    ("sudden shortness of breath", "chest pain", "rapid breathing", "blue lips"): {
        "diagnosis": "Possible Pulmonary Embolism - MEDICAL EMERGENCY",
        "recommendations": [
            "Seek emergency medical care immediately - call 911/ambulance",
            "Remain calm and try to maintain steady breathing if possible"
        ],
        "avoid": [
            "Any delay in seeking emergency care",
            "Physical exertion of any kind"
        ],
        "follow_up": "This is a life-threatening emergency requiring immediate hospital care"
    },
    
    # Throat and ENT Conditions
    ("sore throat", "fever", "difficulty swallowing", "swollen glands"): {
        "diagnosis": "Possible Strep Throat",
        "recommendations": [
            "Gargling with salt water can temporarily relieve pain",
            "Medical evaluation for possible antibiotic treatment"
        ],
        "avoid": [
            "Acidic or spicy foods that can irritate the throat",
            "Sharing utensils or drinks with others"
        ],
        "follow_up": "See a doctor for proper diagnosis and treatment"
    },
    ("ear pain", "hearing difficulty", "fever", "ear discharge"): {
        "diagnosis": "Possible Ear Infection",
        "recommendations": [
            "Over-the-counter pain relievers for discomfort",
            "Warm compress on the affected ear"
        ],
        "avoid": [
            "Inserting anything into the ear canal",
            "Swimming or submerging the head underwater"
        ],
        "follow_up": "See a doctor if symptoms persist more than 2-3 days"
    },
    
    # Gastrointestinal Conditions
    ("abdominal pain", "diarrhea", "nausea", "vomiting"): {
        "diagnosis": "Gastroenteritis (Stomach Flu)",
        "recommendations": [
            "Stay hydrated with clear fluids sipped slowly",
            "Try the BRAT diet (bananas, rice, applesauce, toast) when able to eat"
        ],
        "avoid": [
            "Dairy products, greasy or spicy foods",
            "Caffeine and alcohol which can worsen dehydration"
        ],
        "follow_up": "If symptoms last more than 3 days or include bloody stool, see a doctor"
    },
    ("right lower abdominal pain", "nausea", "fever", "loss of appetite"): {
        "diagnosis": "Possible Appendicitis - REQUIRES MEDICAL ATTENTION",
        "recommendations": [
            "Seek immediate medical evaluation",
            "Do not take pain medications before medical evaluation"
        ],
        "avoid": [
            "Taking laxatives or using heating pads on the abdomen",
            "Eating or drinking until evaluated by a doctor"
        ],
        "follow_up": "This condition may require emergency surgery"
    },
    ("heartburn", "chest pain", "regurgitation", "bitter taste in mouth"): {
        "diagnosis": "Acid Reflux/GERD",
        "recommendations": [
            "Over-the-counter antacids can provide temporary relief",
            "Eat smaller meals and avoid lying down for 3 hours after eating"
        ],
        "avoid": [
            "Spicy, fatty, or acidic foods",
            "Alcohol, caffeine, and smoking"
        ],
        "follow_up": "If symptoms persist more than 2 weeks, consult a doctor"
    },
    
    # Cardiovascular Emergencies
    ("chest pain", "shortness of breath", "pain radiating to arm or jaw", "sweating"): {
        "diagnosis": "Possible Heart Attack - MEDICAL EMERGENCY",
        "recommendations": [
            "Call 911 or emergency services immediately",
            "Take aspirin if available and not allergic"
        ],
        "avoid": [
            "Delay in seeking emergency care",
            "Physical exertion of any kind"
        ],
        "follow_up": "This is a life-threatening emergency requiring immediate hospital care"
    },
    ("sudden weakness", "facial drooping", "difficulty speaking", "confusion"): {
        "diagnosis": "Possible Stroke - MEDICAL EMERGENCY",
        "recommendations": [
            "Call 911 or emergency services immediately",
            "Note the time symptoms began"
        ],
        "avoid": [
            "Delay in seeking emergency care",
            "Taking medications before medical evaluation"
        ],
        "follow_up": "This is a time-sensitive emergency requiring immediate hospital care"
    },
    
    # Neurological Conditions
    ("severe headache", "sensitivity to light", "nausea", "visual disturbances"): {
        "diagnosis": "Migraine",
        "recommendations": [
            "Rest in a dark, quiet room",
            "Over-the-counter pain relievers may help if taken early"
        ],
        "avoid": [
            "Bright lights and loud noises",
            "Known trigger foods like aged cheese, alcohol, or chocolate"
        ],
        "follow_up": "If migraines are frequent or debilitating, consult a neurologist"
    },
    ("sudden severe headache", "stiff neck", "fever", "confusion"): {
        "diagnosis": "Possible Meningitis - MEDICAL EMERGENCY",
        "recommendations": [
            "Seek emergency medical care immediately",
            "This is a potentially life-threatening condition"
        ],
        "avoid": [
            "Any delay in seeking emergency care",
            "Taking medications that might mask symptoms"
        ],
        "follow_up": "This requires immediate hospital evaluation and treatment"
    },
    
    # Musculoskeletal Conditions
    ("joint pain", "joint swelling", "stiffness", "limited range of motion"): {
        "diagnosis": "Possible Arthritis",
        "recommendations": [
            "Over-the-counter anti-inflammatory medications can reduce pain and swelling",
            "Applying ice for 20 minutes several times daily can help reduce inflammation"
        ],
        "avoid": [
            "Activities that cause pain or put stress on affected joints",
            "Remaining inactive for long periods which can increase stiffness"
        ],
        "follow_up": "A doctor can determine the type of arthritis and recommend treatment"
    },
    ("lower back pain", "difficulty moving", "muscle spasms", "pain radiating to legs"): {
        "diagnosis": "Lower Back Strain/Sprain",
        "recommendations": [
            "Rest the back for 1-2 days, avoiding activities that cause pain",
            "Over-the-counter pain relievers and ice packs can reduce pain and swelling"
        ],
        "avoid": [
            "Heavy lifting or twisting movements",
            "Prolonged bed rest which can weaken muscles"
        ],
        "follow_up": "If pain is severe, persists more than a week, or includes numbness, see a doctor"
    },
    
    # Dermatological Conditions
    ("rash", "itching", "redness", "skin swelling"): {
        "diagnosis": "Possible Allergic Reaction",
        "recommendations": [
            "Over-the-counter antihistamines can reduce itching and swelling",
            "Cool compresses can soothe irritated skin"
        ],
        "avoid": [
            "Scratching which can worsen symptoms and lead to infection",
            "Known allergens that may have triggered the reaction"
        ],
        "follow_up": "If symptoms include difficulty breathing or swallowing, seek emergency care"
    },
    ("painful red rash", "blisters", "tingling", "burning"): {
        "diagnosis": "Possible Shingles",
        "recommendations": [
            "See a doctor promptly - antiviral medication works best if started early",
            "Over-the-counter pain relievers can help manage pain"
        ],
        "avoid": [
            "Touching or scratching the rash",
            "Contact with pregnant women or those with weakened immune systems"
        ],
        "follow_up": "Medical evaluation is important for proper diagnosis and treatment"
    },
    
    # Urinary/Renal Conditions
    ("painful urination", "frequent urination", "urgency", "lower abdominal pain"): {
        "diagnosis": "Possible Urinary Tract Infection",
        "recommendations": [
            "Drink plenty of water to help flush bacteria",
            "See a doctor for antibiotics which are typically needed"
        ],
        "avoid": [
            "Caffeine, alcohol, and spicy foods which can irritate the bladder",
            "Delaying urination when you feel the need to go"
        ],
        "follow_up": "Complete the full course of antibiotics if prescribed"
    },
    ("flank pain", "fever", "painful urination", "cloudy urine"): {
        "diagnosis": "Possible Kidney Infection - REQUIRES PROMPT ATTENTION",
        "recommendations": [
            "Seek medical attention promptly",
            "Stay hydrated with water while awaiting medical care"
        ],
        "avoid": [
            "Delaying medical treatment which can lead to serious complications",
            "Alcohol and caffeine which can worsen dehydration"
        ],
        "follow_up": "This condition typically requires antibiotics and possibly hospitalization"
    },
    
    # Endocrine Conditions
    ("excessive thirst", "frequent urination", "fatigue", "unexplained weight loss"): {
        "diagnosis": "Possible Diabetes",
        "recommendations": [
            "See a doctor for proper evaluation and blood testing",
            "Stay hydrated with water"
        ],
        "avoid": [
            "Sugary foods and beverages",
            "Delaying medical evaluation"
        ],
        "follow_up": "This condition requires proper medical diagnosis and management"
    },
    
    # Psychiatric Emergencies
    ("suicidal thoughts", "hopelessness", "depression", "withdrawal"): {
        "diagnosis": "Possible Mental Health Crisis - REQUIRES IMMEDIATE ATTENTION",
        "recommendations": [
            "Call a crisis hotline immediately - National Suicide Prevention Lifeline: 988",
            "Do not leave the person alone if possible"
        ],
        "avoid": [
            "Dismissing or minimizing their feelings",
            "Delay in seeking professional help"
        ],
        "follow_up": "Seek professional mental health care urgently"
    }
}

def find_matching_combination(symptoms):
    """
    Find the best matching symptom combination from SYMPTOM_COMBINATIONS.
    Returns the diagnosis information from the best match.
    """
    if not symptoms or len(symptoms) < 2:
        return None
    
    # Find best matching symptom combination by scoring matches
    best_match = None
    best_match_score = 0
    best_match_key = None
    
    for combination, diagnosis_info in SYMPTOM_COMBINATIONS.items():
        # Count how many symptoms from the combination are in our symptoms list
        matched_symptoms = set(combination).intersection(set(symptoms))
        match_score = len(matched_symptoms)
        
        # Consider a match if at least 50% of symptoms in a combination match
        # or at least 3 symptoms match for larger combinations
        is_good_match = False
        if len(combination) >= 4 and match_score >= 3:
            is_good_match = True
        elif match_score >= len(combination) / 2:
            is_good_match = True
            
        # Update best match if this one has a higher score
        if is_good_match and match_score > best_match_score:
            best_match_score = match_score
            best_match = diagnosis_info
            best_match_key = combination
            
    # If we found a good match, return the diagnosis information
    if best_match:
        print(f"Matched symptom combination: {best_match_key} with score {best_match_score}")
        return best_match
    
    return None

def simple_search(query, data=MEDICAL_DATA):
    """Simple keyword-based search through medical data"""
    query = query.lower()
    results = []
    
    # Extract keywords (remove common stop words)
    stop_words = {"a", "the", "and", "or", "but", "in", "on", "at", "to", "for", "with", "about", "is", "are"}
    keywords = [word for word in re.findall(r'\b\w+\b', query) if word not in stop_words]
    
    # Search through data
    for condition, condition_data in data.items():
        score = 0
        info = condition_data["info"]
        
        for keyword in keywords:
            if keyword in condition.lower():
                score += 10  # Higher weight for matches in the condition name
            if keyword in info.lower():
                score += 1  # Lower weight for matches in the description
        
        if score > 0:
            results.append((condition, condition_data, score))
    
    # Sort by relevance score
    results.sort(key=lambda x: x[2], reverse=True)
    
    # If no results, return general health advice
    if not results:
        return """
        General Health Advice
        
        Without more specific symptoms, here are some general health recommendations:
        
        1. Maintain a balanced diet rich in fruits, vegetables, whole grains, and lean proteins.
        2. Stay hydrated by drinking plenty of water throughout the day.
        3. Get regular physical activity, aiming for at least 150 minutes of moderate activity per week.
        4. Ensure adequate sleep, typically 7-9 hours for adults.
        5. Manage stress through relaxation techniques, mindfulness, or activities you enjoy.
        6. Avoid smoking and limit alcohol consumption.
        7. Wash hands frequently to prevent the spread of illness.
        
        If you are experiencing specific symptoms, please provide more details for a more targeted response.
        """, None
    
    # Get the top result for diagnostic information
    top_condition, top_data, _ = results[0]
    
    # Combine top 2 results for display
    combined = f"Based on the query '{query}', here is the most relevant information:\n\n"
    for i, (condition, condition_data, _) in enumerate(results[:2]):
        combined += f"--- {condition.upper()} ---\n{condition_data['info']}\n\n"
    
    return combined, {
        "diagnosis": top_data["diagnosis"],
        "recommendations": top_data["recommendations"],
        "avoid": top_data["avoid"],
        "follow_up": top_data["follow_up"]
    }

def extract_symptoms_from_query(query):
    """Extract potential symptoms from the query"""
    # Enhanced comprehensive list of common symptoms to look for
    common_symptoms = [
        # Respiratory symptoms
        "fever", "cough", "sneezing", "runny nose", "congestion", "nasal congestion", "stuffy nose", 
        "sore throat", "shortness of breath", "difficulty breathing", "chest pain", "wheezing",
        "phlegm", "mucus", "post nasal drip", "hoarse voice", "loss of smell", "loss of taste",
        
        # Pain and discomfort
        "headache", "migraine", "body aches", "muscle pain", "joint pain", "back pain", "neck pain", 
        "stomach pain", "abdominal pain", "chest tightness", "ear pain", "toothache", "eye pain",
        "throat pain", "painful swallowing", "painful urination", "leg pain", "foot pain", "arm pain",
        
        # Gastrointestinal
        "nausea", "vomiting", "diarrhea", "constipation", "bloating", "gas", "indigestion", 
        "heartburn", "stomach cramps", "blood in stool", "black stool", "loss of appetite",
        "increased appetite", "difficulty swallowing", "abdominal distension", "flatulence",
        
        # Skin issues
        "rash", "hives", "itching", "swelling", "redness", "bruising", "dry skin", "blisters",
        "acne", "sweating", "excessive sweating", "night sweats", "cold sweats", "chills", "sweats",
        "jaundice", "yellowing skin", "yellowing eyes", "skin lesions", "skin peeling",
        
        # Cardiovascular
        "chest pain", "heart palpitations", "rapid heartbeat", "irregular heartbeat", "slow heartbeat",
        "high blood pressure", "low blood pressure", "dizziness", "fainting", "lightheadedness",
        "swollen ankles", "swollen feet", "swollen legs", "calf pain", "claudication",
        
        # Neurological
        "dizziness", "vertigo", "confusion", "memory loss", "forgetfulness", "seizure", "tremor",
        "tingling", "numbness", "weakness", "paralysis", "difficulty speaking", "slurred speech",
        "double vision", "blurred vision", "loss of balance", "poor coordination", "difficulty walking",
        
        # Psychological
        "anxiety", "depression", "mood swings", "irritability", "fatigue", "tiredness", "insomnia", 
        "difficulty sleeping", "excessive sleeping", "nightmares", "stress", "panic attacks", 
        "hallucinations", "paranoia", "feeling sad", "feeling worried", "mental confusion",
        
        # Urinary/Renal
        "frequent urination", "painful urination", "blood in urine", "dark urine", "cloudy urine",
        "foul-smelling urine", "urgency to urinate", "difficulty urinating", "incontinence",
        "decreased urination", "flank pain", "kidney pain",
        
        # Reproductive/Menstrual
        "irregular periods", "heavy periods", "painful periods", "missed periods", "vaginal discharge",
        "vaginal bleeding", "vaginal dryness", "testicular pain", "erectile dysfunction", "genital sores",
        "genital itching", "genital burning", "genital rash", "pelvic pain", "cramping",
        
        # General
        "weight loss", "weight gain", "fever", "fatigue", "weakness", "tired", "malaise", "chills",
        "night sweats", "swollen glands", "swollen lymph nodes", "dehydration", "thirst", "excessive thirst",
        "lethargy", "feeling unwell", "body aches", "discomfort", "disorientation"
    ]
    
    # Check for symptoms in the query
    found_symptoms = []
    query_lower = query.lower()
    
    # First pass: exact matches
    for symptom in common_symptoms:
        if symptom in query_lower:
            found_symptoms.append(symptom)
    
    # Remove overlapping symptoms (keep the most specific one)
    # For example, if both "runny nose" and "nose" are found, keep only "runny nose"
    final_symptoms = []
    for symptom in found_symptoms:
        should_add = True
        for other_symptom in found_symptoms:
            if symptom != other_symptom and symptom in other_symptom:
                should_add = False
                break
        if should_add:
            final_symptoms.append(symptom)
    
    return final_symptoms

def Rag(query):
    """Function to query the RAG system and get information with improved symptom matching."""
    try:
        # Check if query is symptoms for matching with combinations
        query_symptoms = extract_symptoms_from_query(query)
        
        # If we found symptoms in the query, try to match against combinations
        if query_symptoms and len(query_symptoms) >= 2:
            # First try to find matching combinations
            combination_match = find_matching_combination(query_symptoms)
            if combination_match:
                # Update demographic data with the match
                with open("Data/demographic.json", "w") as f:
                    json.dump({
                        "symptoms": query_symptoms,
                        "diagnosis": combination_match.get("diagnosis", "Unknown"),
                        "recommendations": combination_match.get("recommendations", []),
                        "avoid": combination_match.get("avoid", []),
                        "follow_up": combination_match.get("follow_up", "")
                    }, f, indent=4)
                
                # Return formatted information
                diagnosis_info = f"""
                Based on your symptoms ({', '.join(query_symptoms)}), you may have:
                
                {combination_match.get('diagnosis', 'Unknown condition')}
                
                Recommendations:
                - {combination_match.get('recommendations', [''])[0] if combination_match.get('recommendations') else ''}
                - {combination_match.get('recommendations', ['', ''])[1] if len(combination_match.get('recommendations', [])) > 1 else ''}
                
                Please avoid:
                - {combination_match.get('avoid', [''])[0] if combination_match.get('avoid') else ''}
                - {combination_match.get('avoid', ['', ''])[1] if len(combination_match.get('avoid', [])) > 1 else ''}
                
                Follow-up: {combination_match.get('follow_up', '')}
                """
                return diagnosis_info
        
        # If no combination match or not enough symptoms, use traditional search
        result, search_diagnosis_info = simple_search(query)
        
        # Update demographic data with the search results
        if query_symptoms:
            with open("Data/demographic.json", "w") as f:
                json.dump({
                    "symptoms": query_symptoms,
                    "diagnosis": search_diagnosis_info.get("diagnosis", "Unknown"),
                    "recommendations": search_diagnosis_info.get("recommendations", []),
                    "avoid": search_diagnosis_info.get("avoid", []),
                    "follow_up": search_diagnosis_info.get("follow_up", "")
                }, f, indent=4)
        
        return result
    except Exception as e:
        print(f"Error in RAG function: {e}")
        return "Unable to retrieve medical information at this time."

if __name__ == "__main__":
    # Interactive testing mode
    print("Simple RAG System - Test Mode")
    print("Enter medical queries (or 'exit' to quit)")
    while True:
        user_query = input("\nQuery: ")
        if user_query.lower() == 'exit':
            break
        result = Rag(user_query)
        print("\n" + "="*80)
        print(result)
        print("="*80) 