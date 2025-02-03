import os
import subprocess
import time
import logging
import json
import pyautogui  # For keyboard simulation
import numpy as np
from PIL import Image, ImageGrab
from enum import Enum
from typing import Optional, Tuple, Dict, Any, List, Union

# Configure PyAutoGUI to be safe
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1  # Add small delay between actions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Button(Enum):
    """Enum for GBA buttons and their keyboard mappings."""
    A = "x"  # Default mGBA mapping
    B = "z"
    START = "enter"
    SELECT = "backspace"
    RIGHT = "right"
    LEFT = "left"
    UP = "up"
    DOWN = "down"
    R = "s"
    L = "a"

class EmulatorInterface:
    """Interface for communicating with the mGBA emulator.
    
    This class provides methods to:
    - Start and stop the emulator
    - Simulate button presses using keyboard input
    - Capture screenshots
    - Save and load states
    """
    
    def __init__(self, rom_path: str, emulator_path: Optional[str] = None):
        """Initialize the EmulatorInterface.
        
        Args:
            rom_path: Path to the Pokemon ROM file
            emulator_path: Optional path to mGBA executable. If not provided,
                         will try to find it in standard locations.
        """
        self.rom_path = os.path.abspath(rom_path)
        if not os.path.exists(self.rom_path):
            raise FileNotFoundError(f"ROM file not found: {self.rom_path}")
            
        # Find mGBA executable
        self.emulator_path = emulator_path or self._find_mgba()
        if not os.path.exists(self.emulator_path):
            raise FileNotFoundError(f"mGBA executable not found: {self.emulator_path}")
            
        self.process: Optional[subprocess.Popen] = None
        self.window_title = f"mGBA - {os.path.basename(self.rom_path)}"
        logger.info(f"Initialized EmulatorInterface with ROM: {self.rom_path}")
        logger.info(f"Using emulator at: {self.emulator_path}")
        
    def _find_mgba(self) -> str:
        """Find the mGBA executable in standard locations."""
        # Common locations for mGBA
        possible_locations = [
            "/usr/local/bin/mgba-qt",
            "/usr/local/Cellar/mgba/0.10.4/bin/mGBA",
            # Add more locations as needed
        ]
        
        for location in possible_locations:
            if os.path.exists(location):
                return location
                
        raise FileNotFoundError("Could not find mGBA executable in standard locations")
        
    def start(self) -> None:
        """Start the emulator with the ROM file."""
        if self.process is not None:
            logger.warning("Emulator is already running")
            return
            
        try:
            logger.info("Starting emulator...")
            self.process = subprocess.Popen(
                [self.emulator_path, self.rom_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=1,
                universal_newlines=True
            )
            time.sleep(2)  # Give the emulator time to start
            
            # Focus the window
            try:
                window = pyautogui.getWindowsWithTitle(self.window_title)[0]
                window.activate()
            except Exception as e:
                logger.warning(f"Could not focus emulator window: {e}")
                
            logger.info("Emulator started successfully")
        except Exception as e:
            logger.error(f"Failed to start emulator: {e}")
            raise
            
    def stop(self) -> None:
        """Stop the emulator."""
        if self.process is None:
            logger.warning("Emulator is not running")
            return
            
        try:
            logger.info("Stopping emulator...")
            # Close streams first
            if self.process.stdout:
                self.process.stdout.close()
            if self.process.stderr:
                self.process.stderr.close()
                
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("Emulator did not terminate gracefully, forcing...")
                self.process.kill()
                self.process.wait()
                
            self.process = None
            logger.info("Emulator stopped successfully")
        except Exception as e:
            logger.error(f"Failed to stop emulator: {e}")
            raise
            
    def is_running(self) -> bool:
        """Check if the emulator is running."""
        return self.process is not None and self.process.poll() is None
        
    def press_button(self, button: Union[Button, str], duration: float = 0.1) -> None:
        """Press and hold a button for the specified duration.
        
        Args:
            button: The button to press (can be Button enum or string)
            duration: How long to hold the button in seconds
        """
        if not self.is_running():
            logger.error("Cannot press button: emulator is not running")
            return
            
        if isinstance(button, str):
            try:
                button = Button[button.upper()]
            except KeyError:
                logger.error(f"Invalid button: {button}")
                return
                
        try:
            logger.debug(f"Pressing button: {button.value}")
            pyautogui.keyDown(button.value)
            time.sleep(duration)
            pyautogui.keyUp(button.value)
            logger.debug(f"Released button: {button.value}")
        except Exception as e:
            logger.error(f"Failed to press button {button.value}: {e}")
            raise
            
    def press_buttons(self, buttons: List[Union[Button, str]], duration: float = 0.1) -> None:
        """Press multiple buttons simultaneously.
        
        Args:
            buttons: List of buttons to press
            duration: How long to hold the buttons in seconds
        """
        if not self.is_running():
            logger.error("Cannot press buttons: emulator is not running")
            return
            
        button_enums = []
        for button in buttons:
            if isinstance(button, str):
                try:
                    button_enums.append(Button[button.upper()])
                except KeyError:
                    logger.error(f"Invalid button: {button}")
                    return
            else:
                button_enums.append(button)
                
        try:
            logger.debug(f"Pressing buttons: {[b.value for b in button_enums]}")
            # Press all buttons
            for button in button_enums:
                pyautogui.keyDown(button.value)
            time.sleep(duration)
            # Release all buttons
            for button in button_enums:
                pyautogui.keyUp(button.value)
            logger.debug(f"Released buttons: {[b.value for b in button_enums]}")
        except Exception as e:
            logger.error(f"Failed to press buttons: {e}")
            raise
            
    def press_sequence(self, sequence: List[Tuple[Union[Button, str], float]]) -> None:
        """Press a sequence of buttons with specified durations.
        
        Args:
            sequence: List of (button, duration) tuples
        """
        for button, duration in sequence:
            self.press_button(button, duration)
            
    def capture_screen(self, region: Optional[Tuple[int, int, int, int]] = None) -> Image.Image:
        """Capture the emulator screen.
        
        Args:
            region: Optional (left, top, width, height) tuple for partial capture
            
        Returns:
            PIL Image of the captured screen
        """
        try:
            # Find emulator window
            window = pyautogui.getWindowsWithTitle(self.window_title)[0]
            
            if region is None:
                # Capture entire window
                screenshot = pyautogui.screenshot(region=(
                    window.left,
                    window.top,
                    window.width,
                    window.height
                ))
            else:
                # Capture specified region relative to window
                left, top, width, height = region
                screenshot = pyautogui.screenshot(region=(
                    window.left + left,
                    window.top + top,
                    width,
                    height
                ))
                
            return screenshot
        except Exception as e:
            logger.error(f"Failed to capture screen: {e}")
            raise
            
    def save_state(self, slot: int = 0) -> None:
        """Save the current state to a slot.
        
        Args:
            slot: Save state slot number (0-9)
        """
        if not (0 <= slot <= 9):
            logger.error("Save state slot must be between 0 and 9")
            return
            
        try:
            # Press Shift + F1-F10 for save states
            key = f"f{slot + 1}"
            pyautogui.hotkey("shift", key)
            logger.info(f"Saved state to slot {slot}")
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
            raise
            
    def load_state(self, slot: int = 0) -> None:
        """Load a state from a slot.
        
        Args:
            slot: Save state slot number (0-9)
        """
        if not (0 <= slot <= 9):
            logger.error("Save state slot must be between 0 and 9")
            return
            
        try:
            # Press F1-F10 for load states
            key = f"f{slot + 1}"
            pyautogui.press(key)
            logger.info(f"Loaded state from slot {slot}")
        except Exception as e:
            logger.error(f"Failed to load state: {e}")
            raise
            
    # Common button combinations
    def press_a(self, duration: float = 0.1) -> None:
        """Press the A button."""
        self.press_button(Button.A, duration)
        
    def press_b(self, duration: float = 0.1) -> None:
        """Press the B button."""
        self.press_button(Button.B, duration)
        
    def press_start(self, duration: float = 0.1) -> None:
        """Press the START button."""
        self.press_button(Button.START, duration)
        
    def press_select(self, duration: float = 0.1) -> None:
        """Press the SELECT button."""
        self.press_button(Button.SELECT, duration)
        
    def move(self, direction: Union[Button, str], duration: float = 0.1) -> None:
        """Move in a direction (UP, DOWN, LEFT, RIGHT).
        
        Args:
            direction: The direction to move in
            duration: How long to hold the direction
        """
        if isinstance(direction, str):
            direction = direction.upper()
            if direction not in ["UP", "DOWN", "LEFT", "RIGHT"]:
                logger.error(f"Invalid direction: {direction}")
                return
            direction = Button[direction]
            
        self.press_button(direction, duration) 