import logging

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

# Create a consistent error handler
def handle_error(logger, error, context="Operation", silent=False):
    """
    Centralized error handling function
    :param logger: Logger instance
    :param error: Exception that occurred
    :param context: String describing where the error occurred
    :param silent: If True, only log at debug level
    """
    error_msg = f"{context} failed: {str(error)}"
    if silent:
        logger.debug(error_msg, exc_info=True)
    else:
        logger.error(error_msg, exc_info=True)
    return False  # Operation failed 