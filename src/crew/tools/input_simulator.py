"""
Input Simulator Tool

This module provides a CrewAI tool interface for simulating game inputs
and controlling the emulator.
"""

import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from utils.logger import get_logger
from utils.input_handler import InputHandler

logger = get_logger("crew")

@dataclass
class InputSimulatorConfig:
    """Configuration for input simulation."""
    default_press_duration: float = 0.1
    default_sequence_delay: float = 0.05
    max_retries: int = 3
    retry_delay: float = 0.5
    button_map: Dict[str, str] = field(default_factory=lambda: {
        'a': 'x',       # Map A button to X key
        'b': 'z',       # Map B button to Z key
        'up': 'up',     # Keep directional buttons as is
        'down': 'down',
        'left': 'left',
        'right': 'right',
        'start': 'enter',    # Map START to Enter key
        'select': 'backspace', # Map SELECT to Backspace key
        'l': 'a',       # Map L button to A key
        'r': 's'        # Map R button to S key
    })

class InputSimulatorTool:
    """Tool for simulating game inputs."""
    
    def __init__(self, config: Optional[InputSimulatorConfig] = None):
        """Initialize the input simulator tool.
        
        Args:
            config: Tool configuration
        """
        self.config = config or InputSimulatorConfig()
        self.input_handler = InputHandler()
        logger.info("Initialized input simulator tool")
        
    def ensure_emulator_focused(self) -> bool:
        """Ensure the emulator window is focused.
        
        Returns:
            True if emulator is focused, False otherwise
        """
        try:
            # Get emulator PID if we don't have it
            if not self.input_handler.emulator_pid:
                pid = self.input_handler.get_mgba_pid()
                if not pid:
                    logger.error("Could not find mGBA process")
                    return False
                    
            # Focus window
            return self.input_handler.focus_window("mGBA")
            
        except Exception as e:
            logger.error(f"Error focusing emulator: {e}")
            return False
            
    def press_button(self, button: str, duration: Optional[float] = None) -> bool:
        """Press a single button.
        
        Args:
            button: Button to press
            duration: How long to hold the button (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Map button name if needed
            mapped_button = self.config.button_map.get(button.lower(), button.lower())
            
            # Use default duration if none provided
            if duration is None:
                duration = self.config.default_press_duration
                
            # Ensure emulator is focused
            if not self.ensure_emulator_focused():
                return False
                
            # Press button with retries
            for attempt in range(self.config.max_retries):
                try:
                    self.input_handler.press_button(mapped_button, duration)
                    return True
                except Exception as e:
                    logger.warning(f"Button press attempt {attempt + 1} failed: {e}")
                    if attempt < self.config.max_retries - 1:
                        time.sleep(self.config.retry_delay)
                        
            logger.error(f"All attempts to press {button} failed")
            return False
            
        except Exception as e:
            logger.error(f"Error pressing button {button}: {e}")
            return False
            
    def press_sequence(self, sequence: List[Tuple[str, float]]) -> bool:
        """Press a sequence of buttons.
        
        Args:
            sequence: List of (button, duration) tuples
            
        Returns:
            True if all buttons were pressed successfully
        """
        try:
            # Ensure emulator is focused
            if not self.ensure_emulator_focused():
                return False
                
            # Press each button in sequence
            for button, duration in sequence:
                if not self.press_button(button, duration):
                    return False
                time.sleep(self.config.default_sequence_delay)
                
            return True
            
        except Exception as e:
            logger.error(f"Error executing button sequence: {e}")
            return False
            
    def navigate_menu(self, target_index: int, current_index: int = 0,
                     vertical: bool = True) -> bool:
        """Navigate to a specific menu index.
        
        Args:
            target_index: The menu index to navigate to
            current_index: The current menu index
            vertical: Whether the menu is vertical
            
        Returns:
            True if navigation was successful
        """
        try:
            # Ensure emulator is focused
            if not self.ensure_emulator_focused():
                return False
                
            # Use input handler's menu navigation
            self.input_handler.navigate_menu(
                target_index=target_index,
                current_index=current_index,
                vertical=vertical
            )
            return True
            
        except Exception as e:
            logger.error(f"Error navigating menu: {e}")
            return False
            
    def execute_command(self, command: Dict[str, Any]) -> bool:
        """Execute a game command.
        
        Args:
            command: Command dictionary with type, button, and duration
            
        Returns:
            True if command was executed successfully
        """
        try:
            cmd_type = command.get("type")
            if not cmd_type:
                logger.error("No command type specified")
                return False
                
            if cmd_type == "button_press":
                return self.press_button(
                    button=command["button"],
                    duration=command.get("duration", self.config.default_press_duration)
                )
            elif cmd_type == "sequence":
                return self.press_sequence(command["sequence"])
            elif cmd_type == "menu_nav":
                return self.navigate_menu(
                    target_index=command["target_index"],
                    current_index=command.get("current_index", 0),
                    vertical=command.get("vertical", True)
                )
            else:
                logger.error(f"Unknown command type: {cmd_type}")
                return False
                
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            return False
            
    def __str__(self) -> str:
        """Get string representation of the tool.
        
        Returns:
            Tool description string
        """
        return "Input Simulator Tool - Controls game inputs and menu navigation" 