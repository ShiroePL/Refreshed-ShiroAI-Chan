import threading
import time
from flask_socketio import emit
import logging

logger = logging.getLogger(__name__)

class TimerService:
    def __init__(self):
        self.timer = None
        self.is_running = False

    def start_timer(self, duration):
        if self.is_running:
            return False

        self.is_running = True
        self.timer = threading.Thread(target=self._run_timer, args=(duration,))
        self.timer.daemon = True
        self.timer.start()
        return True

    def _run_timer(self, duration):
        try:
            start_time = time.time()
            while time.time() - start_time < duration:
                if not self.is_running:
                    break
                    
                remaining = duration - int(time.time() - start_time)
                emit('timer_update', {'remaining': remaining}, namespace='/')
                time.sleep(1)

            if self.is_running:
                emit('timer_complete', namespace='/')
                
        except Exception as e:
            logger.error(f"Timer error: {e}")
        finally:
            self.is_running = False 