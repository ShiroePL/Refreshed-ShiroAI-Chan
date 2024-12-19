import tkinter as tk
from enum import Enum
import queue
from threading import Thread, Lock
import logging
from src.utils.logging_config import handle_error

logger = logging.getLogger(__name__)

# Disable debug logs from other modules
logging.getLogger('werkzeug').setLevel(logging.WARNING)
logging.getLogger('engineio').setLevel(logging.WARNING)
logging.getLogger('socketio').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('groq').setLevel(logging.WARNING)

# Only show important state changes
def log_state_change(from_state, to_state):
    # Skip logging push-to-talk related state changes
    if hasattr(to_state, 'name'):  # Check if it's an enum
        if to_state.name == 'LISTENING' and from_state.name == 'IDLE':
            return  # Skip logging push-to-talk transitions
        if to_state.name == 'IDLE' and from_state.name == 'LISTENING':
            return  # Skip logging push-to-talk end transitions
    logger.info(f"Assistant State: {to_state.name}")

class AssistantState(Enum):
    IDLE = "IDLE"
    LISTENING = "LISTENING"
    LISTENING_COMMAND = "LISTENING_COMMAND"  # New state for command mode
    PROCESSING = "PROCESSING"
    SPEAKING = "SPEAKING"

class StatusOverlay:
    _instance = None
    _lock = Lock()
    
    @classmethod
    def get_instance(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance
    
    def load_icon(self, color):
        """Create a colored circle as an icon."""
        icon_size = 60
        padding = 5
        
        # Create a temporary canvas to draw the icon
        temp_canvas = tk.Canvas(width=icon_size, height=icon_size, 
                              bg='black', highlightthickness=0)
        
        # Map state names to colors
        color_map = {
            "gray": "#808080",    # Idle
            "blue": "#0000FF",    # Listening for trigger
            "green": "#00FF00",   # Listening for command
            "yellow": "#FFA500",  # Processing
            "purple": "#FF00FF"   # Speaking
        }
        
        # Draw the circle
        temp_canvas.create_oval(
            padding, padding,
            icon_size-padding, icon_size-padding,
            fill=color_map.get(color, "#808080"),  # Default to gray if color not found
            outline="white",
            width=2
        )
        
        return temp_canvas
    
    def __init__(self):
        if StatusOverlay._instance is not None:
            raise Exception("This class is a singleton!")
            
        self.command_queue = queue.Queue()
        self.running = True
        self.root = None
        self.setup_pending = True
        self.current_state = AssistantState.IDLE
        StatusOverlay._instance = self
        print("StatusOverlay initialized")
        
        # Create the root window temporarily for icon creation
        temp_root = tk.Tk()
        
        # Load all icon states
        self.gray_icon = self.load_icon("gray")
        self.blue_icon = self.load_icon("blue")
        self.green_icon = self.load_icon("green")
        self.yellow_icon = self.load_icon("yellow")
        self.purple_icon = self.load_icon("purple")
        
        # Destroy temporary root
        temp_root.destroy()

    def setup_gui(self):
        if not self.setup_pending:
            return
            
        print("Setting up GUI...")
        self.root = tk.Tk()
        self.root.title("Assistant Status")
        
        # Make window floating and always on top
        self.root.attributes('-topmost', True)
        self.root.overrideredirect(True)  # Remove window decorations
        self.root.wm_attributes('-transparentcolor', 'black')  # Make black background transparent
        
        # Create a circular indicator with larger size
        self.canvas = tk.Canvas(self.root, width=60, height=60, bg='black', 
                              highlightthickness=0)
        self.canvas.pack()
        
        # Initialize the circle with larger size and border
        padding = 5
        self.circle = self.canvas.create_oval(
            padding, padding, 
            60-padding, 60-padding, 
            fill="red",
            outline="white",  # Add white border
            width=2  # Border width
        )
        
        # For pulsing animation
        self.pulsing = False
        self.current_state = AssistantState.IDLE
        self.pulse_alpha = 0
        self.pulse_increasing = True
        
        # Add drag functionality
        self.canvas.bind('<Button-1>', self.start_drag)
        self.canvas.bind('<B1-Motion>', self.drag)
        
        # Position window in bottom-right corner initially
        self.position_window()
        
        # Make sure window is visible
        self.root.lift()
        self.root.attributes('-topmost', True)
        
        # Start update loop
        self.update_loop()
        print("GUI setup complete")
        
        self.setup_pending = False

    def position_window(self):
        try:
            # Get all monitors using root.winfo_screenwidth/height for each monitor
            import ctypes
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
            
            callback_type = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong,
                                             ctypes.POINTER(ctypes.c_long), ctypes.c_double)
            callback_function = callback_type(callback)
            user32.EnumDisplayMonitors(None, None, callback_function, 0)
            
            # If there's more than one monitor, use the second one
            if len(monitors) > 1:
                # Use the second monitor (index 1)
                monitor = monitors[1]
                # Position in bottom-right of second monitor
                x = monitor['left'] + 10
                y = monitor['bottom'] - 110
            else:
                # Fallback to primary monitor if no second monitor
                screen_width = self.root.winfo_screenwidth()
                screen_height = self.root.winfo_screenheight()
                x = screen_width - 70
                y = screen_height - 120
            
            self.root.geometry(f'+{x}+{y}')
            logger.info(f"Window positioned at {x}, {y}")
        except Exception as e:
            logger.error(f"Error positioning window: {e}")
            # Fallback to center of primary monitor
            self.root.eval('tk::PlaceWindow . center')

    def start_drag(self, event):
        self.x = event.x
        self.y = event.y

    def drag(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")

    def set_state(self, state: AssistantState):
        try:
            if self.root:
                self._handle_state_change(state)
                self.root.update_idletasks()
            else:
                self.command_queue.put(('set_state', state))
        except Exception as e:
            handle_error(logger, e, "Setting overlay state")

    def _handle_state_change(self, state: AssistantState):
        try:
            old_state = self.current_state
            self.current_state = state
            log_state_change(old_state, state)
            
            # Force stop any ongoing pulse animation
            self.pulsing = False
            
            if state == AssistantState.PROCESSING:
                self.pulsing = True
                self.pulse_alpha = 0
                self.pulse_increasing = True
            else:
                try:
                    # Map states to colors
                    color_map = {
                        AssistantState.IDLE: "#808080",        # Gray
                        AssistantState.LISTENING: "#0000FF",   # Blue
                        AssistantState.LISTENING_COMMAND: "#00FF00",  # Green
                        AssistantState.SPEAKING: "#FF00FF",    # Purple
                    }
                    color = color_map.get(state, state.value)
                    self.canvas.itemconfig(self.circle, fill=color)
                except Exception as e:
                    logger.error(f"Failed to set circle color: {e}")
            
            # Force update
            if self.root:
                self.root.update_idletasks()
                
        except Exception as e:
            logger.error(f"Error handling state change: {e}")

    def calculate_pulse_color(self, alpha):
        try:
            # Ensure alpha is between 0 and 1
            alpha = max(0, min(1, alpha))
            
            # Calculate RGB values for orange pulsing
            r = int(255 * (0.7 + 0.3 * alpha))  # Red varies from 179 to 255
            g = int(165 * (0.7 + 0.3 * alpha))  # Green varies from 116 to 165
            b = 0  # Blue stays at 0
            
            # Format color as hex, ensuring each component has 2 digits
            return f'#{r:02x}{g:02x}{b:02x}'
        except Exception as e:
            print(f"Error calculating pulse color: {e}")
            return "#ffa500"  # Default orange

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
                    
            color = self.calculate_pulse_color(self.pulse_alpha)
            self.canvas.itemconfig(self.circle, fill=color)
            
            if self.root:
                self.root.update_idletasks()
                
        except Exception as e:
            logger.error(f"Error updating pulse: {e}")
            self.pulsing = False

    def update_loop(self):
        try:
            if not self.running:
                logger.debug("Update loop stopped - not running")
                return
                
            self._process_command_queue()
            self._update_pulse_if_needed()
            self._ensure_window_on_top()
            self._schedule_next_update()
                
        except Exception as e:
            handle_error(logger, e, "Overlay update loop")

    def _process_command_queue(self):
        try:
            while True:
                command, *args = self.command_queue.get_nowait()
                if command == 'set_state':
                    self._handle_state_change(args[0])
        except queue.Empty:
            pass
        except Exception as e:
            handle_error(logger, e, "Processing command queue", silent=True)

    def _update_pulse_if_needed(self):
        if self.pulsing:
            self.update_pulse()

    def _ensure_window_on_top(self):
        if self.root:
            self.root.lift()
            self.root.attributes('-topmost', True)

    def _schedule_next_update(self):
        if self.running and self.root:
            self.root.after(50, self.update_loop)

    def close(self):
        try:
            self.running = False
            if self.root:
                self.root.quit()
                self.root.destroy()
        except Exception as e:
            print(f"Error closing overlay: {e}") 

    def test_colors(self):
        """Test all color states in sequence"""
        def cycle_colors():
            logger.debug("Starting color test cycle")
            states = list(AssistantState)
            current = 0
            
            def next_color():
                nonlocal current
                if current < len(states):
                    state = states[current]
                    logger.debug(f"Testing color: {state.name}")
                    self._handle_state_change(state)
                    current += 1
                    self.root.after(1000, next_color)
                else:
                    logger.debug("Color test cycle complete")
            
            next_color()
        
        if self.root:
            self.root.after(1000, cycle_colors)

    def update_icon_color(self, state):
        if state == AssistantState.IDLE:
            self.icon_label.configure(image=self.gray_icon)
        elif state == AssistantState.LISTENING:
            self.icon_label.configure(image=self.blue_icon)
        elif state == AssistantState.LISTENING_COMMAND:
            self.icon_label.configure(image=self.green_icon)  # New bright green icon for command mode
        elif state == AssistantState.PROCESSING:
            self.icon_label.configure(image=self.yellow_icon)
        elif state == AssistantState.SPEAKING:
            self.icon_label.configure(image=self.purple_icon)