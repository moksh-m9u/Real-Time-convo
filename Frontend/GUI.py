import os
import sys
os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = r"C:\Users\MOKSH\OneDrive - MDH International School, Dwarka\Desktop\Projects\FRIDAY\.venv\Lib\site-packages\PyQt5\Qt5\plugins"
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QStackedWidget, QWidget, QLineEdit, QGridLayout, QVBoxLayout, QHBoxLayout, QPushButton, QFrame, QLabel, QSizePolicy, QFileDialog
from PyQt5.QtGui import QIcon, QPainter, QMovie, QColor, QTextCharFormat, QFont, QPixmap, QTextBlockFormat
from PyQt5.QtCore import Qt, QSize, QTimer
from dotenv import dotenv_values

env_vars = dotenv_values(".env")
Assistantname = "DocBot"
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

class ChatSection(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(-10, 40, 40, 100)
        self.chat_text_edit = QTextEdit()
        self.chat_text_edit.setReadOnly(True)
        self.chat_text_edit.setFrameStyle(QFrame.NoFrame)
        layout.addWidget(self.chat_text_edit)

        # Textbox for input
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Type your symptoms here...")
        self.text_input.returnPressed.connect(self.submit_text)
        layout.addWidget(self.text_input)

        # Image upload button
        self.upload_button = QPushButton("Upload Image")
        self.upload_button.clicked.connect(self.upload_image)
        layout.addWidget(self.upload_button)

        self.setStyleSheet("background-color: black;")
        text_color = QColor(Qt.blue)
        text_color_text = QTextCharFormat()
        text_color_text.setForeground(text_color)
        self.chat_text_edit.setCurrentCharFormat(text_color_text)
        self.gif_label = QLabel()
        movie = QMovie(GraphicsDictonaryPath("Jarvis.gif"))
        movie.setScaledSize(QSize(480, 270))
        self.gif_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        self.gif_label.setMovie(movie)
        movie.start()
        layout.addWidget(self.gif_label)
        self.label = QLabel("")
        self.label.setStyleSheet("color: white; font-size: 16px; margin-right: 195px;")
        self.label.setAlignment(Qt.AlignRight)
        layout.addWidget(self.label)
        font = QFont()
        font.setPointSize(13)
        self.chat_text_edit.setFont(font)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.loadMessages)
        self.timer.timeout.connect(self.SpeechRecogText)
        self.timer.start(5)

    def loadMessages(self):
        global old_chat_message
        with open(TempDictonaryPath("Responses.data"), "r", encoding="utf-8") as file:
            messages = file.read()
            if messages and messages != old_chat_message:
                self.addMessage(messages, "White")
                old_chat_message = messages

    def SpeechRecogText(self):
        with open(TempDictonaryPath("Status.data"), "r", encoding="utf-8") as file:
            self.label.setText(file.read())

    def submit_text(self):
        text = self.text_input.text()
        if text:
            SetTextInput(text)
            self.text_input.clear()

    def upload_image(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Image", "", "Image Files (*.png *.jpg *.jpeg)")
        if file_name:
            with open(rf"{TempDirPath}\ImageUpload.data", "w") as f:
                f.write(file_name)

    def addMessage(self, message, color):
        cursor = self.chat_text_edit.textCursor()
        format = QTextCharFormat()
        formatm = QTextBlockFormat()
        formatm.setTopMargin(10)
        formatm.setLeftMargin(10)
        format.setForeground(QColor(color))
        cursor.setCharFormat(format)
        cursor.setBlockFormat(formatm)
        cursor.insertText(message + "\n")
        self.chat_text_edit.setTextCursor(cursor)

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
        home_button = QPushButton("  Home", icon=QIcon(GraphicsDictonaryPath("Home.png")))
        home_button.setStyleSheet("height:40px; background-color:white; color: black")
        message_button = QPushButton("  Chat", icon=QIcon(GraphicsDictonaryPath("Chats.png")))
        message_button.setStyleSheet("height:40px; background-color:white; color: black")
        minimize_button = QPushButton(icon=QIcon(GraphicsDictonaryPath("Minimize2.png")))
        minimize_button.setStyleSheet("background-color:white")
        minimize_button.clicked.connect(self.minimizeWindow)
        self.maximize_button = QPushButton(icon=QIcon(GraphicsDictonaryPath("Maximize.png")))
        self.restore_icon = QIcon(GraphicsDictonaryPath("Minimize.png"))
        self.maximize_button.setStyleSheet("background-color:white")
        self.maximize_button.clicked.connect(self.maximizeWindow)
        close_button = QPushButton(icon=QIcon(GraphicsDictonaryPath("Close.png")))
        close_button.setStyleSheet("background-color:white")
        close_button.clicked.connect(self.close_window)
        title_label = QLabel(f" {Assistantname} ")
        title_label.setStyleSheet("color: black; font-size: 18px; background-color: white")
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
        painter.fillRect(self.rect(), Qt.white)
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