"""
Input handler for emulator controls
"""

import time
import pyautogui
import platform
import subprocess
from typing import Dict, Optional
from utils.logger import get_logger

# Get logger for this module
logger = get_logger("pokemon_player")

# Key mappings for GBA controls
KEY_MAPPINGS = {
    'up': 'up',
    'down': 'down', 
    'left': 'left',
    'right': 'right',
    'a': 'x',  # A button mapped to X
    'b': 'z',  # B button mapped to Z
    'l': 'a',  # L button mapped to A
    'r': 's',  # R button mapped to S
    'start': 'enter',
    'select': 'backspace'
}

class InputHandler:
    """Handles keyboard input for the emulator"""
    
    def __init__(self):
        """Initialize input handler"""
        # Set up pyautogui
        pyautogui.PAUSE = 0.1  # Add small delay between actions
        pyautogui.FAILSAFE = True
        
    def press_button(self, button: str, duration: float = 0.1):
        """Press a button for the specified duration.
        
        Args:
            button: Button to press ('up', 'down', 'left', 'right', 'a', 'b', 'l', 'r', 'start', 'select')
            duration: How long to hold the button in seconds
        """
        try:
            # Get the mapped key
            key = KEY_MAPPINGS.get(button.lower())
            if not key:
                logger.error(f"Unknown button: {button}")
                return
                
            logger.debug(f"Pressing {button} (mapped to {key}) for {duration}s")
            
            # Press and hold the key
            pyautogui.keyDown(key)
            time.sleep(duration)
            pyautogui.keyUp(key)
            
        except Exception as e:
            logger.error(f"Error pressing button {button}: {e}")
            # Make sure to release the key
            try:
                pyautogui.keyUp(key)
            except:
                pass
            raise
            
    def press_buttons(self, buttons: list, duration: float = 0.1):
        """Press multiple buttons simultaneously.
        
        Args:
            buttons: List of buttons to press
            duration: How long to hold the buttons in seconds
        """
        try:
            # Get mapped keys
            keys = []
            for button in buttons:
                key = KEY_MAPPINGS.get(button.lower())
                if key:
                    keys.append(key)
                else:
                    logger.error(f"Unknown button: {button}")
                    
            if not keys:
                return
                
            logger.debug(f"Pressing {buttons} (mapped to {keys}) for {duration}s")
            
            # Press all keys
            for key in keys:
                pyautogui.keyDown(key)
                
            time.sleep(duration)
            
            # Release all keys
            for key in reversed(keys):
                pyautogui.keyUp(key)
                
        except Exception as e:
            logger.error(f"Error pressing buttons {buttons}: {e}")
            # Make sure to release all keys
            try:
                for key in keys:
                    pyautogui.keyUp(key)
            except:
                pass
            raise
    
    def focus_window(self, window_title: str) -> bool:
        """Focus the emulator window.
        
        Args:
            window_title: Title of the window to focus
            
        Returns:
            True if window was focused successfully
        """
        try:
            if platform.system() == "Darwin":
                # On macOS, use AppleScript to focus window
                script = f'''
                tell application "System Events"
                    tell process "{window_title}"
                        set frontmost to true
                    end tell
                end tell
                '''
                subprocess.run(['osascript', '-e', script], check=True)
            else:
                # On other platforms, use pyautogui's window functions
                windows = pyautogui.getWindowsWithTitle(window_title)
                if not windows:
                    logger.warning(f"Could not find window with title: {window_title}")
                    return False
                windows[0].activate()
            
            # Give window time to focus
            time.sleep(0.5)
            return True
            
        except Exception as e:
            logger.warning(f"Could not focus window: {e}")
            return False
    
    def press_sequence(self, sequence: list[tuple[str, float]]) -> None:
        """Press a sequence of buttons with specified durations.
        
        Args:
            sequence: List of (button, duration) tuples
        """
        for button, duration in sequence:
            self.press_button(button, duration)
    
    def hold_direction(self, direction: str, duration: float) -> None:
        """Hold a direction for a specified duration.
        
        Args:
            direction: Direction to hold ('up', 'down', 'left', 'right')
            duration: How long to hold the direction in seconds
        """
        if direction.lower() not in ['up', 'down', 'left', 'right']:
            logger.warning(f"Invalid direction: {direction}")
            return
        
        self.press_button(direction, duration)
    
    def navigate_menu(self, target_index: int, current_index: int = 0,
                     vertical: bool = True) -> None:
        """Navigate to a specific menu index.
        
        Args:
            target_index: The menu index to navigate to
            current_index: The current menu index (default: 0)
            vertical: Whether the menu is vertical (True) or horizontal (False)
        """
        if target_index == current_index:
            return
        
        steps = target_index - current_index
        direction = 'down' if vertical else 'right'
        opposite = 'up' if vertical else 'left'
        
        # Use the shorter path
        if abs(steps) > 5:
            direction, opposite = opposite, direction
            steps = -steps
        
        for _ in range(abs(steps)):
            self.press_button(direction if steps > 0 else opposite, 0.1)
            time.sleep(0.05)  # Small delay between presses 