"""
Input handler for emulator controls
"""

import time
import platform
import subprocess
from typing import Dict, Optional
from utils.logger import get_logger

# Get logger for this module
logger = get_logger("pokemon_player")

# Import Quartz on macOS
if platform.system() == "Darwin":
    from Quartz import (
        CGEventCreateKeyboardEvent,
        CGEventPostToPid,
        CGEventSetFlags,
        kCGHIDEventTap,
        kCGEventFlagMaskCommand
    )

# Virtual key codes for macOS
VK_MAP = {
    'up': 126,    # Up arrow
    'down': 125,  # Down arrow
    'left': 123,  # Left arrow
    'right': 124, # Right arrow
    'x': 7,       # X key (for A button)
    'z': 6,       # Z key (for B button)
    'a': 0,       # A key (for L button)
    's': 1,       # S key (for R button)
    'enter': 36,  # Enter/Return (for Start)
    'backspace': 51, # Delete/Backspace (for Select)
}

class InputHandler:
    """Handles keyboard input for the emulator"""
    
    def __init__(self):
        """Initialize input handler"""
        self.emulator_pid = None
        self.focused = False
        
    def get_mgba_pid(self) -> Optional[int]:
        """Get the process ID of mGBA"""
        if platform.system() == "Darwin":
            script = 'tell application "System Events" to get unix id of first process whose name contains "mGBA"'
            try:
                result = subprocess.run(["osascript", "-e", script], 
                                      capture_output=True, text=True, check=True)
                return int(result.stdout.strip())
            except (subprocess.CalledProcessError, ValueError) as e:
                logger.error(f"Could not get mGBA process ID: {e}")
                return None
        return None
        
    def send_key_event(self, key_code: int, key_down: bool):
        """Send a key event to the mGBA process using Quartz"""
        if not self.emulator_pid:
            return
            
        try:
            event = CGEventCreateKeyboardEvent(None, key_code, key_down)
            CGEventPostToPid(self.emulator_pid, event)
            time.sleep(0.01)  # Small delay between key events
        except Exception as e:
            logger.error(f"Error sending key event: {e}")
        
    def press_button(self, button: str, duration: float = 0.1):
        """Press a button for the specified duration.
        
        Args:
            button: Button to press ('up', 'down', 'left', 'right', 'a', 'b', 'l', 'r', 'start', 'select')
            duration: How long to hold the button in seconds
        """
        try:
            # Ensure we have the emulator PID
            if not self.emulator_pid:
                self.emulator_pid = self.get_mgba_pid()
                if not self.emulator_pid:
                    logger.error("Could not find mGBA process")
                    return
                    
            # Get the virtual key code
            key = VK_MAP.get(button.lower())
            if not key:
                logger.error(f"Unknown button: {button}")
                return
                
            logger.debug(f"Pressing {button} (key code {key}) for {duration}s")
            
            # Press and hold the key
            self.send_key_event(key, True)
            time.sleep(duration)
            self.send_key_event(key, False)
            
        except Exception as e:
            logger.error(f"Error pressing button {button}: {e}")
            # Make sure to release the key
            try:
                if key:
                    self.send_key_event(key, False)
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
            # Ensure we have the emulator PID
            if not self.emulator_pid:
                self.emulator_pid = self.get_mgba_pid()
                if not self.emulator_pid:
                    logger.error("Could not find mGBA process")
                    return
                    
            # Get virtual key codes
            keys = []
            for button in buttons:
                key = VK_MAP.get(button.lower())
                if key:
                    keys.append(key)
                else:
                    logger.error(f"Unknown button: {button}")
                    
            if not keys:
                return
                
            logger.debug(f"Pressing {buttons} (key codes {keys}) for {duration}s")
            
            # Press all keys
            for key in keys:
                self.send_key_event(key, True)
                
            time.sleep(duration)
            
            # Release all keys
            for key in reversed(keys):
                self.send_key_event(key, False)
                
        except Exception as e:
            logger.error(f"Error pressing buttons {buttons}: {e}")
            # Make sure to release all keys
            try:
                for key in keys:
                    self.send_key_event(key, False)
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
            # Get the emulator PID if we don't have it
            if not self.emulator_pid:
                self.emulator_pid = self.get_mgba_pid()
                if not self.emulator_pid:
                    logger.error("Could not find mGBA process")
                    return False
            
            if platform.system() == "Darwin":
                # On macOS, use AppleScript to focus window
                script = '''
                tell application "mGBA"
                    activate
                end tell
                '''
                subprocess.run(['osascript', '-e', script], check=True)
                
                # Give window time to focus
                time.sleep(0.5)
                return True
                
            return False
            
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