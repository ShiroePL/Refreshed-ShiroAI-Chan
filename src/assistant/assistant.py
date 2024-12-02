class SimpleAssistant:
    def __init__(self):
        self.listening = False
        self.last_command = ""
        self.response = ""
        self.running = True

    def get_response(self, command):
        """Get response from the response handler."""
        from .response_handler import handle_response
        return handle_response(command, self) 