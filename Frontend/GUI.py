import sys
import os
import json
import re
import traceback
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QStackedWidget, QWidget, QLineEdit, QGridLayout, QVBoxLayout, QHBoxLayout, QPushButton, QFrame, QLabel, QSizePolicy, QFileDialog, QScrollArea
from PyQt5.QtGui import QIcon, QPainter, QMovie, QColor, QTextCharFormat, QFont, QPixmap, QTextBlockFormat, QPainterPath
from PyQt5.QtCore import Qt, QSize, QTimer, QRect, QPoint
from dotenv import dotenv_values
from time import sleep

env_vars = dotenv_values(".env")
Assistantname = "DocBot"
username = env_vars.get("Username", "User")
current_dir = os.getcwd()
old_chat_message = ""
TempDirPath = rf"{current_dir}\Frontend\Files"
GraphicsDirPath = rf"{current_dir}\Frontend\Graphics"

def TempDictonaryPath(Filename):
    return rf"{TempDirPath}\{Filename}"

def AnswerModifier(Answer):
    lines = Answer.split("\n")
    non_empty_lines = [line for line in lines if line.strip()]
    return "\n".join(non_empty_lines)

def QueryModifier(Query):
    new_query = Query.lower().strip()
    query_words = new_query.split()
    question_words = ["how", "what", "when", "where", "who", "which", "why", "can you", "whom", "whose", "what's", "where's"]
    if any(word + " " in new_query for word in question_words):
        new_query = new_query[:-1] + "?" if query_words[-1][-1] in [".", "?", "!"] else new_query + "?"
    else:
        new_query = new_query[:-1] + "." if query_words[-1][-1] in [".", "?", "!"] else new_query + "."
    return new_query.capitalize()

def SetMicrophoneStatus(Command):
    with open(rf"{TempDirPath}\Mic.data", "w", encoding="utf-8") as file:
        file.write(Command)

def GetMicrophoneStatus():
    with open(rf"{TempDirPath}\Mic.data", "r", encoding="utf-8") as file:
        return file.read()

def SetAssistantStatus(Status):
    with open(rf"{TempDirPath}\Status.data", "w", encoding="utf-8") as file:
        file.write(Status)

def GetAssistantStatus():
    with open(rf"{TempDirPath}\Status.data", "r", encoding="utf-8") as file:
        return file.read()

def SetTextInput(text):
    with open(rf"{TempDirPath}\TextInput.data", "w", encoding="utf-8") as file:
        file.write(text)

def GetTextInput():
    with open(rf"{TempDirPath}\TextInput.data", "r", encoding="utf-8") as file:
        text = file.read().strip()
        if text and text != "None":
            return text
    return ""

def GraphicsDictonaryPath(Filename):
    return rf"{GraphicsDirPath}\{Filename}"

def ShowTextToScreen(Text):
    with open(rf"{TempDirPath}\Responses.data", "w", encoding="utf-8") as file:
        file.write(Text)

class MessageBubble(QFrame):
    def __init__(self, message, is_user=False, parent=None):
        super().__init__(parent)
        self.message = message
        self.is_user = is_user
        self.initUI()
        
    def initUI(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 2, 10, 2)  # Reduced vertical margins
        layout.setSpacing(0)
        
        if self.is_user:
            layout.addStretch(5)  # Push user messages further right
            bubble_color = "#4a90e2"  # Blue for user messages
        else:
            bubble_color = "#2b2b2b"  # Dark gray for AI messages
            
        # Create a bubble container
        bubble = QFrame(self)
        bubble.setStyleSheet(f"""
            background-color: {bubble_color};
            border-radius: 18px;
            padding: 10px;
        """)
        
        # Message text label
        text_label = QLabel(self.message)
        text_label.setWordWrap(True)
        text_label.setStyleSheet("""
            color: white;
            font-size: 14px;
            padding: 5px;
            background: transparent;
        """)
        
        # Add text to bubble
        bubble_layout = QVBoxLayout(bubble)
        bubble_layout.setContentsMargins(12, 6, 12, 6)  # Reduced vertical padding
        bubble_layout.addWidget(text_label)
        
        # Make bubbles much wider to reduce wrapping
        bubble.setMaximumWidth(1200)  # Much wider maximum
        
        # Set a large minimum width to force horizontal spread
        # Calculate min width based on message length but with a higher multiplier
        # to encourage horizontal spread
        min_width = max(400, min(len(self.message) * 15, 1000))
        bubble.setMinimumWidth(min_width)
        
        layout.addWidget(bubble)
        
        if not self.is_user:
            layout.addStretch(5)  # Push AI messages further left
            
        self.setStyleSheet("background: transparent;")
        self.setMaximumWidth(2000)  # Very large maximum width

