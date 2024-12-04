import tkinter as tk
from enum import Enum
import queue
from threading import Thread, Lock

class AssistantState(Enum):
    IDLE = "red"
    LISTENING = "blue"
    PROCESSING = "orange"
    SPEAKING = "green"

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

    def setup_gui(self):
        if not self.setup_pending:
            return
            
        self.root = tk.Tk()
        self.root.title("Assistant Status")
        
        # Make window floating and always on top
        self.root.attributes('-topmost', True)
        self.root.overrideredirect(True)  # Remove window decorations
        
        # Create a circular indicator
        self.canvas = tk.Canvas(self.root, width=40, height=40, bg='black', 
                              highlightthickness=0)
        self.canvas.pack()
        
        # Initialize the circle
        self.circle = self.canvas.create_oval(5, 5, 35, 35, fill="red")
        
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
        
        # Start update loop
        self.update_loop()
        
        self.setup_pending = False

    def position_window(self):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.root.geometry(f'+{screen_width-50}+{screen_height-100}')
    
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
        if self.root:
            self.root.after_idle(self._handle_state_change, state)
        else:
            self.command_queue.put(('set_state', state))

    def _handle_state_change(self, state: AssistantState):
        self.current_state = state
        if state == AssistantState.PROCESSING:
            self.pulsing = True
        else:
            self.pulsing = False
            self.canvas.itemconfig(self.circle, fill=state.value)

    def calculate_pulse_color(self, alpha):
        # Convert from orange to darker orange
        return f'#{int(255*(1-alpha/2)):02x}{int(165*(1-alpha/2)):02x}00'

    def update_pulse(self):
        if self.pulsing:
            if self.pulse_increasing:
                self.pulse_alpha += 0.1
                if self.pulse_alpha >= 1:
                    self.pulse_increasing = False
            else:
                self.pulse_alpha -= 0.1
                if self.pulse_alpha <= 0:
                    self.pulse_increasing = True
                    
            color = self.calculate_pulse_color(self.pulse_alpha)
            self.canvas.itemconfig(self.circle, fill=color)

    def update_loop(self):
        if not self.running:
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
        self.update_pulse()

        # Schedule the next update
        if self.running and self.root:
            self.root.after(50, self.update_loop)

    def close(self):
        self.running = False
        if self.root:
            self.root.quit()
            self.root.destroy() 