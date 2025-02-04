"""
Screen analyzer for Pokemon game state detection
"""

import cv2
import numpy as np
import pyautogui
from PIL import Image
import platform
import subprocess
import tempfile
import os
from utils.logger import get_logger
from typing import Dict

logger = get_logger("pokemon_player")

class ScreenAnalyzer:
    """Analyzes game screen to detect state and extract information"""
    
    def __init__(self, pid: int = None):
        """Initialize screen analyzer
        
        Args:
            pid: Process ID of mGBA window (optional)
        """
        self.pid = pid
        self.is_macos = platform.system() == "Darwin"
        
        # Expected GBA screen dimensions (scaled)
        self.expected_width = 480  
        self.expected_height = 320
        
    def analyze_screen(self, screen: np.ndarray) -> Dict:
        """Analyze the current screen state to determine game context.
        
        Args:
            screen: Processed screenshot array
            
        Returns:
            Dictionary containing screen analysis results
        """
        try:
            # Initialize state dictionary
            state = {
                "in_battle": False,
                "menu_state": None,
                "has_dialog": False,
                "text_content": None,
                "screen_type": "unknown"
            }
            
            # Detect battle state
            state["in_battle"] = self.detect_battle_state(screen)
            
            # Detect menu state if not in battle
            if not state["in_battle"]:
                state["menu_state"] = self.detect_menu_state(screen)
                
            # Check for dialog box
            state["has_dialog"] = self.detect_dialog_box(screen)
            
            # Extract text if dialog box present
            if state["has_dialog"]:
                state["text_content"] = self.extract_text(screen)
                
            # Determine screen type
            if state["in_battle"]:
                state["screen_type"] = "battle"
            elif state["menu_state"]:
                state["screen_type"] = "menu"
            elif state["has_dialog"]:
                state["screen_type"] = "dialog"
            else:
                state["screen_type"] = "overworld"
                
            return state
            
        except Exception as e:
            logger.error(f"Error analyzing screen: {e}")
            return {
                "error": str(e),
                "screen_type": "error"
            }
            
    def get_screen_state(self) -> np.ndarray:
        """Capture and process current game screen state.
        
        Returns:
            Numpy array containing the processed screenshot
        """
        try:
            # Create temp file for screenshot
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                temp_path = tmp.name
                
            if self.is_macos:
                # Focus mGBA window
                script = """
                tell application "System Events"
                    set mgbaProcess to first process whose unix id is %d
                    set frontmost of mgbaProcess to true
                end tell
                """ % self.pid
                
                subprocess.run(['osascript', '-e', script], check=True)
                
                # Take screenshot of focused window
                subprocess.run(['screencapture', '-w', temp_path], check=True)
                
            else:
                # For other platforms, use pyautogui
                screenshot = pyautogui.screenshot()
                screenshot.save(temp_path)
                
            # Read and process the image
            img = cv2.imread(temp_path)
            if img is None:
                raise Exception("Failed to read screenshot")
                
            # Remove temp file
            os.unlink(temp_path)
            
            # Get image dimensions
            height, width = img.shape[:2]
            logger.debug(f"Screenshot dimensions: {width}x{height}")
            
            # Calculate center crop coordinates
            target_ratio = self.expected_width / self.expected_height
            current_ratio = width / height
            
            if current_ratio > target_ratio:
                # Image is too wide
                new_width = int(height * target_ratio)
                x = (width - new_width) // 2
                y = 0
                w = new_width
                h = height
            else:
                # Image is too tall
                new_height = int(width / target_ratio)
                x = 0
                y = (height - new_height) // 2
                w = width
                h = new_height
                
            # Crop image
            cropped = img[y:y+h, x:x+w]
            
            # Resize to expected dimensions
            resized = cv2.resize(cropped, (self.expected_width, self.expected_height))
            
            logger.debug(f"Processed image to {self.expected_width}x{self.expected_height}")
            return resized
            
        except Exception as e:
            logger.error(f"Error capturing screen: {e}")
            raise
            
    def detect_battle_state(self, screen: np.ndarray) -> bool:
        """Detect if currently in a battle.
        
        Args:
            screen: Processed screenshot array
            
        Returns:
            True if in battle, False otherwise
        """
        # TODO: For now, return False until we implement proper detection
        return False
        
    def detect_menu_state(self, screen: np.ndarray) -> str:
        """Detect current menu state.
        
        Args:
            screen: Processed screenshot array
            
        Returns:
            Menu state string
        """
        # TODO: For now, return None until we implement proper detection
        return None
        
    def detect_dialog_box(self, screen: np.ndarray) -> bool:
        """Detect if dialog box is present.
        
        Args:
            screen: Processed screenshot array
            
        Returns:
            True if dialog box present, False otherwise
        """
        # TODO: For now, return False until we implement proper detection
        return False
        
    def extract_text(self, screen: np.ndarray, region: tuple = None) -> str:
        """Extract text from screen region.
        
        Args:
            screen: Processed screenshot array
            region: Optional tuple of (x,y,w,h) defining region to extract text from
            
        Returns:
            Extracted text string
        """
        # TODO: For now, return None until we implement proper text extraction
        return None 