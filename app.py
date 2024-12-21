from src.utils.logging_config import setup_logging, handle_error
import logging

# Setup logging first thing
logger = setup_logging()

from dotenv import load_dotenv
from src.app_instance import socketio, app

# Load environment variables
load_dotenv()

if __name__ == '__main__':
    try:
        socketio.run(app, debug=True)
    except Exception as e:
        handle_error(logger, e, "Application startup")
