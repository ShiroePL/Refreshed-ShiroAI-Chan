from dotenv import load_dotenv
from src import app, socketio

# Load environment variables
load_dotenv()

if __name__ == '__main__':
    socketio.run(app, debug=True)
