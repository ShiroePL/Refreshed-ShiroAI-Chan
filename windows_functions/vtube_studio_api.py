import json
import threading
import time
import websocket
import os
class VTubeStudioAPI:
    def __init__(self):
        self.ws = None
        self.ws_thread = None
        self.connected = False
        self.connect()

    def connect(self):
        try:
            if self.ws:
                self.ws.close()
            
            self.ws = websocket.WebSocketApp(
                "ws://localhost:8001",
                on_open=self.on_open,
                on_message=self.on_message,
                on_close=self.on_close,
                on_error=self.on_error,
            )
            self.ws_thread = threading.Thread(target=self._run_forever)
            self.ws_thread.daemon = True
            self.ws_thread.start()
            time.sleep(0.5)
            self.connected = True
        except Exception as e:
            print(f"Failed to connect to VTube Studio: {e}")
            self.connected = False

    def _run_forever(self):
        """Wrapper for ws.run_forever() with reconnection logic"""
        retry_count = 0
        max_retries = 3
        while retry_count < max_retries:
            try:
                self.ws.run_forever(ping_interval=20)
                break
            except Exception as e:
                print(f"WebSocket connection failed (attempt {retry_count + 1}/{max_retries}): {e}")
                retry_count += 1
                if retry_count < max_retries:
                    time.sleep(2)  # Wait before retrying

    def on_open(self, ws, *args):
        print("WebSocket connection opened")
        self.authenticate()

    def on_message(self, ws, message, *args):
        print("Received message:", message)

    def on_close(self, ws, close_status_code, close_msg, *args):
        print(f"Connection closed (status: {close_status_code}, message: {close_msg})")
        self.connected = False

    def on_error(self, ws, error, *args):
        print("Error:", error)
        self.connected = False

    def close(self):
        if self.ws:
            try:
                self.ws.close()
                if self.ws_thread and self.ws_thread.is_alive():
                    self.ws_thread.join(timeout=1)  # Wait max 1 second
                self.connected = False
            except Exception as e:
                print(f"Error closing VTube Studio connection: {e}")

    def authenticate(self):
        self.ws.send(json.dumps({
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": "SomeID",
            "messageType": "AuthenticationRequest",
            "data": {
                "pluginName": "Shiro chan",
                "pluginDeveloper": "Madrus",
                "authenticationToken": os.getenv("VTUBE_TOKEN") #
            }
        }))

    def play_animation(self, hotkeyID):
        self.ws.send(json.dumps({
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": "SomeID",
            "messageType": "HotkeyTriggerRequest",
            "data": {
                "hotkeyID": hotkeyID
            }
        }))