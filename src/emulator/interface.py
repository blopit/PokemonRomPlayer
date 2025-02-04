"""
Interface for controlling the mGBA emulator
"""

import os
import platform
import subprocess
import time
from typing import Optional, List, Dict, Any
import numpy as np

from utils.logger import get_logger
from utils.input_handler import InputHandler
from utils.screenshot import capture_window, crop_to_ratio
from emulator.memory_reader import MemoryReader
from emulator.memory_map import GameVersion

logger = get_logger("pokemon_player")

class EmulatorInterface:
    """Interface for controlling mGBA emulator"""
    
    def __init__(self, rom_path: str, emulator_path: Optional[str] = None, version: GameVersion = GameVersion.EMERALD):
        """Initialize emulator interface.
        
        Args:
            rom_path: Path to ROM file
            emulator_path: Optional path to mGBA executable
            version: Pokemon game version
        """
        self.rom_path = os.path.abspath(rom_path)
        self.is_macos = platform.system() == "Darwin"
        self.emulator_path = emulator_path or self._find_emulator()
        self.process: Optional[subprocess.Popen] = None
        self.version = version
        self.memory_reader: Optional[MemoryReader] = None
        
        # Expected GBA screen dimensions (scaled)
        self.expected_width = 480
        self.expected_height = 320
        
        # Initialize input handler
        self.input_handler = InputHandler()
        
        logger.info(f"Initialized EmulatorInterface with ROM: {rom_path}")
        logger.info(f"Using emulator at: {self.emulator_path}")
        
    def _find_emulator(self) -> str:
        """Find mGBA executable path.
        
        Returns:
            Path to mGBA executable
        """
        if self.is_macos:
            # Check common macOS locations
            paths = [
                "/usr/local/bin/mgba-qt",
                "/opt/homebrew/bin/mgba-qt",
                "/Applications/mGBA.app/Contents/MacOS/mGBA"
            ]
        else:
            # Check common Linux/Windows locations
            paths = [
                "mgba-qt",
                "C:\\Program Files\\mGBA\\mGBA.exe",
                "C:\\Program Files (x86)\\mGBA\\mGBA.exe"
            ]
            
        for path in paths:
            if os.path.exists(path):
                return path
                
        raise FileNotFoundError("Could not find mGBA executable")
        
    def start(self) -> bool:
        """Start the emulator.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("Starting emulator...")
            
            # Start mGBA
            self.process = subprocess.Popen(
                [self.emulator_path, self.rom_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for emulator to start
            time.sleep(2)
            
            if self.process.poll() is not None:
                logger.error("Failed to start emulator")
                return False
                
            # Initialize memory reader
            self.memory_reader = MemoryReader(self.process.pid, self.version)
            
            logger.info("Emulator started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error starting emulator: {e}")
            return False
            
    def stop(self) -> bool:
        """Stop the emulator.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.process:
                logger.info("Stopping emulator...")
                self.process.terminate()
                self.process.wait(timeout=5)
                self.memory_reader = None
                logger.info("Emulator stopped successfully")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error stopping emulator: {e}")
            return False
            
    def focus_window(self) -> bool:
        """Focus the emulator window.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.process:
                return False
                
            if self.is_macos:
                # Use AppleScript to focus window
                script = """
                tell application "System Events"
                    set mgbaProcess to first process whose unix id is %d
                    set frontmost of mgbaProcess to true
                end tell
                """ % self.process.pid
                
                subprocess.run(['osascript', '-e', script], check=True)
                return True
                
            else:
                # TODO: Implement for other platforms
                return False
                
        except Exception as e:
            logger.error(f"Error focusing window: {e}")
            return False
            
    def get_screen_state(self) -> np.ndarray:
        """Get current screen state.
        
        Returns:
            Numpy array containing the processed screenshot
        """
        try:
            # Capture window screenshot
            screenshot = capture_window(pid=self.process.pid if self.process else None)
            
            # Crop to GBA aspect ratio
            processed = crop_to_ratio(screenshot, self.expected_width, self.expected_height)
            
            return processed
            
        except Exception as e:
            logger.error(f"Error getting screen state: {e}")
            raise
            
    def get_game_state(self) -> Dict[str, Any]:
        """Get current game state from memory.
        
        Returns:
            Dictionary containing game state data
        """
        try:
            if not self.memory_reader:
                return {}
                
            return self.memory_reader.read_game_state()
            
        except Exception as e:
            logger.error(f"Error getting game state: {e}")
            return {}
            
    def get_party_data(self) -> Dict[str, Any]:
        """Get current party data from memory.
        
        Returns:
            Dictionary containing party data
        """
        try:
            if not self.memory_reader:
                return {"count": 0, "pokemon": []}
                
            return self.memory_reader.read_party_data()
            
        except Exception as e:
            logger.error(f"Error getting party data: {e}")
            return {"count": 0, "pokemon": []}
            
    def press_button(self, button: str, duration: float = 0.1):
        """Press a button.
        
        Args:
            button: Button to press
            duration: How long to hold the button
        """
        self.input_handler.press_button(button, duration)
        
    def press_buttons(self, buttons: List[str], duration: float = 0.1):
        """Press multiple buttons simultaneously.
        
        Args:
            buttons: List of buttons to press
            duration: How long to hold the buttons
        """
        self.input_handler.press_buttons(buttons, duration)
            
    @property
    def pid(self) -> Optional[int]:
        """Get process ID of running emulator.
        
        Returns:
            Process ID if emulator is running, None otherwise
        """
        return self.process.pid if self.process else None 