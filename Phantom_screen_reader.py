import pytesseract
from PIL import ImageGrab
import google.generativeai as genai
from livekit.agents import function_tool
import asyncio
from keyboard_mouse_CTRL import move_cursor_tool, mouse_click_tool
import logging
import tkinter as tk
from tkinter import ttk
from PIL import ImageTk

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Tesseract path (update this path according to your installation)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class ScreenReaderInterface:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Phantom Screen Reader")
        self.root.geometry("800x600")
        
        # Create interface elements
        self.preview_frame = ttk.Frame(self.root)
        self.preview_frame.pack(pady=10, fill=tk.BOTH, expand=True)
        
        self.preview_label = ttk.Label(self.preview_frame)
        self.preview_label.pack()
        
        self.text_area = tk.Text(self.root, height=10, wrap=tk.WORD)
        self.text_area.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        self.status_label = ttk.Label(self.root, text="Status: Ready")
        self.status_label.pack(pady=5)
        
    def update_preview(self, image):
        photo = ImageTk.PhotoImage(image)
        self.preview_label.config(image=photo)
        self.preview_label.image = photo
        
    def update_text(self, text):
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(tk.END, text)
        
    def update_status(self, text):
        self.status_label.config(text=f"Status: {text}")
        self.root.update()

async def capture_screen_region():
    """Capture a selected region of the screen"""
    # TODO: Implement screen region selection
    screen = ImageGrab.grab()
    return screen

async def extract_text_from_image(image):
    """Extract text from image using OCR"""
    try:
        text = pytesseract.image_to_string(image)
        return text.strip()
    except Exception as e:
        logger.error(f"OCR Error: {str(e)}")
        return ""

async def summarize_text(text):
    """Summarize text using Gemini"""
    try:
        prompt = f"""Please summarize the following text in a clear and concise way:
        {text}
        Key points:
        1. Main ideas
        2. Important details
        3. Conclusions
        """
        
        response = genai.ChatCompletion.create(
            model=genai.GenerativeModel('gemini-pro'),
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message["content"]
    except Exception as e:
        logger.error(f"Summarization Error: {str(e)}")
        return "Error generating summary"

async def explain_code(code):
    """Explain code using Gemini"""
    try:
        prompt = f"""Please explain this code in simple terms:
        {code}
        Include:
        1. Purpose of the code
        2. How it works
        3. Key functions and their roles
        4. Any important patterns or techniques used
        """
        
        response = genai.ChatCompletion.create(
            model=genai.GenerativeModel('gemini-pro'),
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message["content"]
    except Exception as e:
        logger.error(f"Code Explanation Error: {str(e)}")
        return "Error explaining code"

@function_tool
async def read_screen(mode: str = "text") -> str:
    """Read and analyze screen content"""
    interface = ScreenReaderInterface()
    
    try:
        interface.update_status("Capturing screen...")
        screen = await capture_screen_region()
        interface.update_preview(screen.resize((640, 360)))
        
        interface.update_status("Extracting text...")
        text = await extract_text_from_image(screen)
        
        if not text:
            interface.root.destroy()
            return "❌ No text found on screen"
        
        if mode.lower() == "code":
            interface.update_status("Analyzing code...")
            result = await explain_code(text)
        else:
            interface.update_status("Generating summary...")
            result = await summarize_text(text)
        
        interface.update_text(result)
        await asyncio.sleep(10)  # Keep interface open for 10 seconds
        interface.root.destroy()
        
        return f"✅ Analysis complete:\n{result}"
        
    except Exception as e:
        interface.root.destroy()
        return f"❌ Error: {str(e)}"

@function_tool
async def explain_screen_code() -> str:
    """Specifically analyze code on screen"""
    return await read_screen(mode="code")
