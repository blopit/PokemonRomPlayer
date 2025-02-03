"""
Emulator Interface Module

This module provides a high-level interface for interacting with the GBA emulator.
It handles memory reading, input simulation, and state management.
"""

import logging
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
import time
import cv2
import numpy as np
import pyautogui
from pathlib import Path
import os
import subprocess

from utils.logger import logger
from utils.input_handler import InputHandler
from utils.screen_analyzer import ScreenAnalyzer
from .game_state import GameState, GameMode

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class GameState:
    """Represents the current state of the game."""
    player_x: int = 0
    player_y: int = 0
    current_map: int = 0
    in_battle: bool = False
    in_menu: bool = False
    current_pokemon: List[Dict] = None
    inventory: Dict = None
    mode: GameMode = GameMode.NORMAL

@dataclass
class SpeedConfig:
    """Configuration for emulator speed control."""
    speed_multiplier: float = 1.0  # Normal speed = 1.0
    use_turbo: bool = False        # Turbo mode (max speed)
    frame_skip: int = 0            # Number of frames to skip (0 = none)

class EmulatorInterface:
    """Interface for interacting with the mGBA emulator."""
    
    # Speed control key mappings
    TURBO_KEY = 'tab'          # Hold for turbo
    SPEED_UP_KEY = 'pageup'    # Increase speed
    SPEED_DOWN_KEY = 'pagedown'  # Decrease speed
    
    def __init__(self, rom_path: str, save_state_dir: Optional[str] = None):
        """Initialize the emulator interface.
        
        Args:
            rom_path: Path to the Pokemon ROM file
            save_state_dir: Optional directory for save states
        """
        self.rom_path = Path(rom_path)
        if not self.rom_path.exists():
            raise FileNotFoundError(f"ROM file not found: {self.rom_path}")
        
        self.save_state_dir = Path(save_state_dir) if save_state_dir else None
        if self.save_state_dir:
            self.save_state_dir.mkdir(parents=True, exist_ok=True)
        
        # Find mGBA executable
        self.emulator_path = self._find_mgba()
        if not os.path.exists(self.emulator_path):
            raise FileNotFoundError(f"mGBA executable not found: {self.emulator_path}")
        
        self.window_title = f"mGBA - {self.rom_path.name}"
        self.process: Optional[subprocess.Popen] = None
        
        # Initialize helpers
        self.input_handler = InputHandler()
        self.screen_analyzer = ScreenAnalyzer()
        
        # Speed control state
        self.speed_config = SpeedConfig()
        self._turbo_active = False
        
        logger.info(f"Initialized EmulatorInterface with ROM: {self.rom_path}")
        logger.info(f"Using emulator at: {self.emulator_path}")
    
    def _find_mgba(self) -> str:
        """Find the mGBA executable in standard locations.
        
        Returns:
            Path to mGBA executable
        """
        # Common locations for mGBA
        possible_locations = [
            "/usr/local/bin/mgba-qt",  # Linux/macOS Homebrew
            "/usr/bin/mgba-qt",        # Linux
            "/Applications/mGBA.app/Contents/MacOS/mGBA",  # macOS
            "C:\\Program Files\\mGBA\\mGBA.exe",  # Windows
            # Add more locations as needed
        ]
        
        for location in possible_locations:
            if os.path.exists(location):
                return location
        
        # Try finding in PATH
        try:
            result = subprocess.run(["which", "mgba-qt"], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        
        raise FileNotFoundError("Could not find mGBA executable in standard locations")
    
    def set_speed(self, multiplier: float) -> None:
        """Set the emulator speed multiplier.
        
        Args:
            multiplier: Speed multiplier (1.0 = normal speed)
        """
        if not self.is_running():
            logger.warning("Cannot set speed: emulator not running")
            return
        
        if multiplier < 1.0:
            logger.warning("Speed multiplier cannot be less than 1.0")
            multiplier = 1.0
        
        # Calculate number of speed up/down presses needed
        current_mult = self.speed_config.speed_multiplier
        steps = int(abs(multiplier - current_mult) / 0.25)  # Each press changes speed by 0.25x
        
        key = self.SPEED_UP_KEY if multiplier > current_mult else self.SPEED_DOWN_KEY
        
        # Apply speed change
        for _ in range(steps):
            pyautogui.press(key)
            time.sleep(0.1)  # Small delay between presses
        
        self.speed_config.speed_multiplier = multiplier
        logger.info(f"Set emulator speed to {multiplier}x")
    
    def set_turbo(self, enabled: bool) -> None:
        """Enable or disable turbo mode.
        
        Args:
            enabled: Whether to enable turbo mode
        """
        if not self.is_running():
            logger.warning("Cannot set turbo: emulator not running")
            return
        
        if enabled == self._turbo_active:
            return
        
        if enabled:
            pyautogui.keyDown(self.TURBO_KEY)
            self._turbo_active = True
            logger.info("Turbo mode enabled")
        else:
            pyautogui.keyUp(self.TURBO_KEY)
            self._turbo_active = False
            logger.info("Turbo mode disabled")
        
        self.speed_config.use_turbo = enabled
    
    def set_frame_skip(self, frames: int) -> None:
        """Set the number of frames to skip.
        
        Args:
            frames: Number of frames to skip (0-9)
        """
        if not self.is_running():
            logger.warning("Cannot set frame skip: emulator not running")
            return
        
        frames = max(0, min(frames, 9))  # Clamp to valid range
        
        # Frame skip is usually bound to number keys 0-9
        pyautogui.press(str(frames))
        
        self.speed_config.frame_skip = frames
        logger.info(f"Set frame skip to {frames}")
    
    def start(self, speed_multiplier: float = 1.0, use_turbo: bool = False, frame_skip: int = 0) -> bool:
        """Start the emulator and load the ROM.
        
        Args:
            speed_multiplier: Initial speed multiplier
            use_turbo: Whether to enable turbo mode
            frame_skip: Number of frames to skip
            
        Returns:
            True if successful, False otherwise
        """
        if self.process is not None:
            logger.warning("Emulator is already running")
            return True
        
        try:
            logger.info("Starting emulator...")
            self.process = subprocess.Popen(
                [self.emulator_path, str(self.rom_path)],
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
            
            # Apply initial speed settings
            if speed_multiplier != 1.0:
                self.set_speed(speed_multiplier)
            if use_turbo:
                self.set_turbo(True)
            if frame_skip > 0:
                self.set_frame_skip(frame_skip)
            
            logger.info("Emulator started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start emulator: {e}")
            return False
    
    def stop(self) -> None:
        """Stop the emulator."""
        if self.process is None:
            logger.warning("Emulator is not running")
            return
        
        try:
            logger.info("Stopping emulator...")
            # Disable turbo if active
            if self._turbo_active:
                self.set_turbo(False)
            
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
        """Check if the emulator is running.
        
        Returns:
            True if emulator is running
        """
        return self.process is not None and self.process.poll() is None
    
    def get_screen_state(self) -> np.ndarray:
        """Capture the current emulator screen state.
        
        Returns:
            numpy.ndarray: RGB image of the current screen
        """
        if not self.is_running():
            raise RuntimeError("Emulator is not running")
        
        # Get window position
        window = pyautogui.getWindowsWithTitle(self.window_title)[0]
        x, y, width, height = window.left, window.top, window.width, window.height
        
        # Capture screen
        screenshot = pyautogui.screenshot(region=(x, y, width, height))
        return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    
    def press_button(self, button: str, duration: float = 0.1) -> None:
        """Press a button on the emulator.
        
        Args:
            button: Button to press ('a', 'b', 'start', 'select', 'up', 'down', 'left', 'right')
            duration: How long to hold the button in seconds
        """
        if not self.is_running():
            raise RuntimeError("Emulator is not running")
        
        self.input_handler.press_button(button, duration)
    
    def press_buttons(self, buttons: List[str], duration: float = 0.1) -> None:
        """Press multiple buttons simultaneously.
        
        Args:
            buttons: List of buttons to press
            duration: How long to hold the buttons in seconds
        """
        if not self.is_running():
            raise RuntimeError("Emulator is not running")
        
        self.input_handler.press_buttons(buttons, duration)
    
    def save_state(self, slot: int = 0) -> None:
        """Save the current game state.
        
        Args:
            slot: Save state slot number (0-9)
        """
        if not self.is_running():
            raise RuntimeError("Emulator is not running")
        
        if not self.save_state_dir:
            raise ValueError("Save state directory not specified")
        
        try:
            # Press Shift + F1-F10 for save states
            key = f"f{slot + 1}"
            pyautogui.hotkey("shift", key)
            logger.info(f"Saved state to slot {slot}")
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
            raise
    
    def load_state(self, slot: int = 0) -> None:
        """Load a previously saved game state.
        
        Args:
            slot: Save state slot number to load (0-9)
        """
        if not self.is_running():
            raise RuntimeError("Emulator is not running")
        
        if not self.save_state_dir:
            raise ValueError("Save state directory not specified")
        
        try:
            # Press F1-F10 for load states
            key = f"f{slot + 1}"
            pyautogui.press(key)
            logger.info(f"Loaded state from slot {slot}")
        except Exception as e:
            logger.error(f"Failed to load state: {e}")
            raise
    
    def get_memory_value(self, address: int, size: int = 1) -> int:
        """Read a value from the emulator's memory.
        
        Args:
            address: Memory address to read
            size: Number of bytes to read (1, 2, or 4)
            
        Returns:
            int: Value read from memory
        """
        if not self.is_running():
            raise RuntimeError("Emulator is not running")
        
        # TODO: Implement memory reading using mGBA's Python API
        # For now, return dummy value
        return 0
    
    def set_memory_value(self, address: int, value: int, size: int = 1) -> None:
        """Write a value to the emulator's memory.
        
        Args:
            address: Memory address to write to
            value: Value to write
            size: Size of the value in bytes (1, 2, or 4)
        """
        if not self.is_running():
            raise RuntimeError("Emulator is not running")
        
        # TODO: Implement memory writing using mGBA's Python API
        pass
    
    def get_game_state(self) -> GameState:
        """Get the current game state.
        
        Returns:
            Current GameState
        """
        if not self.is_running():
            raise RuntimeError("Emulator is not running")
        
        # Capture current screen
        screen = self.get_screen_state()
        
        # Create game state
        state = GameState()
        
        # Detect game mode
        if self.screen_analyzer.detect_battle_state(screen):
            state.mode = GameMode.BATTLE
        # TODO: Implement other mode detection
        
        # TODO: Update state from memory values
        
        return state
    
    def screenshot(self, path: Optional[str] = None) -> Optional[str]:
        """
        Take a screenshot of the current game state.
        
        Args:
            path: Optional path to save the screenshot
            
        Returns:
            Path to the saved screenshot if successful, None otherwise
        """
        logger.debug("Taking screenshot")
        # TODO: Implement screenshot capture
        return path
    
    def close(self) -> None:
        """Close the emulator."""
        logger.info("Closing emulator")
        # TODO: Implement emulator cleanup 