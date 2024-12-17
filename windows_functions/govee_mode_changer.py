import pyautogui
import pygetwindow as gw
import time

def open_govee_app():
    # Step 1: Open the Govee Desktop App from system tray
    pyautogui.hotkey('win', 's')  # Open Windows search
    time.sleep(0.5)
    pyautogui.write('Govee Desktop')  # Replace with exact app name
    time.sleep(0.5)
    pyautogui.press('enter')  # Launch the app
    time.sleep(1)  # Reduced from 3 to 2 seconds

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

if __name__ == "__main__":
    # Example usage:
    change_govee_mode('dxgi')  # or change_govee_mode('gdi')