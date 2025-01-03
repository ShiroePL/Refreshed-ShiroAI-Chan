from typing import List, Dict, Optional
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
        logger.debug(f"[CACHE] Received messages to cache: {messages}")
        
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
        logger.debug(f"[CACHE] Converted pairs: {pairs}")
        
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

class ContextCache:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.context = None
            cls._instance.needs_refresh = True  # Initially true to force first load
            cls._instance.last_update = None
            logger.info("[CACHE] Context cache initialized")
        return cls._instance
    
    def get_context(self) -> Optional[str]:
        """Get cached context"""
        return self.context
    
    def update_context(self, new_context: str):
        """Update cached context"""
        self.context = new_context
        self.last_update = datetime.now()
        self.needs_refresh = False
        logger.info(f"[CACHE] Context updated: {new_context[:50]}...")
    
    def mark_for_refresh(self):
        """Mark context as needing refresh"""
        self.needs_refresh = True
        logger.info("[CACHE] Context marked for refresh")
    
    def should_refresh(self) -> bool:
        """Check if context needs refreshing"""
        return self.needs_refresh