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
            self.ws = websocket.WebSocketApp(
                "ws://localhost:8001",
                on_open=self.on_open,
                on_message=self.on_message,
                on_close=self.on_close,
                on_error=self.on_error,
            )
            self.ws_thread = threading.Thread(target=self.ws.run_forever, kwargs={"ping_interval": 20})
            self.ws_thread.daemon = True  # Make thread daemon so it closes with main program
            self.ws_thread.start()
            time.sleep(0.5)  # Reduced sleep time
            self.connected = True
        except Exception as e:
            print(f"Failed to connect to VTube Studio: {e}")
            self.connected = False

    def on_open(self, ws):
        print("WebSocket connection opened")
        self.authenticate()

    def on_message(self, ws, message):
        print("Received message:", message)

    def on_close(self, ws):
        print("Connection closed")

    def close(self):
        if self.ws:
            try:
                self.ws.close()
                if self.ws_thread and self.ws_thread.is_alive():
                    self.ws_thread.join(timeout=1)  # Wait max 1 second
                self.connected = False
            except Exception as e:
                print(f"Error closing VTube Studio connection: {e}")

    def on_error(self, ws, error):
        print("Error:", error)

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