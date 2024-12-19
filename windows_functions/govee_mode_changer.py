import pyautogui
import pygetwindow as gw
import time
import ctypes
from ctypes import wintypes
import os
import subprocess
from pathlib import Path

# Windows API constants
KEYEVENTF_KEYUP = 0x0002
VK_LWIN = 0x5B
VK_S = 0x53

# Load user32.dll
user32 = ctypes.WinDLL('user32')

def send_windows_key_s():
    """Send Windows+S using direct Windows API calls"""
    # Press Windows key
    user32.keybd_event(VK_LWIN, 0, 0, 0)
    # Press S key
    user32.keybd_event(VK_S, 0, 0, 0)
    time.sleep(0.1)  # Small delay
    # Release S key
    user32.keybd_event(VK_S, 0, KEYEVENTF_KEYUP, 0)
    # Release Windows key
    user32.keybd_event(VK_LWIN, 0, KEYEVENTF_KEYUP, 0)

def open_govee_app():
    """Open the Govee Desktop App directly"""
    try:
        # Common installation paths for Govee
        possible_paths = [
            os.path.expandvars(r'C:\Program Files\Govee\Govee Desktop\GoveeDesktop.exe')
        ]

        # Find the correct path
        govee_path = next((path for path in possible_paths if os.path.exists(path)), None)
        
        if govee_path:
            print(f"Found Govee at: {govee_path}")
            # Use subprocess to start the app
            subprocess.Popen([govee_path])
            time.sleep(1)  # Wait for app to start
            return True
        else:
            print("Govee Desktop not found in common locations")
            return False
            
    except Exception as e:
        print(f"Error launching Govee: {e}")
        return False

def focus_govee_window():  # sourcery skip: use-named-expression
    print("Searching for Govee window...")  # Immediate feedback
    
    # Try multiple times to find the window
    max_attempts = 3
    for attempt in range(max_attempts):
        window = gw.getWindowsWithTitle('Govee')
        if window:
            window[0].activate()
            print(f"Govee window found after {attempt + 1} attempts!")
            return window[0]
        time.sleep(0.3)  # Short delay between attempts
    
    print("Govee app window not found after multiple attempts!")
    return None

def perform_clicks(app_window, mode='dxgi'):
    """
    Change Govee rendering mode and close the window
    
    Args:
        app_window: Window object
        mode (str): 'dxgi' or 'gdi' (default: 'dxgi')
    """
    # Step 3: Lock mouse actions inside the app container
    left, top, width, height = app_window.left, app_window.top, app_window.width, app_window.height
    
    # Calculate relative positions for clicks inside the app window
    settings_button = (left + (1563 - 1467), top + (809 - 430))  # settings
    general_settings = (left + (1745 - 1467), top + (570 - 430))  # general settings
    dxgi_option = (left + (1860 - 1467), top + (921 - 430))      # dxgi option
    gdi_option = (left + (1959 - 1467), top + (924 - 430))       # gdi option
    x_button = (left + (2435 - 1467), top + (460 - 430))         # x button
    
    # Simulate clicks
    pyautogui.click(settings_button)
    time.sleep(0.4)
    pyautogui.click(general_settings)
    time.sleep(0.4)
    
    # Choose rendering mode based on parameter
    if mode.lower() == 'gdi':
        pyautogui.click(gdi_option)
        print("Switched to GDI mode!")
    else:  # default to dxgi
        pyautogui.click(dxgi_option)
        print("Switched to DXGI mode!")
    
    time.sleep(0.5)
    pyautogui.click(x_button)
    print("Closed Govee window")

def change_govee_mode(mode='dxgi'):  # sourcery skip: use-named-expression
    """
    Main function to change Govee rendering mode
    
    Args:
        mode (str): 'dxgi' or 'gdi' (default: 'dxgi')
    """
    open_govee_app()
    time.sleep(0.3)
    govee_window = focus_govee_window()
    if govee_window:
        perform_clicks(govee_window, mode)
        return True
    return False

def change_lights_mode(mode='dxgi'):
    change_govee_mode(mode)

if __name__ == "__main__":
    # Example usage:
    change_govee_mode('dxgi')  # or change_govee_mode('gdi')