from typing import List, Dict
from datetime import datetime
from src.utils.logging_config import setup_logger
from src.config.service_config import CHAT_HISTORY_PAIRS

logger = setup_logger("db_cache")

class ChatHistoryCache:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.history_cache = []
            cls._instance.max_pairs = CHAT_HISTORY_PAIRS
            logger.info(f"[CACHE] Chat history cache initialized with {CHAT_HISTORY_PAIRS} pairs limit")
        return cls._instance
    
    def update_cache(self, messages: List[Dict]):
        """Update the cache with new messages"""
        start_time = datetime.now()
        logger.info(f"[CACHE] Previous cache size: {len(self.history_cache)}")
        
        # Since messages come in pairs, we need to handle them differently
        convert_start = datetime.now()
        pairs = []
        for msg in messages:
            if 'question' in msg and 'answer' in msg:
                # Convert DB format to our cache format
                pairs.extend([
                    {
                        "role": "Madrus",
                        "content": msg['question'],
                        "timestamp": msg['timestamp'] if 'timestamp' in msg else datetime.now().isoformat()
                    },
                    {
                        "role": "Shiro",
                        "content": msg['answer'],
                        "timestamp": msg['timestamp'] if 'timestamp' in msg else datetime.now().isoformat()
                    }
                ])
        convert_duration = (datetime.now() - convert_start).total_seconds()
        logger.info(f"[CACHE] Message conversion completed in {convert_duration:.3f} seconds")
        
        # Keep only the last max_pairs
        self.history_cache = pairs[-(self.max_pairs * 2):]  # Times 2 because each pair is 2 messages
        
        total_duration = (datetime.now() - start_time).total_seconds()
        if self.history_cache:
            latest = self.history_cache[-1]
            logger.info(f"[CACHE] Latest cached exchange - Content: {latest['content'][:30]}...")
        logger.info(f"[CACHE] Updated cache with {len(self.history_cache)} messages in {total_duration:.3f} seconds")
    
    def get_cached_history(self) -> List[Dict]:
        """Get cached messages"""
        return self.history_cache
    
    def add_new_exchange(self, question: str, answer: str):
        """Add a new message pair to the cache"""
        logger.info(f"[CACHE] Adding new exchange to cache. Current size: {len(self.history_cache)}")
        
        # Create new exchange entries
        new_exchanges = [
            {
                "role": "Madrus",
                "content": question,
                "timestamp": datetime.now().isoformat()
            },
            {
                "role": "Shiro",
                "content": answer,
                "timestamp": datetime.now().isoformat()
            }
        ]
        
        # Remove oldest pair if we're at max capacity
        if len(self.history_cache) >= (self.max_pairs * 2):  # Times 2 because each pair is 2 messages
            self.history_cache = self.history_cache[2:]  # Remove oldest pair
        
        # Add new pair
        self.history_cache.extend(new_exchanges)
        logger.info(f"[CACHE] Added new exchange. New cache size: {len(self.history_cache)}")