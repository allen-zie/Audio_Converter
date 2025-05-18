import fitz  # PyMuPDF
from gtts import gTTS
from PyQt6.QtWidgets import QApplication, QFileDialog, QVBoxLayout, QPushButton, QWidget, QLabel, QComboBox, QProgressBar, QMessageBox
from PyQt6.QtCore import QThread, pyqtSignal, QTimer
import os
import sys
import requests

class AudioConversionThread(QThread):
    conversion_done = pyqtSignal(str)
    conversion_error = pyqtSignal(str)
    progress_update = pyqtSignal(int)

    def __init__(self, text, voice_option, output_file):
        super().__init__()
        self.text = text
        self.voice_option = voice_option
        self.output_file = output_file

    def run(self):
        try:
            total_parts = 100
            for i in range(1, total_parts + 1):
                self.progress_update.emit(i)
                QThread.msleep(50)  # Simulate processing time

            if self.voice_option == 'Google TTS (gTTS)':
                tts = gTTS(self.text)
                tts.save(self.output_file)
                print(f"Conversion successful: {self.output_file}")  # Debugging log
                self.conversion_done.emit(self.output_file)
            elif self.voice_option == 'Eleven Labs AI':
                api_key = 'your-elevenlabs-api-key'  # Replace with actual API key
                response = requests.post(
                    'https://api.elevenlabs.io/v1/text-to-speech',
                    json={"text": self.text, "voice": "Bella"},
                    headers={"Authorization": f"Bearer {api_key}"}
                )
                if response.status_code == 200:
                    with open(self.output_file, 'wb') as f:
                        f.write(response.content)
                    print(f"Conversion successful: {self.output_file}")  # Debugging log
                    self.conversion_done.emit(self.output_file)
                else:
                    print("Error generating AI audio.")  # Debugging log
                    self.conversion_error.emit("Error generating AI audio.")
        except Exception as e:
            print(f"Conversion error: {str(e)}")  # Debugging log
            self.conversion_error.emit(str(e))

class PDFToAudioConverter(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('PDF to Audio Converter')
        self.setGeometry(300, 300, 400, 250)
        
        layout = QVBoxLayout()
        
        self.label = QLabel('Select PDF file:', self)
        layout.addWidget(self.label)
        
        self.file_button = QPushButton('Choose PDF', self)
        self.file_button.clicked.connect(self.select_pdf)
        layout.addWidget(self.file_button)
        
        self.page_label = QLabel('', self)
        layout.addWidget(self.page_label)
        
        self.voice_label = QLabel('Choose Voice Option:', self)
        layout.addWidget(self.voice_label)
        
        self.voice_combo = QComboBox(self)
        self.voice_combo.addItem('Google TTS (gTTS)')
        self.voice_combo.addItem('Eleven Labs AI')
        layout.addWidget(self.voice_combo)
        
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        self.convert_button = QPushButton('Convert to Audio', self)
        self.convert_button.clicked.connect(self.convert_pdf_to_audio)
        layout.addWidget(self.convert_button)
        
        self.setLayout(layout)
        
    def select_pdf(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Open PDF File', '', 'PDF Files (*.pdf)')
        if file_path:
            self.label.setText(f'Selected File: {file_path}')
            self.pdf_path = file_path
            pdf_document = fitz.open(file_path)
            num_pages = pdf_document.page_count
            self.page_label.setText(f'PDF Loaded Successfully - {num_pages} Pages')
            pdf_document.close()
        
    def extract_text_from_pdf(self, pdf_path):
        pdf_document = fitz.open(pdf_path)
        text = ""
        for page_num in range(pdf_document.page_count):
            page = pdf_document.load_page(page_num)
            text += page.get_text()
        pdf_document.close()
        return text

    def convert_pdf_to_audio(self):
        if hasattr(self, 'pdf_path') and self.pdf_path:
            text = self.extract_text_from_pdf(self.pdf_path)
            if not text.strip():
                QMessageBox.warning(self, "Conversion Error", "No text found in the PDF.")
                return
            
            voice_option = self.voice_combo.currentText()
            output_file, _ = QFileDialog.getSaveFileName(self, 'Save Audio File', '', 'MP3 Files (*.mp3)')
            if output_file:
                if not output_file.endswith('.mp3'):
                    output_file += '.mp3'
                
                self.thread = AudioConversionThread(text, voice_option, output_file)
                self.thread.conversion_done.connect(self.on_conversion_done)
                self.thread.conversion_error.connect(self.on_conversion_error)
                self.thread.progress_update.connect(self.update_progress_bar)
                self.progress_bar.setValue(0)
                self.thread.start()

    def update_progress_bar(self, value):
        self.progress_bar.setValue(value)

    def on_conversion_done(self, output_file):
        print(f"Conversion successful: {output_file}")  # Debugging log
        QMessageBox.information(self, "Success", f"Audio file saved as {output_file}")
        self.progress_bar.setValue(100)

    def on_conversion_error(self, error):
        print(f"Conversion error: {error}")  # Debugging log
        QMessageBox.critical(self, "Error", f"Conversion failed: {error}")
        self.progress_bar.setValue(0)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    converter = PDFToAudioConverter()
    converter.show()
    sys.exit(app.exec())
