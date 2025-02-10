"""
CrewAI Menu Agent

This module provides a CrewAI wrapper around the existing menu agent,
integrating it into the CrewAI task pipeline while preserving its core functionality.
"""

from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from enum import Enum, auto
from crewai import Agent
from utils.logger import get_logger
from ai.menu_agent import MenuAgent as CoreMenuAgent
from utils.command_queue import GameCommand

logger = get_logger("crew")

class MenuAction(Enum):
    """Types of menu actions."""
    OPEN_MENU = auto()      # Open the main menu
    CLOSE_MENU = auto()     # Close current menu
    SELECT_ITEM = auto()    # Select a menu item
    USE_ITEM = auto()       # Use an item
    ORGANIZE_PARTY = auto() # Organize Pokemon party
    SAVE_GAME = auto()      # Save the game
    CHECK_POKEMON = auto()  # Check Pokemon status
    CHECK_BADGES = auto()   # Check gym badges
    CHECK_ITEMS = auto()    # Check inventory

@dataclass
class MenuRequest:
    """Request for menu interaction."""
    action: MenuAction
    target: Optional[str] = None  # Target item/option name
    priority: int = 0  # Higher priority requests take precedence
    context: Dict[str, Any] = field(default_factory=dict)

class CrewMenuAgent(Agent):
    """CrewAI wrapper for the menu management agent."""
    
    def __init__(self, 
                 name: str = "CrewMenuAgent",
                 goal: str = "Handle menu interactions and inventory management efficiently",
                 backstory: str = "UI/UX expert specializing in Pokemon game menus and item management",
                 verbose: bool = True,
                 llm_provider: str = "openai"):
        """Initialize the CrewAI menu agent.
        
        Args:
            name: Agent name
            goal: Agent's primary goal
            backstory: Agent's background story
            verbose: Whether to enable verbose logging
            llm_provider: LLM provider to use
        """
        super().__init__(
            name=name,
            goal=goal,
            backstory=backstory,
            verbose=verbose
        )
        
        # Initialize core menu agent
        self.core_agent = CoreMenuAgent(provider=llm_provider)
        
        # Initialize menu state
        self.current_request = None
        self.request_queue: List[MenuRequest] = []
        self.menu_context: Dict[str, Any] = {}
        
        logger.info(f"Initialized {name} with {llm_provider} provider")
        
    def add_request(self, request: MenuRequest) -> None:
        """Add a menu request to the queue.
        
        Args:
            request: Menu interaction request
        """
        # Insert request in priority order
        insert_idx = 0
        for idx, existing in enumerate(self.request_queue):
            if request.priority > existing.priority:
                break
            insert_idx = idx + 1
            
        self.request_queue.insert(insert_idx, request)
        logger.info(f"Added menu request: {request.action.name} - {request.target}")
        
    def clear_requests(self) -> None:
        """Clear all pending menu requests."""
        self.request_queue.clear()
        self.current_request = None
        logger.info("Cleared all menu requests")
        
    def analyze_state(self, screen_state: Dict[str, Any], game_state: Dict[str, Any]) -> bool:
        """Analyze if current state requires menu interaction.
        
        Args:
            screen_state: Current screen analysis results
            game_state: Current game memory state
            
        Returns:
            True if menu interaction is needed
        """
        # Check if we can handle the current state
        if not self.core_agent.can_handle(screen_state, game_state):
            return False
            
        # If we have a current request, we need menu interaction
        if self.current_request:
            return True
            
        # If we have requests in queue, we need menu interaction
        if self.request_queue:
            self.current_request = self.request_queue.pop(0)
            return True
            
        return False
        
    def handle_menu(self, 
                    screen_state: Dict[str, Any],
                    game_state: Dict[str, Any]) -> List[GameCommand]:
        """Handle menu interaction based on current state and request.
        
        Args:
            screen_state: Current screen analysis results
            game_state: Current game memory state
            
        Returns:
            List of game commands for menu interaction
        """
        try:
            # Check if we need to handle menus
            if not self.analyze_state(screen_state, game_state):
                return []
                
            # Prepare context for menu navigation
            context = {
                "action": self.current_request.action.name,
                "target": self.current_request.target,
                **self.current_request.context,
                **self.menu_context
            }
            
            # Generate commands using core agent
            commands = self.core_agent.generate_commands(
                screen_state=screen_state,
                game_state=game_state,
                context=context
            )
            
            if commands:
                logger.info(f"Generated {len(commands)} menu commands")
            else:
                logger.warning("No menu commands generated")
                # Clear current request if we can't handle it
                self.current_request = None
                
            return commands
            
        except Exception as e:
            logger.error(f"Error handling menu: {e}")
            self.handle_error(e)
            return []
            
    def update_context(self, updates: Dict[str, Any]) -> None:
        """Update the menu context with new information.
        
        Args:
            updates: Dictionary of context updates
        """
        self.menu_context.update(updates)
        
    def handle_error(self, error: Exception) -> None:
        """Handle errors during menu interaction.
        
        Args:
            error: The error that occurred
        """
        logger.error(f"Menu error: {error}")
        # Clear current request on error
        self.current_request = None
        
        # TODO: Implement error recovery strategies
        # For example:
        # - Try to return to main menu
        # - Clear any stuck menu states
        # - Retry with simplified navigation
        
    def __str__(self) -> str:
        """String representation of the agent.
        
        Returns:
            Agent description string
        """
        status = "BUSY" if self.current_request else "IDLE"
        queue_size = len(self.request_queue)
        return f"{self.name} - Menu Expert (Status: {status}, Queued: {queue_size})" 