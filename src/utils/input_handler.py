from typing import Dict, Optional
import pyautogui
import time

class InputHandler:
    """Handles input commands for the emulator."""
    
    # Default key mappings for mGBA
    DEFAULT_KEY_MAPPINGS = {
        'a': 'x',
        'b': 'z',
        'start': 'enter',
        'select': 'backspace',
        'up': 'up',
        'down': 'down',
        'left': 'left',
        'right': 'right',
        'l': 'a',
        'r': 's'
    }
    
    def __init__(self, key_mappings: Optional[Dict[str, str]] = None):
        """Initialize input handler with optional custom key mappings.
        
        Args:
            key_mappings: Optional dictionary mapping GBA buttons to keyboard keys
        """
        self.key_mappings = key_mappings or self.DEFAULT_KEY_MAPPINGS
    
    def press_button(self, button: str, duration: float = 0.1) -> None:
        """Press and hold a button for the specified duration.
        
        Args:
            button: The button to press ('a', 'b', 'start', etc.)
            duration: How long to hold the button in seconds
        """
        if button.lower() not in self.key_mappings:
            raise ValueError(f"Unknown button: {button}")
        
        key = self.key_mappings[button.lower()]
        pyautogui.keyDown(key)
        time.sleep(duration)
        pyautogui.keyUp(key)
    
    def press_buttons(self, buttons: list[str], duration: float = 0.1) -> None:
        """Press multiple buttons simultaneously.
        
        Args:
            buttons: List of buttons to press
            duration: How long to hold the buttons in seconds
        """
        keys = []
        for button in buttons:
            if button.lower() not in self.key_mappings:
                raise ValueError(f"Unknown button: {button}")
            keys.append(self.key_mappings[button.lower()])
        
        for key in keys:
            pyautogui.keyDown(key)
        
        time.sleep(duration)
        
        for key in reversed(keys):
            pyautogui.keyUp(key)
    
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
            raise ValueError(f"Invalid direction: {direction}")
        
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