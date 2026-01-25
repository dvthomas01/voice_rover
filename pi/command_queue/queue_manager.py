"""Thread-safe command queue with priority handling."""

from typing import Optional
import queue
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
        self._queue = queue.PriorityQueue(maxsize=max_size)
        self._lock = threading.Lock()

    def enqueue(self, command: Command) -> bool:
        """Add command to queue.

        Args:
            command: Command to enqueue

        Returns:
            True if successfully enqueued, False if queue is full
        """
        with self._lock:
            if self._queue.full():
                return False
            
            try:
                priority_tuple = (-command.priority, id(command), command)
                self._queue.put(priority_tuple, block=False)
                return True
            except queue.Full:
                return False

    def dequeue(self, timeout: Optional[float] = None) -> Optional[Command]:
        """Remove and return highest priority command from queue.

        Args:
            timeout: Maximum time to wait for command (None = wait forever)

        Returns:
            Next command, or None if timeout reached
        """
        try:
            priority, _, command = self._queue.get(timeout=timeout)
            return command
        except queue.Empty:
            return None

    def clear(self) -> None:
        """Clear all commands from queue.

        CRITICAL: This must be called when STOP command is received.
        """
        with self._lock:
            while not self._queue.empty():
                try:
                    self._queue.get_nowait()
                except queue.Empty:
                    break

    def is_empty(self) -> bool:
        """Check if queue is empty.

        Returns:
            True if queue is empty
        """
        return self._queue.empty()

    def size(self) -> int:
        """Get current queue size.

        Returns:
            Number of commands in queue
        """
        return self._queue.qsize()
