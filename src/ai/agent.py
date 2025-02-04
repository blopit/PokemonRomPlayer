"""
Base agent class for Pokemon game automation
"""

from typing import List, Dict, Any, Optional
from utils.command_queue import CommandQueue, GameCommand
from utils.logger import get_logger

logger = get_logger("pokemon_player")

class Agent:
    """Base class for specialized agents"""
    
    def __init__(self, name: str):
        """Initialize agent.
        
        Args:
            name: Agent name/role
        """
        self.name = name
        self.command_queue = CommandQueue()
        
    def generate_commands(self, 
                         screen_state: Dict[str, Any],
                         game_state: Dict[str, Any],
                         context: Optional[Dict[str, Any]] = None) -> List[GameCommand]:
        """Generate commands based on current state.
        
        Args:
            screen_state: Current screen analysis results
            game_state: Current game memory state
            context: Optional additional context
            
        Returns:
            List of commands to execute
        """
        raise NotImplementedError
        
    def can_handle(self, 
                   screen_state: Dict[str, Any],
                   game_state: Dict[str, Any]) -> bool:
        """Check if this agent can handle the current state.
        
        Args:
            screen_state: Current screen analysis results
            game_state: Current game memory state
            
        Returns:
            True if agent can handle this state
        """
        raise NotImplementedError 