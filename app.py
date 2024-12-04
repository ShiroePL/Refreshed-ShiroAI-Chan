from dotenv import load_dotenv
from src.app_instance import socketio, app
from src.overlay.status_overlay import StatusOverlay, AssistantState
import threading
import time

# Load environment variables
load_dotenv()

# Get the overlay instance
overlay = StatusOverlay.get_instance()
overlay_started = False

def start_overlay():
    """Start the overlay window"""
    global overlay_started
    if not overlay_started:
        print("Starting overlay...")
        overlay.setup_gui()
        overlay_started = True
        print("Overlay started")
        overlay.set_state(AssistantState.IDLE)
        overlay.root.mainloop()

@app.before_request
def before_request():
    """Start the overlay window before the first request"""
    global overlay_started
    if not overlay_started:
        # Start Tkinter in a separate thread
        thread = threading.Thread(target=start_overlay)
        thread.daemon = True
        thread.start()
        # Give the overlay time to start
        time.sleep(0.5)

if __name__ == '__main__':
    socketio.run(app, debug=True)
