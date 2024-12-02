import time

def handle_response(command, assistant):
    """Handle different types of commands and return appropriate responses."""
    command = command.lower()
    
    # Dictionary of command handlers
    handlers = {
        'hello': lambda: "Hello there! How can I help you?",
        'stop': lambda: handle_stop(assistant),
        'time': lambda: f"The current time is {time.strftime('%H:%M')}",
    }

    # Check if any command matches
    for key, handler in handlers.items():
        if key in command:
            return handler()

    return "I didn't quite understand that."

def handle_stop(assistant):
    """Handle the stop command."""
    assistant.listening = False
    return "Stopping listening!" 