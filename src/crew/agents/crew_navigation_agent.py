"""
CrewAI Navigation Agent

This module provides a CrewAI wrapper around the existing navigation agent,
integrating it into the CrewAI task pipeline while preserving its core functionality.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from crewai import Agent
from utils.logger import get_logger
from ai.navigation_agent import NavigationAgent as CoreNavigationAgent
from ai.navigation_agent import NavigationMode, MapLocation
from emulator.game_state import GameState, GameMode

logger = get_logger("crew")

@dataclass
class NavigationTarget:
    """Target location for navigation."""
    name: str
    x: int
    y: int
    map_id: str
    priority: int = 0  # Higher priority targets take precedence

class CrewNavigationAgent(Agent):
    """CrewAI wrapper for the navigation management agent."""
    
    def __init__(self, 
                 name: str = "CrewNavigationAgent",
                 goal: str = "Navigate the Pokemon world efficiently and reach objectives",
                 backstory: str = "Expert pathfinder with deep knowledge of Pokemon world geography",
                 verbose: bool = True,
                 mode: NavigationMode = NavigationMode.EXPLORE):
        """Initialize the CrewAI navigation agent.
        
        Args:
            name: Agent name
            goal: Agent's primary goal
            backstory: Agent's background story
            verbose: Whether to enable verbose logging
            mode: Navigation mode to use
        """
        super().__init__(
            name=name,
            goal=goal,
            backstory=backstory,
            verbose=verbose
        )
        
        # Initialize core navigation agent
        self.core_agent = CoreNavigationAgent(
            name=name,
            emulator=None,  # Will be set when needed
            mode=mode
        )
        
        # Initialize navigation state
        self.current_target = None
        self.target_queue: List[NavigationTarget] = []
        
        logger.info(f"Initialized {name} with mode: {mode}")
        
    def set_emulator(self, emulator) -> None:
        """Set the emulator interface for the core agent.
        
        Args:
            emulator: EmulatorInterface instance
        """
        self.core_agent.emulator = emulator
        
    def add_target(self, target: NavigationTarget) -> None:
        """Add a navigation target to the queue.
        
        Args:
            target: Target location to navigate to
        """
        # Insert target in priority order
        insert_idx = 0
        for idx, existing in enumerate(self.target_queue):
            if target.priority > existing.priority:
                break
            insert_idx = idx + 1
            
        self.target_queue.insert(insert_idx, target)
        logger.info(f"Added navigation target: {target.name} (priority: {target.priority})")
        
    def clear_targets(self) -> None:
        """Clear all navigation targets."""
        self.target_queue.clear()
        self.current_target = None
        logger.info("Cleared all navigation targets")
        
    def analyze_state(self, state: GameState) -> bool:
        """Analyze if current state requires navigation.
        
        Args:
            state: Current game state
            
        Returns:
            True if navigation is needed
        """
        # Check if we're in a state where navigation is possible
        if state.mode != GameMode.OVERWORLD:
            return False
            
        # If we have a current target, we need navigation
        if self.current_target:
            return True
            
        # If we have targets in queue, we need navigation
        if self.target_queue:
            # Set the next target
            self.current_target = self.target_queue.pop(0)
            # Update core agent target
            self.core_agent.target_x = self.current_target.x
            self.core_agent.target_y = self.current_target.y
            return True
            
        return False
        
    def navigate(self, state: GameState) -> bool:
        """Execute navigation based on current state.
        
        Args:
            state: Current game state
            
        Returns:
            True if navigation was successful
        """
        try:
            # Check if we need to navigate
            if not self.analyze_state(state):
                return False
                
            # Update current location in core agent
            if state.map_id and state.player:
                current_loc = MapLocation(
                    name="current",
                    x=state.player.x_position,
                    y=state.player.y_position,
                    map_id=state.map_id
                )
                self.core_agent.set_current_location(current_loc)
                
            # Let core agent handle navigation
            action = self.core_agent.analyze_state(state)
            if action:
                return self.core_agent.execute_action(action, state)
                
            # If no action needed, we might be at target
            if self.core_agent._at_target(state):
                logger.info(f"Reached target: {self.current_target.name}")
                self.current_target = None
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error during navigation: {e}")
            return False
            
    def handle_error(self, error: Exception) -> None:
        """Handle errors during navigation.
        
        Args:
            error: The error that occurred
        """
        logger.error(f"Navigation error: {error}")
        # TODO: Implement error recovery strategies
        # For now, just clear the current target
        self.current_target = None
        
    def __str__(self) -> str:
        """String representation of the agent.
        
        Returns:
            Agent description string
        """
        mode_str = self.core_agent.mode.name if self.core_agent else "UNKNOWN"
        return f"{self.name} - Navigation Expert (Mode: {mode_str})" 