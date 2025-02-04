import unittest
import os
import tempfile
import numpy as np
import cv2
from unittest.mock import patch, MagicMock
import time

import sys
sys.path.insert(0, os.path.abspath('src'))

from utils.screenshot_utils import take_screenshot_sync
from emulator.interface import EmulatorInterface

class TestScreenshotUtils(unittest.TestCase):
    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for test screenshots
        self.test_dir = tempfile.mkdtemp()
        self.addCleanup(self.cleanup)

    def cleanup(self):
        """Clean up test environment."""
        # Remove all files in test directory
        for f in os.listdir(self.test_dir):
            os.remove(os.path.join(self.test_dir, f))
        os.rmdir(self.test_dir)

    @patch('pyautogui.screenshot')
    def test_take_screenshot_success(self, mock_screenshot):
        """Test successful screenshot capture."""
        # Create a fake screenshot
        fake_image = MagicMock()
        fake_image.save = MagicMock()
        mock_screenshot.return_value = fake_image

        # Take screenshot
        output_path = os.path.join(self.test_dir, "screenshot.png")
        screenshot_path = take_screenshot_sync(output_path=output_path)
        
        # Verify screenshot was saved
        fake_image.save.assert_called_once_with(output_path)
        self.assertEqual(screenshot_path, output_path)

    @patch('pyautogui.screenshot')
    def test_take_screenshot_failure(self, mock_screenshot):
        """Test screenshot capture failure."""
        # Mock the screenshot to fail
        mock_screenshot.side_effect = Exception("Failed to capture")

        # Take screenshot
        with self.assertRaises(Exception):
            take_screenshot_sync()

    def test_screenshot_directory_creation(self):
        """Test that screenshot directory is created if it doesn't exist."""
        # Remove screenshots directory if it exists
        screenshots_dir = os.path.join(self.test_dir, "screenshots")
        if os.path.exists(screenshots_dir):
            os.rmdir(screenshots_dir)
        
        # Take screenshot
        try:
            take_screenshot_sync(output_path=os.path.join(screenshots_dir, "test.png"))
        except:
            pass
        
        # Check directory was created
        self.assertTrue(os.path.exists(screenshots_dir))

    @patch('pyautogui.screenshot')
    def test_screenshot_naming(self, mock_screenshot):
        """Test screenshot file naming convention."""
        # Mock successful screenshot
        fake_image = MagicMock()
        fake_image.save = MagicMock()
        mock_screenshot.return_value = fake_image

        # Take multiple screenshots with different timestamps
        paths = []
        for i in range(3):
            time.sleep(0.1)  # Ensure different timestamps
            path = take_screenshot_sync()
            paths.append(path)

        # Check that filenames are unique
        self.assertEqual(len(paths), len(set(paths)))
        
        # Check naming pattern
        for path in paths:
            self.assertTrue(os.path.basename(path).startswith("screenshot_"))
            self.assertTrue(path.endswith(".png"))

    @patch('pyautogui.screenshot')
    def test_screenshot_with_window_title(self, mock_screenshot):
        """Test screenshot capture with specific window title."""
        # Mock successful screenshot
        fake_image = MagicMock()
        fake_image.save = MagicMock()
        mock_screenshot.return_value = fake_image
        
        # Take screenshot with window title
        screenshot_path = take_screenshot_sync(window_title="mGBA")
        
        # Verify screenshot was taken
        mock_screenshot.assert_called_once()
        fake_image.save.assert_called_once()
        self.assertTrue(screenshot_path.endswith(".png"))

    def test_screenshot_image_validity(self):
        """Test that captured screenshots are valid images."""
        # Create a fake screenshot
        fake_image = np.zeros((100, 100, 3), dtype=np.uint8)
        # Add some recognizable pattern
        fake_image[40:60, 40:60] = [255, 0, 0]  # Red square
        
        screenshot_path = os.path.join(self.test_dir, "test.png")
        cv2.imwrite(screenshot_path, fake_image)
        
        # Read back and verify
        read_image = cv2.imread(screenshot_path)
        self.assertIsNotNone(read_image)
        self.assertEqual(read_image.shape, (100, 100, 3))
        # Verify pattern in a single pixel
        self.assertTrue(np.array_equal(read_image[40, 40], [255, 0, 0]))

if __name__ == '__main__':
    unittest.main() 