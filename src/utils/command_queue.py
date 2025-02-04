"""
Command queue system for batched processing of game commands
"""

from dataclasses import dataclass
from typing import List, Optional, Union, Dict
import time
from utils.logger import get_logger

logger = get_logger("pokemon_player")

@dataclass
class GameCommand:
    """Represents a single game command"""
    command_type: str  # 'button_press', 'wait', etc.
    args: Dict  # Command-specific arguments
    delay: float = 0.0  # Delay before executing this command
    
class CommandQueue:
    """Manages a queue of game commands for batch processing"""
    
    def __init__(self):
        self.commands: List[GameCommand] = []
        
    def add_command(self, command: GameCommand):
        """Add a single command to the queue"""
        self.commands.append(command)
        
    def add_commands(self, commands: List[GameCommand]):
        """Add multiple commands to the queue"""
        self.commands.extend(commands)
        
    def clear(self):
        """Clear all commands from the queue"""
        self.commands.clear()
        
    def is_empty(self) -> bool:
        """Check if queue is empty"""
        return len(self.commands) == 0
        
    def process_commands(self, emulator) -> None:
        """Process all commands in the queue"""
        while not self.is_empty():
            command = self.commands.pop(0)
            try:
                # Execute command based on type
                if command.command_type == 'button_press':
                    button = command.args.get('button')
                    duration = command.args.get('duration', 0.1)
                    emulator.press_button(button, duration=duration)
                    
                elif command.command_type == 'wait':
                    duration = command.args.get('duration', 1.0)
                    time.sleep(duration)
                    
                # Add delay after command if specified
                if command.delay > 0:
                    time.sleep(command.delay)
                    
            except Exception as e:
                logger.error(f"Error executing command {command}: {e}")
                
    @staticmethod
    def create_button_press(button: str, duration: float = 0.1, delay: float = 0.0) -> GameCommand:
        """Create a button press command"""
        return GameCommand(
            command_type='button_press',
            args={'button': button, 'duration': duration},
            delay=delay
        )
        
    @staticmethod
    def create_wait(duration: float, delay: float = 0.0) -> GameCommand:
        """Create a wait command"""
        return GameCommand(
            command_type='wait',
            args={'duration': duration},
            delay=delay
        ) 