class ChatContainer(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        
    def initUI(self):
        # Main widget that will contain all messages
        self.container = QWidget()
        self.container.setObjectName("chatContainer")
        self.container.setStyleSheet("""
            #chatContainer {
                background-color: #1a1a1a;
            }
        """)
        
        # Layout for messages
        self.messages_layout = QVBoxLayout(self.container)
        self.messages_layout.setAlignment(Qt.AlignTop)
        self.messages_layout.setSpacing(8)  # Reduced spacing between messages
        self.messages_layout.setContentsMargins(20, 20, 20, 20)  # Increased horizontal margins
        
        # Add stretch at the bottom to keep messages at the top when there are few
        self.messages_layout.addStretch()
        
        # Configure scroll area
        self.setWidget(self.container)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setStyleSheet("""
            QScrollArea {
                background-color: #1a1a1a;
                border: none;
                border-radius: 15px;
            }
            QScrollBar:vertical {
                border: none;
                background: #1a1a1a;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #4a90e2;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #357abd;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        
    def addMessage(self, message, message_type):
        # Remove the stretch at the bottom
        self.messages_layout.removeItem(self.messages_layout.itemAt(self.messages_layout.count() - 1))
        
        # Add new message
        is_user = (message_type == "user")
        bubble = MessageBubble(message, is_user)
        self.messages_layout.addWidget(bubble)
        
        # Add stretch back at the bottom
        self.messages_layout.addStretch()
        
        # Scroll to bottom
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())

class ChatSection(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 40, 5, 100)  # Minimal horizontal margins
        
        # Main section with chat and diagnosis side by side
        main_section = QHBoxLayout()
        
        # Create chat container with expanded width but now with some room for diagnosis
        self.chat_container = ChatContainer()
        self.chat_container.setMinimumWidth(1200)  # Reduced width to make room for diagnosis
        main_section.addWidget(self.chat_container, 7)  # Chat takes 70% of width
        
        # Create diagnosis panel with enhanced modern styling
        self.diagnosis_panel = QFrame()
        self.diagnosis_panel.setObjectName("diagnosisPanel")
        self.diagnosis_panel.setStyleSheet("""
            #diagnosisPanel {
                background-color: #2b2b2b;
                border-radius: 20px;
                padding: 15px;
                margin-left: 15px;
                border: 1px solid #3a3a3a;
            }
            QLabel {
                color: white;
                font-size: 16px;
            }
            QLabel#diagnosisTitle {
                color: #4a90e2;
                font-size: 24px;
                font-weight: bold;
                margin-bottom: 15px;
                border-bottom: 2px solid #4a90e2;
                padding-bottom: 10px;
            }
            QLabel#diagnosisSubtitle {
                color: #4a90e2;
                font-size: 18px;
                font-weight: bold;
                margin-top: 15px;
                margin-bottom: 8px;
                padding: 8px;
                background-color: #363636;
                border-radius: 8px;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #2b2b2b;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #4a90e2;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #357abd;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
            QWidget#scrollContent {
                background-color: transparent;
            }
        """)
        
        main_diagnosis_layout = QVBoxLayout(self.diagnosis_panel)
        main_diagnosis_layout.setContentsMargins(0, 0, 0, 0)
        
        # Title at the top (outside scroll area)
        title_label = QLabel("Patient Diagnosis")
        title_label.setObjectName("diagnosisTitle")
        title_label.setAlignment(Qt.AlignCenter)
        main_diagnosis_layout.addWidget(title_label)
        
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Create widget to hold scrollable content
        scroll_content = QWidget()
        scroll_content.setObjectName("scrollContent")
        diagnosis_layout = QVBoxLayout(scroll_content)
        diagnosis_layout.setSpacing(8)
        diagnosis_layout.setContentsMargins(15, 0, 15, 0)
        
        # Symptoms section
        symptoms_title = QLabel("Symptoms:")
        symptoms_title.setObjectName("diagnosisSubtitle")
        diagnosis_layout.addWidget(symptoms_title)
        
        self.symptoms_label = QLabel("No symptoms recorded yet")
        self.symptoms_label.setWordWrap(True)
        self.symptoms_label.setStyleSheet("""
            padding: 12px 16px;
            background-color: #333333;
            border-radius: 8px;
            margin: 5px 0px;
            font-size: 16px;
            line-height: 1.4;
            min-height: 40px;
        """)
        self.symptoms_label.setTextFormat(Qt.RichText)
        diagnosis_layout.addWidget(self.symptoms_label)
        
        # Diagnosis section
        diagnosis_title = QLabel("Likely Condition:")
        diagnosis_title.setObjectName("diagnosisSubtitle")
        diagnosis_layout.addWidget(diagnosis_title)
        
        self.diagnosis_label = QLabel("Pending diagnosis")
        self.diagnosis_label.setWordWrap(True)
        self.diagnosis_label.setStyleSheet("""
            padding: 12px 16px;
            background-color: #333333;
            border-radius: 8px;
            margin: 5px 0px;
            font-size: 16px;
            line-height: 1.4;
            min-height: 40px;
        """)
        self.diagnosis_label.setTextFormat(Qt.RichText)
        diagnosis_layout.addWidget(self.diagnosis_label)
        
        # Recommendations section
        recommendations_title = QLabel("Recommendations:")
        recommendations_title.setObjectName("diagnosisSubtitle")
        diagnosis_layout.addWidget(recommendations_title)
        
        self.recommendations_label = QLabel("Pending recommendations")
        self.recommendations_label.setWordWrap(True)
        self.recommendations_label.setStyleSheet("""
            padding: 12px 16px;
            background-color: #333333;
            border-radius: 8px;
            margin: 5px 0px;
            font-size: 16px;
            line-height: 1.4;
            min-height: 40px;
        """)
        self.recommendations_label.setTextFormat(Qt.RichText)
        diagnosis_layout.addWidget(self.recommendations_label)
        
        # Avoid section
        avoid_title = QLabel("Avoid:")
        avoid_title.setObjectName("diagnosisSubtitle")
        diagnosis_layout.addWidget(avoid_title)
        
        self.avoid_label = QLabel("Pending advice")
        self.avoid_label.setWordWrap(True)
        self.avoid_label.setStyleSheet("""
            padding: 12px 16px;
            background-color: #333333;
            border-radius: 8px;
            margin: 5px 0px;
            font-size: 16px;
            line-height: 1.4;
            min-height: 40px;
        """)
        self.avoid_label.setTextFormat(Qt.RichText)
        diagnosis_layout.addWidget(self.avoid_label)
        
        # Follow-up section
        followup_title = QLabel("Follow-up:")
        followup_title.setObjectName("diagnosisSubtitle")
        diagnosis_layout.addWidget(followup_title)
        
        self.followup_label = QLabel("Pending follow-up advice")
        self.followup_label.setWordWrap(True)
        self.followup_label.setStyleSheet("""
            padding: 12px 16px;
            background-color: #333333;
            border-radius: 8px;
            margin: 5px 0px;
            font-size: 16px;
            line-height: 1.4;
            min-height: 40px;
        """)
        self.followup_label.setTextFormat(Qt.RichText)
        diagnosis_layout.addWidget(self.followup_label)
        
        # Note at the bottom of scrollable area
        note_label = QLabel("AI-generated summary for professional reference only")
        note_label.setWordWrap(True)
        note_label.setStyleSheet("""
            color: #999999; 
            font-style: italic; 
            font-size: 14px;
            padding: 12px;
            margin-top: 15px;
            background-color: rgba(74, 144, 226, 0.1);
            border-radius: 8px;
            border-left: 3px solid #4a90e2;
            line-height: 1.4;
        """)
        diagnosis_layout.addWidget(note_label)
        
        # Add stretch at the bottom
        diagnosis_layout.addStretch()
        
        # Set the scroll content and add to main layout
        scroll_area.setWidget(scroll_content)
        main_diagnosis_layout.addWidget(scroll_area)
        
        main_section.addWidget(self.diagnosis_panel, 3)  # Diagnosis takes 30% of width
        
        layout.addLayout(main_section)

        # Input section with better styling
        input_container = QWidget()
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(0, 10, 0, 10)
        input_layout.setSpacing(10)  # Add spacing between input and button

        # Add doctor recommendation button in bottom left
        self.recommend_doctor_btn = QPushButton("Recommend Doctor")
        self.recommend_doctor_btn.setMinimumHeight(45)
        self.recommend_doctor_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border-radius: 22px;
                padding: 5px 20px;
                font-size: 14px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background-color: #357abd;
            }
            QPushButton:pressed {
                background-color: #2d6da3;
            }
            QPushButton:disabled {
                background-color: #555555;
                color: #999999;
            }
        """)
        self.recommend_doctor_btn.clicked.connect(self.recommend_doctor)
        input_layout.addWidget(self.recommend_doctor_btn)

        # Textbox for input with improved styling
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Type your symptoms here...")
        self.text_input.setMinimumHeight(45)
        self.text_input.setStyleSheet("""
            QLineEdit {
                background-color: #2b2b2b;
                color: white;
                border-radius: 22px;
                padding: 5px 20px;
                font-size: 14px;
                border: 1px solid #333333;
            }
            QLineEdit:focus {
                border: 1px solid #4a90e2;
            }
            QLineEdit::placeholder {
                color: #888888;
            }
        """)
        self.text_input.returnPressed.connect(self.submit_text)
        input_layout.addWidget(self.text_input)
        
        # --- Add Send Button --- 
        self.send_button = QPushButton("Send")
        self.send_button.setMinimumHeight(45)
        self.send_button.setFixedWidth(80) # Fixed width for the send button
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border-radius: 22px;
                padding: 5px 15px;
                font-size: 14px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background-color: #357abd;
            }
            QPushButton:pressed {
                background-color: #2d6da3;
            }
        """)
        self.send_button.clicked.connect(self.submit_text)
        input_layout.addWidget(self.send_button)
        # --- End Send Button ---

        layout.addWidget(input_container)
        
        # Doctor recommendation popup
        self.doctor_card = QFrame(self)
        self.doctor_card.setObjectName("doctorCard")
        self.doctor_card.setStyleSheet("""
            #doctorCard {
                background-color: #2b2b2b;
                border-radius: 15px;
                border: 1px solid #4a90e2;
                min-width: 300px;
                max-width: 400px;
            }
            QLabel#doctorName {
                color: #4a90e2;
                font-size: 18px;
                font-weight: bold;
                background-color: transparent;
            }
            QLabel#doctorSpec {
                color: white;
                font-size: 16px;
                font-weight: bold;
                background-color: transparent;
            }
            QLabel#doctorDetails {
                color: #cccccc;
                font-size: 14px;
                background-color: transparent;
            }
            QLabel#doctorLabel {
                color: #999999;
                font-size: 12px;
                background-color: transparent;
            }
            QPushButton#closeButton {
                background-color: transparent;
                color: #999999;
                border: none;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton#closeButton:hover {
                color: white;
            }
        """)
        
        doctor_layout = QVBoxLayout(self.doctor_card)
        
        # Header with close button
        header_layout = QHBoxLayout()
        recommendation_label = QLabel("Recommended Specialist")
        recommendation_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold; background-color: transparent;")
        close_button = QPushButton("×")
        close_button.setObjectName("closeButton")
        close_button.clicked.connect(self.hide_doctor_card)
        close_button.setFixedSize(30, 30)
        
        header_layout.addWidget(recommendation_label)
        header_layout.addWidget(close_button, alignment=Qt.AlignRight)
        doctor_layout.addLayout(header_layout)
        
        # Doctor details
        self.doctor_name = QLabel("Dr. Name")
        self.doctor_name.setObjectName("doctorName")
        doctor_layout.addWidget(self.doctor_name)
        
        self.doctor_spec = QLabel("Specialization")
        self.doctor_spec.setObjectName("doctorSpec")
        doctor_layout.addWidget(self.doctor_spec)
        
        # Additional details
        details_layout = QGridLayout()
        
        exp_label = QLabel("Experience:")
        exp_label.setObjectName("doctorLabel")
        self.exp_value = QLabel("15 years")
        self.exp_value.setObjectName("doctorDetails")
        details_layout.addWidget(exp_label, 0, 0)
        details_layout.addWidget(self.exp_value, 0, 1)
        
        qualif_label = QLabel("Qualifications:")
        qualif_label.setObjectName("doctorLabel")
        self.qualif_value = QLabel("MBBS, MD")
        self.qualif_value.setObjectName("doctorDetails")
        details_layout.addWidget(qualif_label, 1, 0)
        details_layout.addWidget(self.qualif_value, 1, 1)
        
        loc_label = QLabel("Location:")
        loc_label.setObjectName("doctorLabel")
        self.loc_value = QLabel("New Delhi")
        self.loc_value.setObjectName("doctorDetails")
        details_layout.addWidget(loc_label, 2, 0)
        details_layout.addWidget(self.loc_value, 2, 1)
        
        hours_label = QLabel("Hours:")
        hours_label.setObjectName("doctorLabel")
        self.hours_value = QLabel("9:00 - 17:00")
        self.hours_value.setObjectName("doctorDetails")
        details_layout.addWidget(hours_label, 3, 0)
        details_layout.addWidget(self.hours_value, 3, 1)
        
        doctor_layout.addLayout(details_layout)
        
        # Add some padding
        doctor_layout.setContentsMargins(20, 15, 20, 15)
        doctor_layout.setSpacing(10)
        
        # Position in bottom left (will be shown/hidden as needed)
        self.doctor_card.setGeometry(50, self.height() - 450, 350, 300)
        self.doctor_card.hide()
        
        # Initial state of recommendation button (disabled if no diagnosis)
        self.update_recommend_btn_state()

        self.setStyleSheet("background-color: black;")
        
        # GIF setup
        self.gif_label = QLabel()
        movie = QMovie(GraphicsDictonaryPath("Jarvis.gif"))
        movie.setScaledSize(QSize(480, 270))
        self.gif_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        self.gif_label.setMovie(movie)
        movie.start()
        layout.addWidget(self.gif_label)
        
        # Status text and mic button container
        status_container = QWidget()
        status_layout = QHBoxLayout(status_container)
        status_layout.setContentsMargins(0, 0, 0, 0)
        
        # Status text
        self.label = QLabel("")
        self.label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 14px;
                margin-right: 195px;
                font-style: italic;
            }
        """)
        self.label.setAlignment(Qt.AlignRight)
        status_layout.addWidget(self.label)
        
        # Mic button
        self.mic_button = QPushButton()
        self.mic_button.setFixedSize(50, 50)
        self.mic_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 25px;
            }
            QPushButton:hover {
                background-color: #333333;
            }
        """)
        self.mic_toggled = True
        self.update_mic_icon()
        self.mic_button.clicked.connect(self.toggle_mic)
        status_layout.addWidget(self.mic_button)
        
        layout.addWidget(status_container)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.loadMessages)
        self.timer.timeout.connect(self.SpeechRecogText)
        self.timer.timeout.connect(self.updateDiagnosisPanel)
        self.timer.start(1000)  # Update every 1 second instead of 5ms - this is more efficient

    def update_mic_icon(self):
        icon_path = GraphicsDictonaryPath("Mic_on.png" if self.mic_toggled else "Mic_off.png")
        self.mic_button.setIcon(QIcon(icon_path))
        self.mic_button.setIconSize(QSize(40, 40))

    def toggle_mic(self):
        self.mic_toggled = not self.mic_toggled
        self.update_mic_icon()
        SetMicrophoneStatus("False" if self.mic_toggled else "True")

    def loadMessages(self):
        global old_chat_message
        with open(TempDictonaryPath("Responses.data"), "r", encoding="utf-8") as file:
            messages = file.read()
            if messages and messages != old_chat_message:
                # Split messages into user and AI messages
                lines = messages.split('\n')
                for line in lines:
                    if line.strip():
                        if line.startswith(f"{username} :"):
                            # User message
                            message = line.replace(f"{username} :", "").strip()
                            self.chat_container.addMessage(message, "user")
                        elif line.startswith(f"{Assistantname} :"):
                            # AI message
                            message = line.replace(f"{Assistantname} :", "").strip()
                            self.chat_container.addMessage(message, "ai")
                old_chat_message = messages

    def SpeechRecogText(self):
        with open(TempDictonaryPath("Status.data"), "r", encoding="utf-8") as file:
            self.label.setText(file.read())

    def submit_text(self):
        text = self.text_input.text().strip()
        if text:
            # --- Add message to GUI immediately ---
            self.chat_container.addMessage(text, "user") 
            # --------------------------------------
            SetTextInput(text) # Send to backend
            self.text_input.clear()

    def updateDiagnosisPanel(self):
        """Update the diagnosis panel with information from demographic.json"""
        try:
            if os.path.exists("Data/demographic.json"):
                with open("Data/demographic.json", "r") as f:
                    data = json.load(f)
                
                # Update symptoms - Display as bullet points (always in real-time)
                symptoms_list = data.get("symptoms", [])
                if symptoms_list:
                    # Format as bullet points with line breaks and remove asterisks
                    cleaned_symptoms = [s.strip().replace("*", "") for s in symptoms_list]
                    symptoms_text = "<br>".join([f"• {s}" for s in cleaned_symptoms])
                    self.symptoms_label.setText(symptoms_text)
                else:
                    self.symptoms_label.setText("No symptoms recorded yet") # Clear if empty

                # Update diagnosis - Only show the precise diagnosis from RAG
                diagnosis = data.get("diagnosis", "")
                
                if diagnosis and diagnosis.strip() and diagnosis.lower() != "unknown":
                    # Store current diagnosis before updating
                    previous_diagnosis = getattr(self, '_previous_diagnosis', "")
                    
                    # Set diagnosis label to show just the condition name
                    self.diagnosis_label.setText(diagnosis.strip())
                    
                    # Check if this is a new/changed diagnosis - if so, update doctor recommendation
                    if diagnosis != previous_diagnosis and previous_diagnosis != "":
                        print(f"Final diagnosis changed from '{previous_diagnosis}' to '{diagnosis}'. Updating doctor recommendation.")
                        QTimer.singleShot(500, self.recommend_doctor)  # Schedule doctor recommendation to run after a slight delay
                    
                    # Store the current diagnosis for comparison next time
                    self._previous_diagnosis = diagnosis
                else:
                    self.diagnosis_label.setText("Pending diagnosis") # Default message when no diagnosis
                    self._previous_diagnosis = ""

                self.update_recommend_btn_state()

                # Update recommendations - Make them concise (2-3 lines)
                recommendations_list = data.get("recommendations", [])
                if recommendations_list:
                    # Limit to 2-3 most important recommendations
                    important_recs = []
                    med_count = 0
                    
                    # First include medication recommendations, limited to 2
                    for rec in recommendations_list:
                        rec = rec.strip()
                        # Remove asterisks completely
                        rec = rec.replace("*", "")
                        
                        # Check if this is a medication recommendation
                        if ":" in rec and any(med in rec.lower() for med in ["mg", "acetaminophen", "ibuprofen", "tylenol", "advil", "dose", "capsule", "tablet"]):
                            if med_count < 2:  # Limit to 2 medication recommendations
                                parts = rec.split(":", 1)
                                if len(parts) == 2:
                                    med_name = parts[0].strip()
                                    dosage = parts[1].strip()
                                    # Clean up "this is not a prescription" text
                                    dosage = re.sub(r'this is not a prescription[^.]*\.', '', dosage, flags=re.IGNORECASE).strip()
                                    important_recs.append(f"• <b>{med_name}</b>: {dosage}")
                                    med_count += 1
                        # Add one lifestyle/general recommendation
                        elif len(important_recs) < 3 and "follow package instructions" not in rec.lower() and "not a prescription" not in rec.lower():
                            important_recs.append(f"• {rec}")
                    
                    # Ensure we have something
                    if not important_recs and recommendations_list:
                        important_recs = [f"• {recommendations_list[0].replace('*', '')}"]
                    
                    # Join with HTML line breaks for proper formatting
                    recommendations_text = "<br>".join(important_recs)
                    self.recommendations_label.setText(recommendations_text)
                else:
                    self.recommendations_label.setText("Pending recommendations") # Clear if empty

                # Update avoid - Keep brief
                avoid_list = data.get("avoid", [])
                if avoid_list:
                    # Limit to 2 most important items to avoid
                    important_avoids = [f"• {a.strip().replace('*', '')}" for a in avoid_list[:2]]
                    avoid_text = "<br>".join(important_avoids)
                    self.avoid_label.setText(avoid_text)
                else:
                    self.avoid_label.setText("Pending advice") # Clear if empty

                # Update follow-up - Keep brief and remove redundancy
                follow_up = data.get("follow_up", "")
                if follow_up and follow_up.strip():
                    # Remove redundant "consult a doctor" if it's the only advice
                    if "consult" in follow_up.lower() and "doctor" in follow_up.lower() and len(follow_up) > 60:
                        follow_up = "Monitor symptoms and seek medical attention if condition worsens."
                    self.followup_label.setText(follow_up)
                else:
                    self.followup_label.setText("Monitor symptoms for changes") # Simple default
        except json.JSONDecodeError:
            print("Error: Could not decode demographic.json. File might be corrupted or empty.")
            # Optionally clear the panel or show an error state
            self.symptoms_label.setText("Error loading data")
            self.diagnosis_label.setText("Error loading data")
            self.recommendations_label.setText("Error loading data")
            self.avoid_label.setText("Error loading data")
            self.followup_label.setText("Error loading data")
        except Exception as e:
            print(f"Error updating diagnosis panel: {e}")
            traceback.print_exc()
    
    def update_recommend_btn_state(self):
        """Enable/disable doctor recommendation button based on diagnosis"""
        try:
            if os.path.exists("Data/demographic.json"):
                with open("Data/demographic.json", "r") as f:
                    data = json.load(f)
                
                if data.get("diagnosis") and data["diagnosis"].strip():
                    self.recommend_doctor_btn.setEnabled(True)
                else:
                    self.recommend_doctor_btn.setEnabled(False)
        except Exception as e:
            print(f"Error updating recommendation button state: {e}")
            self.recommend_doctor_btn.setEnabled(False)
    
    def recommend_doctor(self):
        """Show doctor recommendation based on current diagnosis"""
        try:
            # Get current diagnosis
            with open("Data/demographic.json", "r") as f:
                data = json.load(f)
            
            if not data.get("diagnosis"):
                return
                
            diagnosis = data["diagnosis"].lower()
            symptoms = [s.lower() for s in data.get("symptoms", [])]
            
            print(f"Finding specialist for diagnosis: {diagnosis}, symptoms: {symptoms}")
            
            # --- Get Recommended Specialist Type from Gemini (via demographic.json) ---
            recommended_type = data.get("recommended_specialist_type", "Cardiologist")
            print(f"Gemini recommended specialist type: {recommended_type}")
            # --- End Recommended Specialist Type ---

            # Load doctors data
            try:
                with open("Data/doctorsdata.json", "r") as f:
                    doctors = json.load(f)
            except FileNotFoundError:
                print("Doctor data file not found, creating sample data")
                # Create sample doctors data - REAL DOCTORS ONLY, NO AI
                doctors = [
                    {
                        "id": 1,
                        "name": "John Smith",
                        "specialization": "Pulmonologist",
                        "specialties": ["flu", "fever", "cold", "cough", "general illness", "headache", "sore throat"],
                        "experience": 12,
                        "qualifications": ["MBBS", "MD"],
                        "officeLocation": {"city": "New Delhi"},
                        "workingHours": {"monday": {"start": "9:00", "end": "17:00"}}
                    },
                    {
                        "id": 2,
                        "name": "Sarah Johnson",
                        "specialization": "Pulmonologist",
                        "specialties": ["pneumonia", "asthma", "respiratory", "lung", "bronchitis", "persistent cough", "breathing difficulty"], # Added more lung symptoms
                        "experience": 15,
                        "qualifications": ["MBBS", "MD", "DM"],
                        "officeLocation": {"city": "Mumbai"},
                        "workingHours": {"monday": {"start": "10:00", "end": "18:00"}}
                    },
                    {
                        "id": 3,
                        "name": "Raj Patel",
                        "specialization": "Cardiologist",
                        "specialties": ["heart", "chest pain", "blood pressure", "cardiac", "palpitations", "dizziness"], # Added heart symptoms
                        "experience": 20,
                        "qualifications": ["MBBS", "MD", "DM"],
                        "officeLocation": {"city": "Bangalore"},
                        "workingHours": {"monday": {"start": "8:00", "end": "16:00"}}
                    },
                    {
                        "id": 4,
                        "name": "Priya Sharma",
                        "specialization": "ENT Specialist",
                        "specialties": ["throat", "ear", "nose", "sinusitis", "tonsillitis", "sore throat", "ear pain", "hearing loss", "nasal congestion"], # Added ENT symptoms
                        "experience": 10,
                        "qualifications": ["MBBS", "MS"],
                        "officeLocation": {"city": "Hyderabad"},
                        "workingHours": {"monday": {"start": "9:30", "end": "17:30"}}
                    },
                    {
                        "id": 5,
                        "name": "Amit Kumar",
                        "specialization": "Urologist",
                        "specialties": ["urinary tract infection", "uti", "kidney stones", "bladder", "prostate", "painful urination", "blood in urine"], # Added UTI/Urology symptoms
                        "experience": 15,
                        "qualifications": ["MBBS", "MS", "MCh"],
                        "officeLocation": {"city": "Delhi"},
                        "workingHours": {"monday": {"start": "10:00", "end": "18:00"}}
                    },
                    {
                        "id": 6,
                        "name": "Meera Reddy",
                        "specialization": "Nephrologist",
                        "specialties": ["kidney disease", "renal failure", "hypertension", "dialysis", "proteinuria", "swelling"], # Added Kidney symptoms
                        "experience": 12,
                        "qualifications": ["MBBS", "MD", "DM"],
                        "officeLocation": {"city": "Chennai"},
                        "workingHours": {"monday": {"start": "9:00", "end": "17:00"}}
                    }
                ]
                # Save sample data if it was created
                if not os.path.exists("Data/doctorsdata.json"):
                    os.makedirs("Data", exist_ok=True)
                    with open("Data/doctorsdata.json", "w") as f:
                        json.dump(doctors, f, indent=4)
            
            # --- Improved Doctor Matching Logic ---
            best_match_doctor = None
            print(f"Looking for specialist type: '{recommended_type}'") # Debug print
            
            # 1. First attempt: Direct specialty match
            matching_doctors = []
            for doctor in doctors:
                specialization = doctor.get("specialization", "").strip()
                if specialization.lower() == recommended_type.lower():
                    matching_doctors.append(doctor)
            
            # 2. Second attempt: Partial specialty match if no exact match
            if not matching_doctors:
                print(f"No exact specialty match found, trying partial matches")
                for doctor in doctors:
                    specialization = doctor.get("specialization", "").strip()
                    # Check if recommended type contains the specialization or vice versa
                    if (recommended_type.lower() in specialization.lower() or 
                        specialization.lower() in recommended_type.lower()):
                        matching_doctors.append(doctor)
            
            # 3. Third attempt: Match by symptoms against doctor specialties
            if not matching_doctors:
                print(f"No specialty matches found, matching by symptoms")
                doctor_scores = []
                
                for doctor in doctors:
                    doctor_specialties = [s.lower() for s in doctor.get("specialties", [])]
                    score = 0
                    
                    # Match symptoms against doctor's specialties
                    for symptom in symptoms:
                        symptom_lower = symptom.lower()
                        for specialty in doctor_specialties:
                            # Check if symptom contains specialty or vice versa
                            if symptom_lower in specialty or specialty in symptom_lower:
                                score += 1
                    
                    # Match diagnosis against doctor's specialties            
                    for specialty in doctor_specialties:
                        if specialty in diagnosis:
                            score += 2  # Higher weight for diagnosis match
                    
                    # Store doctor with their match score
                    if score > 0:
                        doctor_scores.append((doctor, score))
                
                # Sort by score (highest first)
                if doctor_scores:
                    doctor_scores.sort(key=lambda x: x[1], reverse=True)
                    print(f"Found {len(doctor_scores)} doctors with symptom matches: {[(d[0].get('name'), d[1]) for d in doctor_scores[:3]]}")
                    matching_doctors = [d[0] for d in doctor_scores]
            
            # 4. Final fallback: Use Pulmonologist (since we have no General Physician)
            if not matching_doctors:
                print("No matches found, trying Pulmonologist fallback")
                for doctor in doctors:
                    if doctor.get("specialization", "").lower() == "pulmonologist":
                        matching_doctors.append(doctor)
            
            # 5. Last resort: Use Cardiologist as absolute fallback
            if not matching_doctors:
                print("No Pulmonologist found, trying Cardiologist fallback")
                for doctor in doctors:
                    if doctor.get("specialization", "").lower() == "cardiologist":
                        matching_doctors.append(doctor)
            
            # 6. Final fallback: Pick any doctor
            if not matching_doctors and doctors:
                print("No relevant doctor found. Using first available doctor.")
                matching_doctors = [doctors[0]]
            
            # After all matching attempts, sort by experience and pick the best
            if matching_doctors:
                matching_doctors.sort(key=lambda x: x.get("experience", 0), reverse=True)
                best_match_doctor = matching_doctors[0]
                print(f"Selected doctor: {best_match_doctor.get('name')} ({best_match_doctor.get('specialization')})")
            
            # --- End of Improved Matching Logic ---

            if best_match_doctor:
                doctor = best_match_doctor # Use the best match found
                print(f"Selected doctor: {doctor.get('name')} ({doctor.get('specialization')})")
                
                # Update doctor card with information
                self.doctor_name.setText(f"Dr. {doctor.get('name', 'Specialist')}")
                self.doctor_spec.setText(doctor.get("specialization", "Specialist"))
                self.exp_value.setText(f"{doctor.get('experience', '10+')} years")
                
                # Format qualifications
                qualifications = doctor.get("qualifications", [])
                if qualifications:
                    self.qualif_value.setText(", ".join(qualifications))
                else:
                    self.qualif_value.setText("MBBS, MD")
                
                # Format location
                location = doctor.get("officeLocation", {})
                if location:
                    address = location.get("city", "")
                    if address:
                        self.loc_value.setText(address)
                    else:
                        self.loc_value.setText("Available for consultation")
                else:
                    self.loc_value.setText("Available for consultation")
                
                # Format hours
                hours = doctor.get("workingHours", {}).get("monday", {})
                if hours and "start" in hours and "end" in hours:
                    self.hours_value.setText(f"{hours['start']} - {hours['end']}")
                else:
                    self.hours_value.setText("9:00 - 17:00")
                
                # Ensure card is on top of all other elements
                self.doctor_card.setParent(self)
                self.doctor_card.raise_()
                
                # Show doctor card with animation
                self.doctor_card.show()
                self.animate_doctor_card()
            else:
                print("No suitable doctor found")
                
        except Exception as e:
            print(f"Error recommending doctor: {e}")
            import traceback
            traceback.print_exc()
    
    def animate_doctor_card(self):
        """Animate the doctor card appearing"""
        # Starting position (off-screen)
        self.doctor_card.setGeometry(-350, self.height() - 450, 350, 300)
        
        # Create animation
        for i in range(0, 351, 5):  # Smaller step for smoother animation
            QApplication.processEvents()
            self.doctor_card.setGeometry(i - 350, self.height() - 450, 350, 300)
            sleep(0.009)  # Shorter delay for smoother animation
    
    def hide_doctor_card(self):
        """Hide the doctor card with animation"""
        # Animate out
        for i in range(350, -1, -5):  # Smaller step for smoother animation
            QApplication.processEvents()
            self.doctor_card.setGeometry(i - 350, self.height() - 450, 350, 300)
            sleep(0.009)  # Shorter delay for smoother animation
        
        self.doctor_card.hide()

class InitialScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        desktop = QApplication.desktop()
        screen_width = desktop.screenGeometry().width()
        screen_height = desktop.screenGeometry().height()
        layout = QVBoxLayout()
        gif_label = QLabel()
        movie = QMovie(GraphicsDictonaryPath("Jarvis.gif"))
        max_gif_size_H = int(screen_width / 16 * 9)
        movie.setScaledSize(QSize(screen_width, max_gif_size_H))
        gif_label.setMovie(movie)
        movie.start()
        gif_label.setAlignment(Qt.AlignCenter)
        self.icon_label = QLabel()
        pixmap = QPixmap(GraphicsDictonaryPath("Mic_on.png"))
        self.icon_label.setPixmap(pixmap.scaled(60, 60))
        self.icon_label.setFixedSize(150, 150)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.toggled = True
        self.toggle_icon()
        self.icon_label.mousePressEvent = self.toggle_icon
        self.label = QLabel("")
        self.label.setStyleSheet("color: white; font-size: 16px;")
        layout.addWidget(gif_label, alignment=Qt.AlignCenter)
        layout.addWidget(self.label, alignment=Qt.AlignCenter)
        layout.addWidget(self.icon_label, alignment=Qt.AlignCenter)
        self.setLayout(layout)
        self.setFixedHeight(screen_height)
        self.setFixedWidth(screen_width)
        self.setStyleSheet("background-color: black;")
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.SpeechRecogText)
        self.timer.start(5)

    def SpeechRecogText(self):
        with open(TempDictonaryPath("Status.data"), "r", encoding="utf-8") as file:
            self.label.setText(file.read())

    def toggle_icon(self, event=None):
        pixmap = QPixmap(GraphicsDictonaryPath("Mic_on.png" if self.toggled else "Mic_off.png"))
        self.icon_label.setPixmap(pixmap.scaled(60, 60))
        SetMicrophoneStatus("False" if self.toggled else "True")
        self.toggled = not self.toggled

class MessageScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        desktop = QApplication.desktop()
        screen_width = desktop.screenGeometry().width()
        screen_height = desktop.screenGeometry().height()
        layout = QVBoxLayout()
        layout.addWidget(ChatSection())
        self.setLayout(layout)
        self.setStyleSheet("background-color: black;")
        self.setFixedHeight(screen_height)
        self.setFixedWidth(screen_width)

class CustomTopBar(QWidget):
    def __init__(self, parent, stack_widget):
        super().__init__(parent)
        self.stack_widget = stack_widget
        self.setFixedHeight(50)
        layout = QHBoxLayout(self)
        layout.setAlignment(Qt.AlignRight)
        
        # Enhanced Home button
        home_button = QPushButton("  Home")
        home_button.setIcon(QIcon(GraphicsDictonaryPath("Home.png")))
        home_button.setIconSize(QSize(20, 20))
        home_button.setStyleSheet("""
            QPushButton {
                height: 40px;
                background-color: #2b2b2b;
                color: white;
                border-radius: 20px;
                padding: 5px 15px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4a90e2;
            }
            QPushButton:pressed {
                background-color: #357abd;
            }
        """)
        
        # Enhanced Chat button
        message_button = QPushButton("  Chat")
        message_button.setIcon(QIcon(GraphicsDictonaryPath("Chats.png")))
        message_button.setIconSize(QSize(20, 20))
        message_button.setStyleSheet("""
            QPushButton {
                height: 40px;
                background-color: #2b2b2b;
                color: white;
                border-radius: 20px;
                padding: 5px 15px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4a90e2;
            }
            QPushButton:pressed {
                background-color: #357abd;
            }
        """)
        
        # Window control buttons
        minimize_button = QPushButton(icon=QIcon(GraphicsDictonaryPath("Minimize2.png")))
        minimize_button.setStyleSheet("""
            QPushButton {
                background-color: #2b2b2b;
                border: none;
                border-radius: 15px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #4a90e2;
            }
        """)
        minimize_button.clicked.connect(self.minimizeWindow)
        
        self.maximize_button = QPushButton(icon=QIcon(GraphicsDictonaryPath("Maximize.png")))
        self.restore_icon = QIcon(GraphicsDictonaryPath("Minimize.png"))
        self.maximize_button.setStyleSheet("""
            QPushButton {
                background-color: #2b2b2b;
                border: none;
                border-radius: 15px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #4a90e2;
            }
        """)
        self.maximize_button.clicked.connect(self.maximizeWindow)
        
        close_button = QPushButton(icon=QIcon(GraphicsDictonaryPath("Close.png")))
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #2b2b2b;
                border: none;
                border-radius: 15px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #e74c3c;
            }
        """)
        close_button.clicked.connect(self.close_window)
        
        # Enhanced title label
        title_label = QLabel(f" {Assistantname} ")
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 18px;
                font-weight: bold;
                background-color: #2b2b2b;
                border-radius: 15px;
                padding: 5px 15px;
            }
        """)
        
        home_button.clicked.connect(lambda: self.stack_widget.setCurrentIndex(0))
        message_button.clicked.connect(lambda: self.stack_widget.setCurrentIndex(1))
        
        layout.addWidget(title_label)
        layout.addStretch(1)
        layout.addWidget(home_button)
        layout.addWidget(message_button)
        layout.addStretch(1)
        layout.addWidget(minimize_button)
        layout.addWidget(self.maximize_button)
        layout.addWidget(close_button)
        
        self.draggable = True
        self.offset = None

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#2b2b2b"))  # Changed to match the dark theme
        super().paintEvent(event)

    def minimizeWindow(self):
        self.parent().showMinimized()

    def maximizeWindow(self):
        if self.parent().isMaximized():
            self.parent().showNormal()
            self.maximize_button.setIcon(QIcon(GraphicsDictonaryPath("Maximize.png")))
        else:
            self.parent().showMaximized()
            self.maximize_button.setIcon(self.restore_icon)

    def close_window(self):
        self.parent().close()

    def mousePressEvent(self, event):
        if self.draggable:
            self.offset = event.pos()

    def mouseMoveEvent(self, event):
        if self.draggable and self.offset:
            new_pos = event.globalPos() - self.offset
            self.parent().move(new_pos)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        desktop = QApplication.desktop()
        screen_width = desktop.screenGeometry().width()
        screen_height = desktop.screenGeometry().height()
        stacked_widget = QStackedWidget(self)
        stacked_widget.addWidget(InitialScreen())
        stacked_widget.addWidget(MessageScreen())
        self.setGeometry(0, 0, screen_width, screen_height)
        self.setStyleSheet("background-color: black;")
        self.setMenuWidget(CustomTopBar(self, stacked_widget))
        self.setCentralWidget(stacked_widget)

def GraphicalUserInterface():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    with open(rf"{TempDirPath}\TextInput.data", "w") as f:
        f.write("None")  # Initialize text input
    with open(rf"{TempDirPath}\ImageUpload.data", "w") as f:
        f.write("None")  # Initialize image upload
    sys.exit(app.exec_())

if __name__ == "__main__":
    GraphicalUserInterface()