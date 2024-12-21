import tkinter as tk
from flask import Flask, request
from flask_socketio import SocketIO, emit
import logging
from enum import Enum
import sys
import ctypes
import queue
from threading import Thread, Lock
import threading

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OverlayState(str, Enum):
    IDLE = "IDLE"
    LISTENING = "LISTENING"
    LISTENING_COMMAND = "LISTENING_COMMAND"
    PROCESSING = "PROCESSING"
    SPEAKING = "SPEAKING"
    ERROR = "ERROR"

    @classmethod
    def _missing_(cls, value):
        """Handle invalid state values"""
        logger.warning(f"Invalid state requested: {value}")
        return cls.IDLE  # Default to IDLE for invalid states

class OverlayWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the main window
        self.setup_overlay_window()
        self.command_queue = queue.Queue()
        self.running = True
        
    def setup_overlay_window(self):
        self.overlay = tk.Toplevel(self.root)
        self.overlay.overrideredirect(True)  # Remove window decorations
        self.overlay.attributes('-topmost', True)  # Keep on top
        self.overlay.attributes('-alpha', 0.8)  # Set transparency
        self.overlay.wm_attributes('-transparentcolor', 'black')
        
        # Create a circular indicator with larger size
        self.canvas = tk.Canvas(self.overlay, width=60, height=60, 
                              bg='black', highlightthickness=0)
        self.canvas.pack()
        
        # Initialize the circle with larger size and border
        padding = 5
        self.circle = self.canvas.create_oval(
            padding, padding, 
            60-padding, 60-padding, 
            fill="#808080",  # Default gray
            outline="white",  # Add white border
            width=2  # Border width
        )
        
        # For pulsing animation
        self.pulsing = False
        self.pulse_alpha = 0
        self.pulse_increasing = True
        
        # Add drag functionality
        self.canvas.bind('<Button-1>', self.start_drag)
        self.canvas.bind('<B1-Motion>', self.drag)
        
        # Position window
        self.position_window()
        
    def position_window(self):
        try:
            # Get screen info using Windows API
            user32 = ctypes.windll.user32
            monitors = []
            
            def callback(hmonitor, hdc, lprect, lparam):
                rect = ctypes.cast(lprect, ctypes.POINTER(ctypes.c_long))
                monitors.append({
                    'left': rect[0],
                    'top': rect[1],
                    'right': rect[2],
                    'bottom': rect[3]
                })
                return 1
            
            callback_type = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_ulong, 
                                             ctypes.c_ulong,
                                             ctypes.POINTER(ctypes.c_long), 
                                             ctypes.c_double)
            callback_function = callback_type(callback)
            user32.EnumDisplayMonitors(None, None, callback_function, 0)
            
            # If there's more than one monitor, use the second one
            if len(monitors) > 1:
                monitor = monitors[1]
                x = monitor['left'] + 10
                y = monitor['bottom'] - 110
            else:
                screen_width = self.root.winfo_screenwidth()
                screen_height = self.root.winfo_screenheight()
                x = screen_width - 70
                y = screen_height - 120
            
            self.overlay.geometry(f'+{x}+{y}')
            logger.info(f"Window positioned at {x}, {y}")
        except Exception as e:
            logger.error(f"Error positioning window: {e}")
            self.overlay.eval('tk::PlaceWindow . center')

    def start_drag(self, event):
        self.x = event.x
        self.y = event.y

    def drag(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.overlay.winfo_x() + deltax
        y = self.overlay.winfo_y() + deltay
        self.overlay.geometry(f"+{x}+{y}")

    def update_state(self, state: OverlayState):
        # Queue the state update instead of doing it directly
        self.command_queue.put(('update_state', state))

    def process_commands(self):
        """Process queued commands"""
        try:
            while self.running:
                try:
                    # Check queue with timeout to allow window updates
                    command, *args = self.command_queue.get_nowait()
                    if command == 'update_state':
                        self._do_update_state(args[0])
                except queue.Empty:
                    pass
                self.overlay.update()  # Process Tkinter events
                self.root.after(50, self.process_commands)  # Schedule next check
                return
        except Exception as e:
            logger.error(f"Error processing commands: {e}")

    def _do_update_state(self, state: OverlayState):
        """Actually perform the state update"""
        try:
            # Map states to colors
            color_map = {
                OverlayState.IDLE: "#808080",        # Gray
                OverlayState.LISTENING: "#0000FF",   # Blue
                OverlayState.LISTENING_COMMAND: "#00FF00",  # Green
                OverlayState.PROCESSING: "#FFA500",  # Orange
                OverlayState.SPEAKING: "#FF00FF",    # Purple
                OverlayState.ERROR: "#FF0000",       # Red
            }
            
            if state == OverlayState.PROCESSING:
                self.start_pulse()
            else:
                self.stop_pulse()
                color = color_map.get(state, "#808080")
                self.canvas.itemconfig(self.circle, fill=color)
                
        except Exception as e:
            logger.error(f"Error updating state: {e}")

    def start_pulse(self):
        self.pulsing = True
        self.pulse_alpha = 0
        self.pulse_increasing = True
        self.update_pulse()

    def stop_pulse(self):
        self.pulsing = False

    def update_pulse(self):
        if not self.pulsing:
            return
            
        try:
            if self.pulse_increasing:
                self.pulse_alpha += 0.05
                if self.pulse_alpha >= 1:
                    self.pulse_increasing = False
            else:
                self.pulse_alpha -= 0.05
                if self.pulse_alpha <= 0:
                    self.pulse_increasing = True
                    
            # Calculate pulsing orange color
            alpha = max(0, min(1, self.pulse_alpha))
            r = int(255 * (0.7 + 0.3 * alpha))
            g = int(165 * (0.7 + 0.3 * alpha))
            color = f'#{r:02x}{g:02x}00'
            
            self.canvas.itemconfig(self.circle, fill=color)
            
            if self.pulsing:
                self.overlay.after(50, self.update_pulse)
                
        except Exception as e:
            logger.error(f"Error updating pulse: {e}")
            self.pulsing = False

    def start(self):
        """Start processing commands and run the main loop"""
        self.process_commands()
        self.root.mainloop()

    def stop(self):
        """Stop the overlay window"""
        self.running = False
        if self.root:
            self.root.quit()

# Initialize Flask and SocketIO
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Create overlay window
overlay_window = None

@app.route('/state_change', methods=['POST'])
def http_state_change():
    """Handle state change via HTTP POST"""
    try:
        data = request.json
        new_state = data.get('state')
        if new_state and overlay_window:
            logger.info(f"Updating overlay state to: {new_state}")
            # Convert string to enum safely
            state_enum = OverlayState(new_state)
            overlay_window.update_state(state_enum)
            return {'status': 'success'}
        return {'status': 'error', 'message': 'Invalid state or no overlay window'}, 400
    except ValueError as e:
        logger.error(f"Invalid state value: {e}")
        return {'status': 'error', 'message': f'Invalid state: {str(e)}'}, 400
    except Exception as e:
        logger.error(f"Error handling state change: {e}")
        return {'status': 'error', 'message': str(e)}, 500

@socketio.on('connect')
def handle_connect():
    logger.info("Client connected")
    emit('status', {'connected': True})

@socketio.on('disconnect')
def handle_disconnect():
    logger.info("Client disconnected")

@socketio.on('state_change')
def handle_state_change(data):
    """Handle state change from websocket"""
    try:
        new_state = data.get('state')
        if new_state and overlay_window:
            logger.info(f"Updating overlay state to: {new_state}")
            overlay_window.update_state(OverlayState(new_state))
    except Exception as e:
        logger.error(f"Error handling state change: {e}")

def run_flask():
    """Run Flask-SocketIO server in a separate thread"""
    port = 8020
    logger.info(f"Starting overlay service on port {port}")
    socketio.run(app, host='0.0.0.0', port=port, debug=False)

if __name__ == "__main__":
    try:
        # Initialize overlay in main thread
        overlay_window = OverlayWindow()
        logger.info("Overlay window initialized")

        # Start Flask in a separate thread
        flask_thread = Thread(target=run_flask, daemon=True)
        flask_thread.start()

        # Run Tkinter main loop in main thread
        overlay_window.start()

    except Exception as e:
        logger.error(f"Failed to start overlay: {e}")
        sys.exit(1)
    finally:
        if overlay_window:
            overlay_window.stop() 