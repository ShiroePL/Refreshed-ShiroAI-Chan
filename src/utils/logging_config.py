import logging
from .error_handler import handle_error

def setup_logging():
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )

    # Get the root logger
    logger = logging.getLogger()

    # Configure specific loggers
    loggers_config = {
        'werkzeug': logging.WARNING,
        'engineio': logging.WARNING,
        'socketio': logging.WARNING,
        'httpx': logging.WARNING,
        'httpcore': logging.WARNING,
        'groq': logging.WARNING,
    }

    # Apply configurations
    for logger_name, level in loggers_config.items():
        logging.getLogger(logger_name).setLevel(level)

    return logger