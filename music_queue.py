"""Music queue management for the Discord Music Bot."""

import random
from typing import List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class MusicQueue:
    """Queue for managing music playback."""
    
    def __init__(self) -> None:
        self.queue: List[Any] = []
        self.current: Optional[Any] = None
        self.loop_mode: bool = False
        
    def add(self, song: Any) -> None:
        """Add song to queue."""
        self.queue.append(song)
        logger.info(f"Added song to queue: {song.title}")
        
    def get_next(self) -> Optional[Any]:
        """Get next song from queue."""
        if self.loop_mode and self.current:
            logger.info(f"Loop mode: repeating {self.current.title}")
            return self.current
            
        if self.queue:
            self.current = self.queue.pop(0)
            logger.info(f"Playing next song: {self.current.title}")
            return self.current
        
        self.current = None
        return None
        
    def clear(self) -> None:
        """Clear the queue."""
        logger.info(f"Clearing queue with {len(self.queue)} songs")
        self.queue.clear()
        self.current = None
        
    def shuffle(self) -> None:
        """Shuffle the queue."""
        random.shuffle(self.queue)
        logger.info(f"Shuffled queue with {len(self.queue)} songs")
        
    def skip(self) -> Optional[Any]:
        """Skip current song."""
        if self.queue:
            self.current = self.queue.pop(0)
            logger.info(f"Skipped to: {self.current.title}")
            return self.current
        
        self.current = None
        logger.info("No more songs in queue")
        return None
    
    @property
    def size(self) -> int:
        """Get the current queue size."""
        return len(self.queue)
    
    @property
    def is_empty(self) -> bool:
        """Check if queue is empty."""
        return len(self.queue) == 0 and self.current is None
