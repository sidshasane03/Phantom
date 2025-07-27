import speech_recognition as sr
import webbrowser
import time
import pyautogui
import asyncio
import google.generativeai as genai
from dotenv import load_dotenv
from livekit.agents import function_tool
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from Phantom_google_search import google_search
from Phantom_window_CTRL import open, close, folder_file
from keyboard_mouse_CTRL import move_cursor_tool, mouse_click_tool, scroll_cursor_tool, type_text_tool, press_key_tool, swipe_gesture_tool, press_hotkey_tool, control_volume_tool



def get_voice_input():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        audio = recognizer.listen(source)
    try:
        command = recognizer.recognize_google(audio)
        return command.lower()
    except:
        return ""
    
genai.configure(api_key="YOUR_GEMINI_API_KEY")
async def get_installation_steps(software_name):
    prompt = f"""
    Generate detailed steps to download and install {software_name} on Windows.
    Include:
    1. Official download URL
    2. System requirements
    3. Step-by-step installation process
    4. Common installation options and recommended settings
    5. Verification steps after installation
    """
    
    response = genai.ChatCompletion.create(
        model = genai.GenerativeModel('gemini-pro'),
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message["content"]

async def extract_terms_conditions(url):
    try:
        driver = webdriver.Chrome()
        driver.get(url)
        
        # Common terms & conditions selectors
        selectors = [
            "//a[contains(text(), 'Terms')]",
            "//a[contains(text(), 'EULA')]",
            "//a[contains(text(), 'License Agreement')]"
        ]
        
        for selector in selectors:
            try:
                element = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, selector))
                )
                element.click()
                time.sleep(2)
                terms_text = driver.find_element(By.TAG_NAME, "body").text
                driver.quit()
                return terms_text
            except:
                continue
                
        driver.quit()
        return "Terms and conditions not found"
    except Exception as e:
        return f"Error extracting terms: {str(e)}"

async def summarize_terms(terms_text):
    prompt = f"""Summarize the following software terms and conditions in 3-4 key points:
    {terms_text}
    Focus on: Usage rights, Restrictions, Privacy implications, and Liability"""
    
    response = genai.ChatCompletion.create(
        model = genai.GenerativeModel('gemini-pro'),
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message["content"]

@function_tool
async def download_software(software_name: str) -> str:
    """Downloads and installs software using automated UI interactions"""
    # Get installation steps from LLM
    instructions = await get_installation_steps(software_name)
    print(f"📝 Installation instructions received for {software_name}")

    # Extract download URL
    if "https://" in instructions:
        url_start = instructions.find("https://")
        url_end = instructions.find(" ", url_start)
        download_url = instructions[url_start:url_end]
        
        # Get and summarize terms & conditions
        terms_text = await extract_terms_conditions(download_url)
        terms_summary = await summarize_terms(terms_text)
        print("\n📜 Terms & Conditions Summary:")
        print(terms_summary)
        
        # Ask for user confirmation
        print("\n⚠️ Do you accept the terms and conditions? (say 'yes' to continue)")
        user_response = get_voice_input()
        
        if "yes" in user_response.lower():
            # Execute installation steps using keyboard/mouse control
            webbrowser.open(download_url)
            await asyncio.sleep(3)
            
            # Automated download sequence
            await move_cursor_tool("down", 200)
            await mouse_click_tool("left")
            await asyncio.sleep(2)
            
            # Handle download dialog
            await press_hotkey_tool(["ctrl", "s"])
            await asyncio.sleep(1)
            await press_key_tool("enter")
            
            print(f"✅ {software_name} download started")
            
            # Monitor download progress
            await asyncio.sleep(10)  # Wait for download
            
            # Run installer
            downloaded_file = f"{software_name}_setup.exe"  # Assumed name
            await folder_file(f"open {downloaded_file}")
            
            # Handle installation dialog
            await asyncio.sleep(2)
            await press_key_tool("enter")
            
            return f"✅ {software_name} installation process completed"
        else:
            return "❌ Installation cancelled - Terms not accepted"
    else:
        return "❌ No valid download URL found in instructions"
