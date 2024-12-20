from src.utils.logging_config import setup_logging
import logging

# Setup logging first thing
logger = setup_logging()

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
        logger.info("Starting overlay...")
        try:
            # Create and run the overlay in the main thread
            overlay.setup_gui()
            overlay_started = True
            logger.info("Overlay started")
            overlay.set_state(AssistantState.IDLE)
            # Don't call mainloop here - let the thread handle it
        except Exception as e:
            logger.error(f"Error starting overlay: {e}")

@app.before_request
def before_request():
    """Start the overlay window before the first request"""
    global overlay_started
    if not overlay_started:
        try:
            # Start Tkinter in a separate thread
            thread = threading.Thread(target=start_overlay)
            thread.daemon = True
            thread.start()
            # Give the overlay time to start
            time.sleep(0.5)
        except Exception as e:
            logger.error(f"Error in before_request: {e}")


if __name__ == '__main__':
    try:
        socketio.run(app, debug=True)
    except Exception as e:
        handle_error(logger, e, "Application startup")
