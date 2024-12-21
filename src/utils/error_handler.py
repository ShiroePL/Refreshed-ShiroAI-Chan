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