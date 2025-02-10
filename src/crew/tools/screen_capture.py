"""
Screen Capture Tool

This module provides a CrewAI tool interface for capturing and processing
game screenshots.
"""

import os
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass
from utils.logger import get_logger
from utils.screenshot import capture_window, crop_to_ratio, take_screenshot, get_latest_screenshot
import cv2

logger = get_logger("crew")

@dataclass
class ScreenCaptureConfig:
    """Configuration for screen capture."""
    output_dir: str = "screenshots"
    target_width: int = 240  # GBA screen width
    target_height: int = 160  # GBA screen height
    max_retries: int = 3
    retry_delay: float = 0.5

class ScreenCaptureTool:
    """Tool for capturing and processing game screenshots."""
    
    def __init__(self, config: Optional[ScreenCaptureConfig] = None):
        """Initialize the screen capture tool.
        
        Args:
            config: Tool configuration
        """
        self.config = config or ScreenCaptureConfig()
        
        # Ensure output directory exists
        os.makedirs(self.config.output_dir, exist_ok=True)
        logger.info(f"Initialized screen capture tool with output dir: {self.config.output_dir}")
        
    def capture_game_screen(self, emulator_pid: Optional[int] = None) -> Optional[str]:
        """Capture the current game screen.
        
        Args:
            emulator_pid: Optional process ID of the emulator
            
        Returns:
            Path to the captured screenshot if successful, None otherwise
        """
        try:
            # Try to capture with retries
            for attempt in range(self.config.max_retries):
                try:
                    # Capture window
                    img = capture_window(pid=emulator_pid, max_retries=1)
                    
                    # Crop to GBA aspect ratio
                    img = crop_to_ratio(
                        img,
                        self.config.target_width,
                        self.config.target_height
                    )
                    
                    # Save screenshot with timestamp
                    timestamp = time.strftime("%Y%m%d-%H%M%S")
                    output_path = os.path.join(
                        self.config.output_dir,
                        f"screenshot_{timestamp}.png"
                    )
                    
                    # Save processed image
                    cv2.imwrite(output_path, img)
                    logger.info(f"Saved processed screenshot to {output_path}")
                    
                    return output_path
                    
                except Exception as e:
                    logger.warning(f"Screenshot attempt {attempt + 1} failed: {e}")
                    if attempt < self.config.max_retries - 1:
                        time.sleep(self.config.retry_delay)
                        
            logger.error("All screenshot attempts failed")
            return None
            
        except Exception as e:
            logger.error(f"Error in screen capture: {e}")
            return None
            
    def get_latest_capture(self) -> Optional[str]:
        """Get the path to the most recent screenshot.
        
        Returns:
            Path to the latest screenshot if available, None otherwise
        """
        return get_latest_screenshot(self.config.output_dir)
        
    def process_screenshot(self, screenshot_path: str) -> Optional[Dict[str, Any]]:
        """Process a screenshot to extract game state information.
        
        Args:
            screenshot_path: Path to the screenshot to process
            
        Returns:
            Dictionary containing extracted information if successful, None otherwise
        """
        try:
            # TODO: Implement OCR and game state extraction
            # For now, just return basic file info
            if not os.path.exists(screenshot_path):
                logger.error(f"Screenshot not found: {screenshot_path}")
                return None
                
            return {
                "path": screenshot_path,
                "timestamp": os.path.getctime(screenshot_path),
                "size": os.path.getsize(screenshot_path)
            }
            
        except Exception as e:
            logger.error(f"Error processing screenshot: {e}")
            return None
            
    def cleanup_old_screenshots(self, max_age_hours: int = 24) -> None:
        """Clean up screenshots older than the specified age.
        
        Args:
            max_age_hours: Maximum age of screenshots to keep in hours
        """
        try:
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            for filename in os.listdir(self.config.output_dir):
                if not filename.startswith("screenshot_"):
                    continue
                    
                filepath = os.path.join(self.config.output_dir, filename)
                file_age = current_time - os.path.getctime(filepath)
                
                if file_age > max_age_seconds:
                    try:
                        os.remove(filepath)
                        logger.debug(f"Removed old screenshot: {filename}")
                    except Exception as e:
                        logger.warning(f"Could not remove {filename}: {e}")
                        
        except Exception as e:
            logger.error(f"Error cleaning up screenshots: {e}")
            
    def __str__(self) -> str:
        """Get string representation of the tool.
        
        Returns:
            Tool description string
        """
        return "Screen Capture Tool - Captures and processes game screenshots" 