"""
Tests for the game automation module.
"""

import os
import sys
import time
import unittest
from unittest.mock import Mock, patch
import numpy as np
from pathlib import Path
import subprocess

# Add src directory to Python path
src_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(src_dir))

from automation.game_loop import GameAutomation

class TestGameAutomation(unittest.TestCase):
    @patch('subprocess.run')
    def setUp(self, mock_run):
        """Set up test fixtures."""
        # Mock process listing
        mock_run.return_value = Mock(
            stdout="Finder, mGBA-Qt, Terminal",
            stderr=""
        )
        
        self.automation = GameAutomation(window_name="mGBA")
        
        # Create test screenshot directory
        self.test_screenshots_dir = Path("test_screenshots")
        self.test_screenshots_dir.mkdir(exist_ok=True)
        self.automation.screenshots_dir = self.test_screenshots_dir

    def tearDown(self):
        """Clean up test fixtures."""
        # Remove test screenshots
        for file in self.test_screenshots_dir.glob("*.png"):
            file.unlink()
        self.test_screenshots_dir.rmdir()

    @patch('subprocess.run')
    @patch('utils.keyboard_input.get_pid')
    def test_init_exact_match(self, mock_get_pid, mock_run):
        """Test initialization with exact process match."""
        mock_run.return_value = Mock(stdout="mGBA", stderr="")
        mock_get_pid.return_value = 12345
        
        automation = GameAutomation(window_name="mGBA")
        self.assertEqual(automation.window_name, "mGBA")
        self.assertEqual(automation.pid, 12345)
        self.assertIsNone(automation.last_state)
        self.assertEqual(automation.last_action_time, 0)

    @patch('subprocess.run')
    @patch('utils.keyboard_input.get_pid')
    def test_init_partial_match(self, mock_get_pid, mock_run):
        """Test initialization with partial process name match."""
        mock_run.return_value = Mock(stdout="mGBA-Qt", stderr="")
        mock_get_pid.return_value = 12345
        
        automation = GameAutomation(window_name="mGBA")
        self.assertEqual(automation.window_name, "mGBA")
        self.assertEqual(automation.pid, 12345)

    @patch('subprocess.run')
    def test_init_process_not_found(self, mock_run):
        """Test initialization when process is not found."""
        mock_run.return_value = Mock(stdout="Finder, Terminal", stderr="")
        with self.assertRaises(RuntimeError):
            GameAutomation(window_name="NonexistentWindow")

    @patch('subprocess.run')
    def test_find_process_error(self, mock_run):
        """Test process finding when AppleScript fails."""
        mock_run.side_effect = subprocess.CalledProcessError(1, 'osascript')
        with self.assertRaises(RuntimeError):
            GameAutomation(window_name="mGBA")

    @patch('subprocess.run')
    def test_capture_window_not_found(self, mock_run):
        """Test window capture when window is not found."""
        mock_run.return_value = Mock(stdout="", stderr="")
        screenshot = self.automation.capture_window()
        self.assertIsNone(screenshot)

    @patch('subprocess.run')
    @patch('cv2.imread')
    def test_capture_window_success(self, mock_imread, mock_run):
        """Test successful window capture."""
        # Mock AppleScript result
        mock_run.side_effect = [
            Mock(stdout="12345\n", stderr=""),  # Window ID
            Mock(returncode=0)  # screencapture command
        ]

        # Mock image reading
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        mock_imread.return_value = test_image
        
        screenshot = self.automation.capture_window()
        self.assertIsNotNone(screenshot)
        self.assertEqual(screenshot.shape, (100, 100, 3))

    def test_should_process_first_state(self):
        """Test should_process with first state."""
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        self.assertTrue(self.automation.should_process(test_image))
        self.assertIsNotNone(self.automation.last_state)

    def test_should_process_no_change(self):
        """Test should_process with no state change."""
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        self.automation.last_state = test_image.copy()
        self.automation.last_action_time = time.time()
        self.assertFalse(self.automation.should_process(test_image))

    def test_should_process_significant_change(self):
        """Test should_process with significant state change."""
        # Create two different images
        image1 = np.zeros((100, 100, 3), dtype=np.uint8)
        image2 = np.ones((100, 100, 3), dtype=np.uint8) * 255
        
        self.automation.last_state = image1
        self.automation.last_action_time = 0
        self.assertTrue(self.automation.should_process(image2))

    def test_execute_action_wait(self):
        """Test execute_action with WAIT action."""
        start_time = time.time()
        self.automation.execute_action("WAIT")
        elapsed = time.time() - start_time
        self.assertGreaterEqual(elapsed, 0.5)

    @patch('utils.keyboard_input.send_key')
    def test_execute_action_movement(self, mock_send_key):
        """Test execute_action with movement actions."""
        actions = ["MOVE_UP", "MOVE_DOWN", "MOVE_LEFT", "MOVE_RIGHT"]
        for action in actions:
            self.automation.execute_action(action)
            self.assertEqual(mock_send_key.call_count, 2)  # Press and release
            mock_send_key.reset_mock()

    @patch('utils.keyboard_input.send_key')
    def test_execute_action_buttons(self, mock_send_key):
        """Test execute_action with button actions."""
        actions = ["PRESS_A", "PRESS_B", "PRESS_START", "PRESS_SELECT"]
        for action in actions:
            self.automation.execute_action(action)
            self.assertEqual(mock_send_key.call_count, 2)  # Press and release
            mock_send_key.reset_mock()

if __name__ == '__main__':
    unittest.main() 