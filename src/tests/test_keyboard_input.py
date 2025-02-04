"""
Tests for the keyboard input module.
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(src_dir))

from utils.keyboard_input import (
    get_pid,
    send_key,
    send_cmd_enter,
    send_string,
    KeyboardAutomator,
    VK_MAP
)

class TestKeyboardInput(unittest.TestCase):
    @patch('subprocess.run')
    def test_get_pid_success(self, mock_run):
        """Test successful process ID retrieval."""
        mock_run.return_value = Mock(stdout="12345\n", stderr="")
        pid = get_pid("TestApp")
        self.assertEqual(pid, 12345)
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_get_pid_not_found(self, mock_run):
        """Test process ID retrieval when process not found."""
        mock_run.return_value = Mock(stdout="", stderr="")
        pid = get_pid("NonexistentApp")
        self.assertIsNone(pid)

    @patch('Quartz.CGEventCreateKeyboardEvent')
    @patch('Quartz.CGEventPostToPid')
    def test_send_key(self, mock_post, mock_create):
        """Test sending keyboard events."""
        mock_event = Mock()
        mock_create.return_value = mock_event

        # Test key press
        send_key(12345, ord('a'), True)
        mock_create.assert_called_with(None, ord('a'), True)
        mock_post.assert_called_with(12345, mock_event)

        # Test key release
        send_key(12345, ord('a'), False)
        mock_create.assert_called_with(None, ord('a'), False)
        mock_post.assert_called_with(12345, mock_event)

    @patch('utils.keyboard_input.send_key')
    def test_send_cmd_enter(self, mock_send_key):
        """Test sending Cmd+Enter combination."""
        send_cmd_enter(12345)
        self.assertEqual(mock_send_key.call_count, 4)  # 2 keys x press/release

    @patch('utils.keyboard_input.send_key')
    def test_send_string(self, mock_send_key):
        """Test sending a string as keyboard events."""
        test_string = "test"
        send_string(12345, test_string)
        
        # Each character should generate press and release events
        expected_calls = len(test_string) * 2
        self.assertEqual(mock_send_key.call_count, expected_calls)

class TestKeyboardAutomator(unittest.TestCase):
    @patch('utils.keyboard_input.get_pid')
    def setUp(self, mock_get_pid):
        """Set up test fixtures."""
        mock_get_pid.return_value = 12345
        self.automator = KeyboardAutomator("TestApp")

    def test_init(self):
        """Test initialization."""
        self.assertEqual(self.automator.app_name, "TestApp")
        self.assertEqual(self.automator.pid, 12345)
        self.assertFalse(self.automator.running)
        self.assertEqual(len(self.automator.threads), 0)

    def test_start_success(self):
        """Test successful start."""
        result = self.automator.start()
        self.assertTrue(result)
        self.assertTrue(self.automator.running)

    @patch('utils.keyboard_input.get_pid')
    def test_start_failure(self, mock_get_pid):
        """Test start failure when process not found."""
        mock_get_pid.return_value = None
        automator = KeyboardAutomator("NonexistentApp")
        result = automator.start()
        self.assertFalse(result)
        self.assertFalse(automator.running)

    @patch('utils.keyboard_input.send_cmd_enter')
    def test_start_cmd_enter_task(self, mock_send_cmd_enter):
        """Test starting Cmd+Enter task."""
        self.automator.start()
        self.automator.start_cmd_enter_task(interval_seconds=0.1)
        self.assertEqual(len(self.automator.threads), 1)
        self.assertTrue(self.automator.threads[0].is_alive())

    @patch('utils.keyboard_input.send_string')
    def test_start_continue_task(self, mock_send_string):
        """Test starting continue message task."""
        self.automator.start()
        self.automator.start_continue_task(interval_minutes=0.001, message="test")
        self.assertEqual(len(self.automator.threads), 1)
        self.assertTrue(self.automator.threads[0].is_alive())

    def test_stop(self):
        """Test stopping automation."""
        self.automator.start()
        self.automator.start_cmd_enter_task(interval_seconds=0.1)
        self.automator.start_continue_task(interval_minutes=0.001)
        
        # Let tasks run briefly
        import time
        time.sleep(0.2)
        
        # Stop automation
        self.automator.stop()
        self.assertFalse(self.automator.running)
        self.assertEqual(len(self.automator.threads), 0)

if __name__ == '__main__':
    unittest.main() 