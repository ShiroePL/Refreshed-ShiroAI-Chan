import logging
from pathlib import Path
from colorama import Back, init, Fore, Style
import sys

# Initialize colorama
init()

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors"""
    
    COLORS = {
        'DEBUG': Fore.CYAN,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Style.BRIGHT,
        
        # Custom labels
        'STARTUP': Fore.BLUE + Style.BRIGHT,
        'INIT': Fore.CYAN + Style.BRIGHT,
        'CONNECT': Fore.BLUE + Style.BRIGHT,
        'DISCONNECT': Fore.MAGENTA,
        'RECEIVE': Fore.GREEN,
        'GROQ': Fore.YELLOW,
        'TTS': Fore.MAGENTA,
        'SEND': Fore.GREEN + Style.BRIGHT,
        'SUCCESS': Fore.GREEN + Style.BRIGHT,
        'WARNING': Fore.YELLOW + Style.BRIGHT,
        'ERROR': Fore.RED + Style.BRIGHT,
        'SHUTDOWN': Fore.RED,
        'HTTP': Fore.BLUE,
        
        # Added missing labels
        'TRANSCRIPT': Fore.MAGENTA + Style.BRIGHT + Back.CYAN,  # Rainbow-like effect for high visibility of new messages
        'POST': Fore.BLUE + Style.BRIGHT,        # HTTP POST requests
        'GET': Fore.BLUE,                        # HTTP GET requests
        'SERVICE': Fore.YELLOW + Style.BRIGHT,   # Service-related logs
        'PROMPT': Fore.MAGENTA,   # AI prompt-related logs
        'SAVE': Fore.YELLOW,      # Save-related logs
        'BACKOFF': Fore.YELLOW,  # Backoff-related logs
        'OPENAI': Fore.BLUE,    # OpenAI-related logs
    }

    def format(self, record):
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{Style.RESET_ALL}"
        
        for label, color in self.COLORS.items():
            if f"[{label}]" in record.msg:
                record.msg = record.msg.replace(
                    f"[{label}]",
                    f"{color}[{label}]{Style.RESET_ALL}"
                )
        
        return super().format(record)

def setup_logger(module_name: str) -> logging.Logger:
    """
    Setup a logger for a specific module with both console and file output
    
    Args:
        module_name: Name of the module (e.g., 'ai', 'brain', 'main')
        
    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logs directory if it doesn't exist
    Path("logs").mkdir(exist_ok=True)
    
    # Get or create logger
    logger = logging.getLogger(module_name)
    logger.setLevel(logging.INFO)
    logger.propagate = False  # Prevent double logging
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(ColoredFormatter(
        '%(asctime)s - [%(name)s] - %(levelname)s - %(message)s'
    ))
    console_handler.setLevel(logging.INFO)
    
    # File handler without colors
    file_handler = logging.FileHandler(f'logs/{module_name}.log', encoding='utf-8')
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - [%(name)s] - %(levelname)s - %(message)s'
    ))
    
    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    # Configure specific loggers to be less verbose
    quiet_loggers = ['werkzeug', 'engineio', 'socketio', 'uvicorn', 
                     'uvicorn.error', 'uvicorn.access', 'fastapi']
    
    for quiet_logger in quiet_loggers:
        logging.getLogger(quiet_logger).setLevel(logging.WARNING)
    
    return logger

def handle_error(logger: logging.Logger, error: Exception, context: str, silent: bool = False):
    """Centralized error handling"""
    error_msg = f"{context}: {str(error)}"
    if silent:
        logger.debug(error_msg, exc_info=True)
    else:
        logger.error(error_msg, exc_info=True)