from src.utils.logging_config import setup_logger, handle_error

# Setup main logger
logger = setup_logger('main')

from dotenv import load_dotenv
from src.app_instance import socketio, app

# Load environment variables
load_dotenv()

if __name__ == '__main__':
    try:
        logger.info("[STARTUP] Starting main application...")
        socketio.run(
            app, 
            host="0.0.0.0", 
            port=5000, 
            debug=True
        )
    except Exception as e:
        handle_error(logger, e, "Application startup")