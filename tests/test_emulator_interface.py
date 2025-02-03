"""
Tests for the Emulator Interface

This module contains tests for the EmulatorInterface class.
"""

import unittest
from unittest.mock import Mock, patch
import tempfile
import os
from pathlib import Path

from src.emulator.interface import EmulatorInterface, GameState

class TestEmulatorInterface(unittest.TestCase):
    """Test cases for EmulatorInterface."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.emulator_path = os.path.join(self.temp_dir, "emulator")
        self.rom_path = os.path.join(self.temp_dir, "pokemon.gba")
        
        # Create dummy files
        Path(self.emulator_path).touch()
        Path(self.rom_path).touch()
        
        self.emulator = EmulatorInterface(self.emulator_path, self.rom_path)
    
    def tearDown(self):
        """Clean up test environment."""
        for file in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, file))
        os.rmdir(self.temp_dir)
    
    def test_initialization(self):
        """Test emulator initialization."""
        self.assertEqual(self.emulator.emulator_path, self.emulator_path)
        self.assertEqual(self.emulator.rom_path, self.rom_path)
        self.assertIsInstance(self.emulator.current_state, GameState)
    
    def test_start(self):
        """Test emulator start functionality."""
        # For now, just test that it returns True (default implementation)
        self.assertTrue(self.emulator.start())
    
    def test_read_memory(self):
        """Test memory reading."""
        # Test reading from a valid address
        result = self.emulator.read_memory(0x1000, 4)
        self.assertEqual(result, b'')  # Default implementation returns empty bytes
    
    def test_write_memory(self):
        """Test memory writing."""
        # Test writing to a valid address
        result = self.emulator.write_memory(0x1000, b'test')
        self.assertTrue(result)  # Default implementation returns True
    
    def test_press_button(self):
        """Test button press simulation."""
        with patch('time.sleep') as mock_sleep:
            self.emulator.press_button('A', 0.1)
            mock_sleep.assert_called_once_with(0.1)
    
    def test_get_game_state(self):
        """Test game state retrieval."""
        state = self.emulator.get_game_state()
        self.assertIsInstance(state, GameState)
        self.assertEqual(state.player_x, 0)
        self.assertEqual(state.player_y, 0)
        self.assertFalse(state.in_battle)
    
    def test_save_state(self):
        """Test save state functionality."""
        # Test saving to slot 0
        result = self.emulator.save_state(0)
        self.assertTrue(result)  # Default implementation returns True
        
        # Test saving to different slot
        result = self.emulator.save_state(1)
        self.assertTrue(result)
    
    def test_load_state(self):
        """Test load state functionality."""
        # Test loading from slot 0
        result = self.emulator.load_state(0)
        self.assertTrue(result)  # Default implementation returns True
        
        # Test loading from different slot
        result = self.emulator.load_state(1)
        self.assertTrue(result)
    
    def test_screenshot(self):
        """Test screenshot functionality."""
        # Test without path
        result = self.emulator.screenshot()
        self.assertIsNone(result)  # Default implementation returns None
        
        # Test with path
        test_path = os.path.join(self.temp_dir, "screenshot.png")
        result = self.emulator.screenshot(test_path)
        self.assertEqual(result, test_path)
    
    def test_close(self):
        """Test emulator cleanup."""
        # Just ensure it doesn't raise any exceptions
        try:
            self.emulator.close()
        except Exception as e:
            self.fail(f"close() raised {type(e).__name__} unexpectedly!")

if __name__ == '__main__':
    unittest.main() 