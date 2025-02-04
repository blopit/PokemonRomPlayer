"""
Tests for the game automation loop.
"""

import unittest
import os
import tempfile
import time
import cv2
import numpy as np
from unittest.mock import patch, MagicMock

# Adjust sys.path to import our module
import sys
sys.path.insert(0, os.path.abspath('src'))

from automation.game_loop import GameLoop
from emulator.game_state import GameState, GameMode, BattleState

class TestGameLoop(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        # Create a fake ROM file in a temporary directory
        self.temp_rom = tempfile.NamedTemporaryFile(delete=False, suffix='.gba')
        self.temp_rom.write(b'dummy data')
        self.temp_rom.close()
        self.rom_path = self.temp_rom.name

        # Instantiate the GameLoop
        self.loop = GameLoop(self.rom_path)

    def tearDown(self):
        """Clean up test fixtures."""
        os.remove(self.rom_path)
        # Clean up screenshots directory if created
        screenshots_dir = os.path.join(os.getcwd(), "screenshots")
        if os.path.exists(screenshots_dir):
            for f in os.listdir(screenshots_dir):
                os.remove(os.path.join(screenshots_dir, f))

    @patch('automation.game_loop.query_llm')
    @patch('automation.game_loop.EmulatorInterface')
    def test_process_state(self, MockEmulatorInterface, mock_query_llm):
        """Test processing of game state."""
        # Create a fake screen (numpy array)
        fake_image = np.zeros((100, 100, 3), dtype=np.uint8)

        # Ensure screenshots directory exists and simulate saving a screenshot
        screenshots_dir = os.path.join(os.getcwd(), "screenshots")
        os.makedirs(screenshots_dir, exist_ok=True)
        fake_screenshot_path = os.path.join(screenshots_dir, "fake.png")
        cv2.imwrite(fake_screenshot_path, fake_image)

        # Configure the mock for query_llm to return a valid Python list string
        mock_query_llm.return_value = '[{"action": "press_button", "button": "a", "duration": 0.1}, {"action": "wait", "duration": 1.0}]'

        # Patch the get_emulator_screenshot_from_hotkey method to return our fake image
        self.loop.emulator = MagicMock()
        self.loop.emulator.get_emulator_screenshot_from_hotkey.return_value = fake_image

        actions = self.loop.process_state(fake_image)
        self.assertIsInstance(actions, list)
        self.assertEqual(actions[0]['action'], 'press_button')
        self.assertEqual(actions[0]['button'], 'a')
        self.assertEqual(actions[0]['duration'], 0.1)

    @patch('automation.game_loop.query_llm')
    @patch('automation.game_loop.EmulatorInterface')
    def test_process_state_invalid_llm_response(self, MockEmulatorInterface, mock_query_llm):
        """Test handling of invalid LLM responses."""
        fake_image = np.zeros((100, 100, 3), dtype=np.uint8)
        
        # Test with invalid JSON response
        mock_query_llm.return_value = 'invalid json'
        actions = self.loop.process_state(fake_image)
        self.assertEqual(actions, [])  # Should return empty list on error
        
        # Test with valid JSON but wrong format
        mock_query_llm.return_value = '{"action": "press_button"}'  # Not a list
        actions = self.loop.process_state(fake_image)
        self.assertEqual(actions, [])
        
        # Test with empty response
        mock_query_llm.return_value = ''
        actions = self.loop.process_state(fake_image)
        self.assertEqual(actions, [])

    @patch('automation.game_loop.query_llm')
    @patch('automation.game_loop.EmulatorInterface')
    def test_process_state_missing_fields(self, MockEmulatorInterface, mock_query_llm):
        """Test handling of responses with missing fields."""
        fake_image = np.zeros((100, 100, 3), dtype=np.uint8)
        
        # Missing duration field
        mock_query_llm.return_value = '[{"action": "press_button", "button": "a"}]'
        actions = self.loop.process_state(fake_image)
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0].get('duration', 0.1), 0.1)  # Should use default duration
        
        # Missing button field for press_button action
        mock_query_llm.return_value = '[{"action": "press_button", "duration": 0.1}]'
        actions = self.loop.process_state(fake_image)
        self.assertEqual(actions, [])  # Should ignore invalid action

    @patch('automation.game_loop.query_llm')
    @patch('automation.game_loop.EmulatorInterface')
    def test_execute_action(self, MockEmulatorInterface, mock_query_llm):
        """Test action execution."""
        # Create a fake emulator interface with a mocked send_input method
        fake_emulator = MagicMock()
        fake_emulator.send_input = MagicMock(return_value=True)
        self.loop.emulator = fake_emulator

        # Test press_button action
        action = {"action": "press_button", "button": "a", "duration": 0.2}
        self.loop.execute_action(action)
        fake_emulator.send_input.assert_called_with("a", 0.2)

        # Test wait action by checking the time elapsed
        start_time = time.time()
        self.loop.execute_action({"action": "wait", "duration": 0.5})
        elapsed = time.time() - start_time
        self.assertTrue(elapsed >= 0.5)

    @patch('automation.game_loop.query_llm')
    @patch('automation.game_loop.EmulatorInterface')
    def test_execute_action_error_handling(self, MockEmulatorInterface, mock_query_llm):
        """Test error handling in execute_action."""
        fake_emulator = MagicMock()
        fake_emulator.send_input = MagicMock(side_effect=Exception("Failed to send input"))
        self.loop.emulator = fake_emulator
        
        # Test handling of send_input failure
        action = {"action": "press_button", "button": "a", "duration": 0.1}
        self.loop.execute_action(action)  # Should not raise exception
        
        # Test with invalid action type
        action = {"action": "invalid_action", "duration": 0.1}
        self.loop.execute_action(action)  # Should not raise exception
        
        # Test with missing fields
        action = {"action": "press_button"}  # Missing button and duration
        self.loop.execute_action(action)  # Should not raise exception

    @patch('automation.game_loop.query_llm')
    @patch('automation.game_loop.EmulatorInterface')
    def test_start_stop(self, MockEmulatorInterface, mock_query_llm):
        """Test emulator start and stop functionality."""
        # Mock the emulator interface
        mock_emulator = MagicMock()
        MockEmulatorInterface.return_value = mock_emulator
        
        # Create a new game loop instance with the mock
        loop = GameLoop(self.rom_path)
        
        # Start the loop but interrupt it immediately
        def fake_get_screenshot():
            raise KeyboardInterrupt()
        
        mock_emulator.get_emulator_screenshot_from_hotkey = fake_get_screenshot
        
        # Run the loop
        loop.start()
        
        # Verify start and stop were called
        mock_emulator.start.assert_called_once()
        mock_emulator.stop.assert_called_once()

    @patch('automation.game_loop.query_llm')
    @patch('automation.game_loop.EmulatorInterface')
    def test_multiple_actions(self, MockEmulatorInterface, mock_query_llm):
        """Test handling of multiple actions in sequence."""
        fake_emulator = MagicMock()
        self.loop.emulator = fake_emulator
        
        # Test sequence of actions
        actions = [
            {"action": "press_button", "button": "up", "duration": 0.1},
            {"action": "wait", "duration": 0.2},
            {"action": "press_button", "button": "a", "duration": 0.1}
        ]
        
        for action in actions:
            self.loop.execute_action(action)
        
        # Verify all button presses were called
        self.assertEqual(fake_emulator.send_input.call_count, 2)
        
        # Verify the calls were made with correct arguments
        fake_emulator.send_input.assert_any_call("up", 0.1)
        fake_emulator.send_input.assert_any_call("a", 0.1)

if __name__ == '__main__':
    unittest.main() 