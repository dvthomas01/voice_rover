"""Thread-safe command queue with priority handling."""

from typing import Optional
from queue import PriorityQueue
import threading
from ..command_parser.command_schema import Command, PRIORITY_STOP


class CommandQueueManager:
    """Manages command queue with priority handling and thread safety."""

    def __init__(self, max_size: int = 100):
        """Initialize command queue manager.

        Args:
            max_size: Maximum queue size
        """
        self.max_size = max_size
        self._queue = PriorityQueue(maxsize=max_size)
        self._lock = threading.Lock()
        self._stop_event = threading.Event()

    def enqueue(self, command: Command) -> bool:
        """Add command to queue.

        Args:
            command: Command to enqueue

        Returns:
            True if successfully enqueued, False if queue is full
            
        TODO: Add command to priority queue
        TODO: Use negative priority (PriorityQueue is min-heap, we want max priority first)
        TODO: Thread-safe operation
        """
        # TODO: Implement enqueue
        # PriorityQueue uses min-heap, so use negative priority for max priority first
        # try:
        #     self._queue.put((-command.priority, id(command), command), block=False)
        #     return True
        # except queue.Full:
        #     return False
        
        return False

    def dequeue(self, timeout: Optional[float] = None) -> Optional[Command]:
        """Remove and return highest priority command from queue.

        Args:
            timeout: Maximum time to wait for command (None = wait forever)

        Returns:
            Next command, or None if timeout reached
            
        TODO: Get command from priority queue
        TODO: Handle timeout
        TODO: Thread-safe operation
        """
        # TODO: Implement dequeue
        # try:
        #     priority, _, command = self._queue.get(timeout=timeout)
        #     return command
        # except queue.Empty:
        #     return None
        
        return None

    def clear(self) -> None:
        """Clear all commands from queue.

        CRITICAL: This must be called when STOP command is received.
        
        TODO: Clear all items from queue
        TODO: Thread-safe operation
        """
        # TODO: Implement clear
        # with self._lock:
        #     while not self._queue.empty():
        #         try:
        #             self._queue.get_nowait()
        #         except queue.Empty:
        #             break
        pass

    def is_empty(self) -> bool:
        """Check if queue is empty.

        Returns:
            True if queue is empty
            
        TODO: Check if queue is empty
        """
        # TODO: Implement
        # return self._queue.empty()
        return True

    def size(self) -> int:
        """Get current queue size.

        Returns:
            Number of commands in queue
            
        TODO: Get queue size
        """
        # TODO: Implement
        # return self._queue.qsize()
        return 0
