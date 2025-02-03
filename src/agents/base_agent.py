"""
Base Agent Module

This module defines the base agent class that all specialized agents will inherit from.
It provides common functionality and interfaces for agent interaction.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from ..emulator.interface import EmulatorInterface, GameState

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """Base class for all AI agents in the system."""
    
    def __init__(self, emulator: EmulatorInterface, config: Dict[str, Any]):
        """
        Initialize the base agent.
        
        Args:
            emulator: Interface to the GBA emulator
            config: Configuration dictionary for the agent
        """
        self.emulator = emulator
        self.config = config
        self.name = self.__class__.__name__
        logger.info(f"Initializing {self.name}")
        
    @abstractmethod
    def act(self, state: GameState) -> bool:
        """
        Process the current game state and take appropriate action.
        
        Args:
            state: Current game state
            
        Returns:
            True if action was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def can_handle(self, state: GameState) -> bool:
        """
        Determine if this agent can handle the current game state.
        
        Args:
            state: Current game state
            
        Returns:
            True if this agent can handle the current state
        """
        pass
    
    def update_config(self, new_config: Dict[str, Any]) -> None:
        """
        Update the agent's configuration.
        
        Args:
            new_config: New configuration dictionary
        """
        self.config.update(new_config)
        logger.debug(f"Updated {self.name} config: {new_config}")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the agent.
        
        Returns:
            Dictionary containing agent status information
        """
        return {
            "name": self.name,
            "config": self.config,
            "active": self.can_handle(self.emulator.get_game_state())
        }
    
    def _log_action(self, action: str, success: bool, details: Optional[str] = None) -> None:
        """
        Log an action taken by the agent.
        
        Args:
            action: Name of the action
            success: Whether the action was successful
            details: Optional additional details
        """
        status = "SUCCESS" if success else "FAILED"
        message = f"{self.name} {action}: {status}"
        if details:
            message += f" - {details}"
        
        if success:
            logger.info(message)
        else:
            logger.error(message)
    
    def _safe_execute(self, action_name: str, action_func: callable, *args, **kwargs) -> Any:
        """
        Safely execute an action with error handling and logging.
        
        Args:
            action_name: Name of the action for logging
            action_func: Function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Result of the action function
        """
        try:
            result = action_func(*args, **kwargs)
            self._log_action(action_name, True)
            return result
        except Exception as e:
            self._log_action(action_name, False, str(e))
            logger.exception(f"Error in {self.name} during {action_name}")
            return None 