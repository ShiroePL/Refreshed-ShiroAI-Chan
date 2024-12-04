import tkinter as tk
from enum import Enum
import queue
from threading import Thread, Lock
import logging

# Configure logging to be more concise
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
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
    logger.info(f"Assistant State: {to_state.name}")

class AssistantState(Enum):
    IDLE = "red"
    LISTENING = "blue"
    PROCESSING = "orange"
    SPEAKING = "pink"

class StatusOverlay:
    _instance = None
    _lock = Lock()
    
    @classmethod
    def get_instance(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance
    
    def __init__(self):
        if StatusOverlay._instance is not None:
            raise Exception("This class is a singleton!")
            
        self.command_queue = queue.Queue()
        self.running = True
        self.root = None
        self.setup_pending = True
        StatusOverlay._instance = self
        print("StatusOverlay initialized")

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
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            # Position slightly higher from bottom
            self.root.geometry(f'+{screen_width-70}+{screen_height-120}')
            print(f"Window positioned at {screen_width-70}, {screen_height-120}")
        except Exception as e:
            print(f"Error positioning window: {e}")

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
            log_state_change(self.current_state, state)
            if self.root:
                # Apply change directly instead of using after_idle
                self._handle_state_change(state)
                # Force update
                self.root.update_idletasks()
            else:
                self.command_queue.put(('set_state', state))
        except Exception as e:
            logger.error(f"Error setting state: {e}", exc_info=True)

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
                    self.canvas.itemconfig(self.circle, fill=state.value)
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
                
            # Handle any pending commands
            try:
                while True:
                    command, *args = self.command_queue.get_nowait()
                    if command == 'set_state':
                        self._handle_state_change(args[0])
            except queue.Empty:
                pass

            # Update pulse animation if needed
            if self.pulsing:
                self.update_pulse()

            # Ensure window stays on top
            if self.root:
                self.root.lift()
                self.root.attributes('-topmost', True)

            # Schedule the next update
            if self.running and self.root:
                self.root.after(50, self.update_loop)
                
        except Exception as e:
            logger.error(f"Error in update loop: {e}", exc_info=True)

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