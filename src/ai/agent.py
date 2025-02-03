from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from dataclasses import dataclass

from utils.logger import logger
from emulator.interface import EmulatorInterface
from emulator.game_state import GameState

@dataclass
class AgentAction:
    """Represents an action to be taken by an agent."""
    action_type: str
    parameters: Dict[str, Any]
    priority: int = 0
    
    def __lt__(self, other):
        """Compare actions by priority."""
        return self.priority < other.priority

class Agent(ABC):
    """Base class for AI agents."""
    
    def __init__(self, emulator: EmulatorInterface, name: str = "BaseAgent"):
        """Initialize the agent.
        
        Args:
            emulator: EmulatorInterface instance
            name: Agent name for logging
        """
        self.emulator = emulator
        self.name = name
        logger.info(f"Initialized {self.name}")
    
    @abstractmethod
    def analyze_state(self, state: GameState) -> Optional[AgentAction]:
        """Analyze the current game state and decide on an action.
        
        Args:
            state: Current game state
            
        Returns:
            Optional action to take
        """
        pass
    
    @abstractmethod
    def execute_action(self, action: AgentAction) -> bool:
        """Execute the specified action.
        
        Args:
            action: Action to execute
            
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
            # Analyze state and get action
            action = self.analyze_state(state)
            if action is None:
                return False
            
            # Execute action
            logger.debug(f"{self.name} executing action: {action.action_type}")
            success = self.execute_action(action)
            
            if success:
                logger.debug(f"{self.name} successfully executed action: {action.action_type}")
            else:
                logger.warning(f"{self.name} failed to execute action: {action.action_type}")
            
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