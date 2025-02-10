"""
Integration tests for CrewAI tool interfaces.

These tests verify that the screen capture, input simulation, and image processing
tools work correctly and handle various scenarios appropriately.
"""

import os
import time
import pytest
import numpy as np
from PIL import Image
from unittest.mock import Mock, patch

from crew.tools.screen_capture import ScreenCaptureTool, ScreenCaptureConfig
from crew.tools.input_simulator import InputSimulatorTool, InputSimulatorConfig
from crew.tools.image_processor import ImageProcessorTool, ImageProcessorConfig

# Test data directory
TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "test_data")
os.makedirs(TEST_DATA_DIR, exist_ok=True)

@pytest.fixture
def screen_capture_tool():
    """Fixture for screen capture tool."""
    config = ScreenCaptureConfig(
        output_dir=TEST_DATA_DIR,
        target_width=240,
        target_height=160
    )
    return ScreenCaptureTool(config)

@pytest.fixture
def input_simulator_tool():
    """Fixture for input simulator tool."""
    config = InputSimulatorConfig(
        default_press_duration=0.1,
        default_sequence_delay=0.05
    )
    return InputSimulatorTool(config)

@pytest.fixture
def image_processor_tool():
    """Fixture for image processor tool."""
    config = ImageProcessorConfig(
        ocr_lang="eng",
        min_confidence=0.6
    )
    return ImageProcessorTool(config)

# Screen Capture Tool Tests
class TestScreenCaptureTool:
    """Tests for the screen capture tool."""
    
    def test_capture_game_screen(self, screen_capture_tool):
        """Test capturing a game screen."""
        # Capture screen
        screenshot_path = screen_capture_tool.capture_game_screen()
        
        # Verify screenshot was created
        assert screenshot_path is not None
        assert os.path.exists(screenshot_path)
        
        # Verify image dimensions
        img = Image.open(screenshot_path)
        width, height = img.size
        assert width == screen_capture_tool.config.target_width
        assert height == screen_capture_tool.config.target_height
        
    def test_capture_with_invalid_pid(self, screen_capture_tool):
        """Test capturing with an invalid process ID."""
        # Try to capture with invalid PID
        screenshot_path = screen_capture_tool.capture_game_screen(emulator_pid=99999)
        
        # Should fall back to active window capture
        assert screenshot_path is not None
        assert os.path.exists(screenshot_path)
        
    def test_get_latest_capture(self, screen_capture_tool):
        """Test getting the latest screenshot."""
        # Capture multiple screenshots
        paths = []
        for _ in range(3):
            path = screen_capture_tool.capture_game_screen()
            paths.append(path)
            time.sleep(0.1)  # Ensure different timestamps
            
        # Get latest
        latest = screen_capture_tool.get_latest_capture()
        assert latest == paths[-1]

# Input Simulator Tool Tests
class TestInputSimulatorTool:
    """Tests for the input simulator tool."""
    
    def test_press_button(self, input_simulator_tool):
        """Test pressing a single button."""
        # Mock the input handler
        with patch.object(input_simulator_tool.input_handler, 'press_button') as mock_press:
            # Press a button
            success = input_simulator_tool.press_button('a', duration=0.1)
            
            # Verify
            assert success
            mock_press.assert_called_once_with('x', 0.1)  # 'a' maps to 'x'
            
    def test_press_sequence(self, input_simulator_tool):
        """Test pressing a sequence of buttons."""
        # Mock the input handler
        with patch.object(input_simulator_tool.input_handler, 'press_button') as mock_press:
            # Press sequence
            sequence = [('up', 0.1), ('a', 0.2)]
            success = input_simulator_tool.press_sequence(sequence)
            
            # Verify
            assert success
            assert mock_press.call_count == 2
            mock_press.assert_any_call('up', 0.1)
            mock_press.assert_any_call('x', 0.2)  # 'a' maps to 'x'
            
    def test_navigate_menu(self, input_simulator_tool):
        """Test menu navigation."""
        # Mock the input handler
        with patch.object(input_simulator_tool.input_handler, 'navigate_menu') as mock_nav:
            # Navigate menu
            success = input_simulator_tool.navigate_menu(
                target_index=2,
                current_index=0,
                vertical=True
            )
            
            # Verify
            assert success
            mock_nav.assert_called_once_with(
                target_index=2,
                current_index=0,
                vertical=True
            )

# Image Processor Tool Tests
class TestImageProcessorTool:
    """Tests for the image processor tool."""
    
    def test_extract_text(self, image_processor_tool):
        """Test extracting text from an image."""
        # Create test image with text
        img = np.zeros((160, 240, 3), dtype=np.uint8)
        # TODO: Add test text to image
        
        # Extract text
        text = image_processor_tool.extract_text(img)
        assert isinstance(text, str)
        
    def test_detect_battle_state(self, image_processor_tool):
        """Test detecting battle state from an image."""
        # Create test battle screen
        img = np.zeros((160, 240, 3), dtype=np.uint8)
        # TODO: Add battle UI elements
        
        # Detect battle state
        battle_info = image_processor_tool.detect_battle_state(img)
        assert isinstance(battle_info, dict)
        assert "menu_text" in battle_info
        assert "moves" in battle_info
        
    def test_detect_dialog(self, image_processor_tool):
        """Test detecting dialog text."""
        # Create test dialog screen
        img = np.zeros((160, 240, 3), dtype=np.uint8)
        # TODO: Add dialog text
        
        # Detect dialog
        dialog = image_processor_tool.detect_dialog(img)
        assert dialog is None  # No text in test image
        
    def test_analyze_game_state(self, image_processor_tool, screen_capture_tool):
        """Test analyzing complete game state."""
        # Capture a real screenshot
        screenshot_path = screen_capture_tool.capture_game_screen()
        
        # Analyze state
        state_info = image_processor_tool.analyze_game_state(screenshot_path)
        assert isinstance(state_info, dict)
        assert "battle_state" in state_info
        assert "dialog" in state_info
        assert "timestamp" in state_info

# Error Handling Tests
class TestToolErrorHandling:
    """Tests for tool error handling."""
    
    def test_screen_capture_retries(self, screen_capture_tool):
        """Test screen capture retry logic."""
        with patch('cv2.imread', side_effect=[None, None, np.zeros((160, 240, 3))]):
            screenshot_path = screen_capture_tool.capture_game_screen()
            assert screenshot_path is not None
            
    def test_input_simulator_focus_failure(self, input_simulator_tool):
        """Test input simulator handling focus failure."""
        with patch.object(input_simulator_tool.input_handler, 'focus_window', return_value=False):
            success = input_simulator_tool.press_button('a')
            assert not success
            
    def test_image_processor_invalid_image(self, image_processor_tool):
        """Test image processor handling invalid image."""
        result = image_processor_tool.analyze_game_state("nonexistent.png")
        assert result == {}
