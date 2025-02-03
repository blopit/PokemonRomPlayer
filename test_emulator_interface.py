import unittest
import os
import time
from emulator_interface import EmulatorInterface, Button

class TestEmulatorInterface(unittest.TestCase):
    """Test cases for the EmulatorInterface class."""
    
    def setUp(self):
        """Set up test environment before each test."""
        self.rom_path = "moemon star em v1.1c.gba"
        self.interface = EmulatorInterface(self.rom_path)
        
    def tearDown(self):
        """Clean up after each test."""
        if self.interface.is_running():
            self.interface.stop()
            
    def test_initialization(self):
        """Test that the interface initializes correctly."""
        self.assertIsNotNone(self.interface)
        self.assertEqual(self.interface.rom_path, os.path.abspath(self.rom_path))
        self.assertIsNotNone(self.interface.emulator_path)
        self.assertTrue(os.path.exists(self.interface.emulator_path))
        
    def test_start_stop(self):
        """Test starting and stopping the emulator."""
        # Test starting
        self.interface.start()
        self.assertTrue(self.interface.is_running())
        time.sleep(2)  # Give it a moment to fully start
        
        # Test stopping
        self.interface.stop()
        self.assertFalse(self.interface.is_running())
        
    def test_invalid_rom_path(self):
        """Test that invalid ROM path raises an error."""
        with self.assertRaises(FileNotFoundError):
            EmulatorInterface("nonexistent.gba")
            
    def test_button_press(self):
        """Test button press functionality."""
        self.interface.start()
        
        # Test single button press
        start_time = time.time()
        self.interface.press_button(Button.A)
        duration = time.time() - start_time
        self.assertGreaterEqual(duration, 0.1)  # Default duration
        
        # Test button press with custom duration
        start_time = time.time()
        self.interface.press_button(Button.B, duration=0.2)
        duration = time.time() - start_time
        self.assertGreaterEqual(duration, 0.2)
        
        # Test button press with string input
        self.interface.press_button("START")
        
        # Test invalid button
        self.interface.press_button("INVALID")  # Should log error but not raise exception
            
    def test_multi_button_press(self):
        """Test pressing multiple buttons simultaneously."""
        self.interface.start()
        
        # Test multiple buttons
        start_time = time.time()
        self.interface.press_buttons([Button.A, Button.B])
        duration = time.time() - start_time
        self.assertGreaterEqual(duration, 0.1)  # Default duration
        
        # Test with string input
        self.interface.press_buttons(["UP", "A"])
        
        # Test with mixed input
        self.interface.press_buttons([Button.DOWN, "B"])
        
        # Test with invalid button
        self.interface.press_buttons([Button.A, "INVALID"])  # Should log error but not execute
            
    def test_button_sequence(self):
        """Test pressing a sequence of buttons."""
        self.interface.start()
        
        sequence = [
            (Button.A, 0.1),
            (Button.UP, 0.2),
            (Button.B, 0.1)
        ]
        
        start_time = time.time()
        self.interface.press_sequence(sequence)
        duration = time.time() - start_time
        self.assertGreaterEqual(duration, 0.4)  # Sum of all durations
            
    def test_movement(self):
        """Test movement functionality."""
        self.interface.start()
        
        # Test all directions
        for direction in ["UP", "DOWN", "LEFT", "RIGHT"]:
            self.interface.move(direction)
            
        # Test with Button enum
        self.interface.move(Button.UP)
        
        # Test invalid direction
        self.interface.move("INVALID")  # Should log error but not raise exception
            
if __name__ == '__main__':
    unittest.main() 