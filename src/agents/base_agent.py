"""
Base Agent Module

This module defines the base agent class that all other agents inherit from.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from utils.logger import get_logger
from emulator.interface import EmulatorInterface
from emulator.game_state import GameState

# Get logger for this module
logger = get_logger("agents")

class BaseAgent(ABC):
    """Base class for all agents."""
    
    def __init__(self, name: str, emulator: EmulatorInterface):
        """Initialize the base agent.
        
        Args:
            name: Agent name
            emulator: EmulatorInterface instance
        """
        self.name = name
        self.emulator = emulator
        logger.info(f"Initialized {self.name} agent")
    
    @abstractmethod
    def analyze_state(self, state: GameState) -> Optional[Dict[str, Any]]:
        """Analyze the current game state and decide on an action.
        
        Args:
            state: Current game state
            
        Returns:
            Optional action parameters
        """
        pass
    
    @abstractmethod
    def execute_action(self, action_params: Dict[str, Any]) -> bool:
        """Execute an action with the given parameters.
        
        Args:
            action_params: Action parameters
            
        Returns:
            True if action was successful
        """
        pass
    
    def update(self, state: GameState) -> bool:
        """Update the agent with the current game state.
        
        Args:
            state: Current game state
            
        Returns:
            True if agent took action
        """
        try:
            # Analyze state
            action_params = self.analyze_state(state)
            if action_params is None:
                return False
            
            # Execute action
            logger.debug(f"{self.name} executing action: {action_params}")
            success = self.execute_action(action_params)
            
            if success:
                logger.debug(f"{self.name} successfully executed action")
            else:
                logger.warning(f"{self.name} failed to execute action")
            
            return success
            
        except Exception as e:
            logger.error(f"Error in {self.name} update: {e}")
            return False
    
    def handle_error(self, error: Exception) -> None:
        """Handle an error that occurred during agent operation.
        
        Args:
            error: Exception that occurred
        """
        logger.error(f"Error in {self.name}: {error}")
        # Subclasses can implement specific error handling 