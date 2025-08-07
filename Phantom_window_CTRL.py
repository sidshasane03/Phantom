import os
import subprocess
import logging
import sys
import pyautogui
import platform
import pyttsx3
import time
import asyncio
from PIL import ImageGrab, Image, ImageTk, ImageDraw
import pytesseract
import keyboard
from fuzzywuzzy import process


try:
    from livekit.agents import function_tool
except ImportError:
    def function_tool(func): 
        return func

try:
    import win32gui
    import win32con
except ImportError:
    win32gui = None
    win32con = None

try:
    import pygetwindow as gw
except ImportError:
    gw = None

# Setup encoding and logger
sys.stdout.reconfigure(encoding='utf-8')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Updated APP_MAPPINGS with more accurate paths and common applications



    
    # Check in APP_MAPPINGS first

    
    # Check common Program Files locations



# -------------------------
# Global focus utility
# -------------------------
async def focus_window(title_keyword: str) -> bool:
    if not gw:
        logger.warning("⚠ pygetwindow")
        return False

    await asyncio.sleep(1.5)  # Give time for window to appear
    title_keyword = title_keyword.lower().strip()

    for window in gw.getAllWindows():
        if title_keyword in window.title.lower():
            if window.isMinimized:
                window.restore()
            window.activate()
            return True
    return False

# Index files/folders
async def index_items(base_dirs):
    item_index = []
    for base_dir in base_dirs:
        for root, dirs, files in os.walk(base_dir):
            for d in dirs:
                item_index.append({"name": d, "path": os.path.join(root, d), "type": "folder"})
            for f in files:
                item_index.append({"name": f, "path": os.path.join(root, f), "type": "file"})
    logger.info(f"✅ Indexed {len(item_index)} items.")
    return item_index

async def search_item(query, index, item_type):
    filtered = [item for item in index if item["type"] == item_type]
    choices = [item["name"] for item in filtered]
    if not choices:
        return None
    best_match, score = process.extractOne(query, choices)
    logger.info(f"🔍 Matched '{query}' to '{best_match}' with score {score}")
    if score > 70:
        for item in filtered:
            if item["name"] == best_match:
                return item
    return None

# File/folder actions
async def open_folder(path):
    try:
        os.startfile(path) if os.name == 'nt' else subprocess.call(['xdg-open', path])
        await focus_window(os.path.basename(path))
    except Exception as e:
        logger.error(f"❌ फ़ाइल open करने में error आया। {e}")

async def play_file(path):
    try:
        os.startfile(path) if os.name == 'nt' else subprocess.call(['xdg-open', path])
        await focus_window(os.path.basename(path))
    except Exception as e:
        logger.error(f"❌ फ़ाइल open करने में error आया।: {e}")

async def create_folder(path):
    try:
        os.makedirs(path, exist_ok=True)
        return f"✅ Folder create हो गया।: {path}"
    except Exception as e:
        return f"❌ फ़ाइल create करने में error आया।: {e}"

async def rename_item(old_path, new_path):
    try:
        os.rename(old_path, new_path)
        return f"✅ नाम बदलकर {new_path} कर दिया गया।"
    except Exception as e:
        return f"❌ नाम बदलना fail हो गया: {e}"

async def delete_item(path):
    try:
        if os.path.isdir(path):
            os.rmdir(path)
        else:
            os.remove(path)
        return f"🗑️ Deleted: {path}"
    except Exception as e:
        return f"❌ Delete नहीं हुआ।: {e}"

# App control
@function_tool
async def open(app_title: str) -> str:
    """Enhanced open function with better error handling and app detection"""
    try:
        if platform.system() == "Windows":
            pyautogui.press('win')
            time.sleep(0.5)
            pyautogui.write(app_title)
            time.sleep(1)
            pyautogui.press('enter')
        elif platform.system() == "Darwin":
            pyautogui.hotkey('command', 'space')
            time.sleep(0.5)
            pyautogui.write(app_title)
            time.sleep(1)
            pyautogui.press('enter')
        elif platform.system() == "Linux":
            pyautogui.press('super')
            time.sleep(0.5)
            pyautogui.write(app_title)
            time.sleep(1)
            pyautogui.press('enter')
        else:
            print("Sorry, I can only open applications on Windows, macOS, or Linux (Ubuntu/Debian) for now.")
            return False
            
    except Exception as e:
        return f"❌ Error launching {app_title}: {str(e)}"

@function_tool
async def close(app_title: str) -> str:
    # """Enhanced close function with better window detection"""
    # if not win32gui:
    #     return "❌ win32gui module not available"

    # closed = False
    # def enum_handler(hwnd, result):
    #     nonlocal closed
    #     if win32gui.IsWindowVisible(hwnd):
    #         window_text = win32gui.GetWindowText(hwnd).lower()
    #         if window_title.lower() in window_text:
                try:
                    if platform.system() == "Windows" or platform.system() == "Linux":
                        pyautogui.hotkey('alt', 'f4') # Standard close shortcut for Windows and many Linux environments
                    elif platform.system() == "Darwin": # macOS
                         pyautogui.hotkey('command', 'q') # Standard quit shortcut for macOS apps
                    else:
                        print("Sorry, I don't know how to close applications on this operating system.")
                        return False
                    
                    print("Close command sent. Hope it worked!")
                    return True
                except Exception as e:
                    print(f"Error closing window: {e}")

    # try:
    #     win32gui.EnumWindows(enum_handler, None)
    #     if closed:
    #         return f"✅ Successfully closed {window_title}"
    #     else:
    #         # Try alternative method using taskkill
    #         subprocess.run(['taskkill', '/F', '/IM', f'{window_title}.exe'], 
    #                      stdout=subprocess.DEVNULL, 
    #                      stderr=subprocess.DEVNULL)
    #         return f"✅ Attempted to force close {window_title}"
    # except Exception as e:
    #     return f"❌ Error closing {window_title}: {str(e)}"

# phantom command logic
@function_tool
async def folder_file(command: str) -> str:
    folders_to_index = ["D:/"]
    index = await index_items(folders_to_index)
    command_lower = command.lower()

    if "create folder" in command_lower:
        folder_name = command.replace("create folder", "").strip()
        path = os.path.join("D:/", folder_name)
        return await create_folder(path)

    if "rename" in command_lower:
        parts = command_lower.replace("rename", "").strip().split("to")
        if len(parts) == 2:
            old_name = parts[0].strip()
            new_name = parts[1].strip()
            item = await search_item(old_name, index, "folder")
            if item:
                new_path = os.path.join(os.path.dirname(item["path"]), new_name)
                return await rename_item(item["path"], new_path)
        return "❌ rename command valid नहीं है।"

    if "delete" in command_lower:
        item = await search_item(command, index, "folder") or await search_item(command, index, "file")
        if item:
            return await delete_item(item["path"])
        return "❌ Delete करने के लिए item नहीं मिला।"

    if "folder" in command_lower or "open folder" in command_lower:
        item = await search_item(command, index, "folder")
        if item:
            await open_folder(item["path"])
            return f"✅ Folder opened: {item['name']}"
        return "❌ Folder नहीं मिला।."

    item = await search_item(command, index, "file")
    if item:
        await play_file(item["path"])
        return f"✅ File opened: {item['name']}"

    return "⚠ कुछ भी match नहीं हुआ।"
