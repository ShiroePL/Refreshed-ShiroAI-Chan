# Service URLs
BRAIN_MODULE_URL = "http://127.0.0.1:8015"
AI_SERVICE_URL = "http://127.0.0.1:8013"
VTUBE_MODULE_URL = "http://127.0.0.1:8002"
FRONTEND_URL = "http://127.0.0.1:5000"
DB_MODULE_URL = "http://127.0.0.1:8014"

# Number of message pairs (user:assistant) to fetch for chat history
CHAT_HISTORY_PAIRS = 5  # Changed from hardcoded 30 to 5 pairs

# Logging configuration
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_LEVEL = 'INFO' 