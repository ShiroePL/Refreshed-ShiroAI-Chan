from dotenv import load_dotenv
from src.app_instance import socketio, app
from src.overlay.status_overlay import StatusOverlay
import threading

# Load environment variables
load_dotenv()

# Get the overlay instance
overlay = StatusOverlay.get_instance()
overlay_started = False

@app.before_request
def before_request():
    """Start the overlay window before the first request"""
    global overlay_started
    if not overlay_started:
        def run_overlay():
            overlay.setup_gui()
            overlay.root.mainloop()
        
        # Start Tkinter in a separate thread
        thread = threading.Thread(target=run_overlay)
        thread.daemon = True
        thread.start()
        overlay_started = True

if __name__ == '__main__':
    socketio.run(app, debug=True)
