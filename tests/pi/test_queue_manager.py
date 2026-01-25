"""Unit tests for command queue manager."""

import pytest
import threading
import time
from pi.command_queue.queue_manager import CommandQueueManager
from pi.command_parser.command_schema import Command, CommandType, PRIORITY_STOP, PRIORITY_NORMAL


class TestCommandQueueManager:
    """Test cases for CommandQueueManager."""

    def setup_method(self):
        """Set up test fixtures."""
        self.queue = CommandQueueManager(max_size=10)

    def test_enqueue_dequeue(self):
        """Test basic enqueue and dequeue operations."""
        cmd = Command(CommandType.MOVE_FORWARD, {"speed": 0.4}, PRIORITY_NORMAL)
        
        assert self.queue.enqueue(cmd) is True
        assert self.queue.is_empty() is False
        assert self.queue.size() == 1
        
        dequeued = self.queue.dequeue()
        assert dequeued is not None
        assert dequeued.command_type == CommandType.MOVE_FORWARD
        assert self.queue.is_empty() is True

    def test_priority_ordering(self):
        """Test that STOP command dequeues first."""
        cmd1 = Command(CommandType.MOVE_FORWARD, {"speed": 0.4}, PRIORITY_NORMAL)
        cmd2 = Command(CommandType.MOVE_BACKWARD, {"speed": 0.4}, PRIORITY_NORMAL)
        cmd3 = Command(CommandType.STOP, {}, PRIORITY_STOP)
        
        self.queue.enqueue(cmd1)
        self.queue.enqueue(cmd2)
        self.queue.enqueue(cmd3)
        
        first = self.queue.dequeue()
        assert first.command_type == CommandType.STOP
        
        second = self.queue.dequeue()
        assert second.command_type == CommandType.MOVE_FORWARD
        
        third = self.queue.dequeue()
        assert third.command_type == CommandType.MOVE_BACKWARD

    def test_clear_queue(self):
        """Test clearing the queue."""
        cmd1 = Command(CommandType.MOVE_FORWARD, {"speed": 0.4}, PRIORITY_NORMAL)
        cmd2 = Command(CommandType.MOVE_BACKWARD, {"speed": 0.4}, PRIORITY_NORMAL)
        
        self.queue.enqueue(cmd1)
        self.queue.enqueue(cmd2)
        assert self.queue.size() == 2
        
        self.queue.clear()
        assert self.queue.is_empty() is True
        assert self.queue.size() == 0

    def test_stop_priority(self):
        """Test STOP command always dequeues first regardless of order."""
        cmd1 = Command(CommandType.MOVE_FORWARD, {"speed": 0.4}, PRIORITY_NORMAL)
        cmd2 = Command(CommandType.STOP, {}, PRIORITY_STOP)
        cmd3 = Command(CommandType.MOVE_BACKWARD, {"speed": 0.4}, PRIORITY_NORMAL)
        
        self.queue.enqueue(cmd1)
        self.queue.enqueue(cmd2)
        self.queue.enqueue(cmd3)
        
        first = self.queue.dequeue()
        assert first.command_type == CommandType.STOP

    def test_queue_full(self):
        """Test queue full condition."""
        queue = CommandQueueManager(max_size=2)
        
        cmd1 = Command(CommandType.MOVE_FORWARD, {"speed": 0.4}, PRIORITY_NORMAL)
        cmd2 = Command(CommandType.MOVE_BACKWARD, {"speed": 0.4}, PRIORITY_NORMAL)
        cmd3 = Command(CommandType.ROTATE_CLOCKWISE, {"speed": 0.4}, PRIORITY_NORMAL)
        
        assert queue.enqueue(cmd1) is True
        assert queue.enqueue(cmd2) is True
        assert queue.enqueue(cmd3) is False

    def test_dequeue_timeout(self):
        """Test dequeue with timeout."""
        result = self.queue.dequeue(timeout=0.1)
        assert result is None

    def test_thread_safety_enqueue(self):
        """Test thread-safe enqueue operations."""
        queue = CommandQueueManager(max_size=50)
        
        def enqueue_commands():
            for _ in range(10):
                cmd = Command(CommandType.MOVE_FORWARD, {"speed": 0.4}, PRIORITY_NORMAL)
                queue.enqueue(cmd)
        
        threads = [threading.Thread(target=enqueue_commands) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert queue.size() == 30

    def test_thread_safety_dequeue(self):
        """Test thread-safe dequeue operations."""
        for i in range(10):
            cmd = Command(CommandType.MOVE_FORWARD, {"speed": 0.4}, PRIORITY_NORMAL)
            self.queue.enqueue(cmd)
        
        results = []
        
        def dequeue_commands():
            for _ in range(5):
                cmd = self.queue.dequeue()
                if cmd:
                    results.append(cmd)
        
        threads = [threading.Thread(target=dequeue_commands) for _ in range(2)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(results) == 10

    def test_fifo_for_same_priority(self):
        """Test FIFO ordering for commands with same priority."""
        cmd1 = Command(CommandType.MOVE_FORWARD, {"speed": 0.4}, PRIORITY_NORMAL)
        cmd2 = Command(CommandType.MOVE_BACKWARD, {"speed": 0.4}, PRIORITY_NORMAL)
        cmd3 = Command(CommandType.ROTATE_CLOCKWISE, {"speed": 0.4}, PRIORITY_NORMAL)
        
        self.queue.enqueue(cmd1)
        self.queue.enqueue(cmd2)
        self.queue.enqueue(cmd3)
        
        assert self.queue.dequeue().command_type == CommandType.MOVE_FORWARD
        assert self.queue.dequeue().command_type == CommandType.MOVE_BACKWARD
        assert self.queue.dequeue().command_type == CommandType.ROTATE_CLOCKWISE

    def test_clear_during_operations(self):
        """Test clearing queue during concurrent operations."""
        def enqueue_and_clear():
            for i in range(5):
                cmd = Command(CommandType.MOVE_FORWARD, {"speed": 0.4}, PRIORITY_NORMAL)
                self.queue.enqueue(cmd)
            self.queue.clear()
        
        thread = threading.Thread(target=enqueue_and_clear)
        thread.start()
        thread.join()
        
        assert self.queue.is_empty() is True
