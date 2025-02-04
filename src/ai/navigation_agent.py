"""
Navigation Agent Module

This module handles navigation and pathfinding in the game world.
"""

from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass
from enum import Enum, auto
import logging

from utils.logger import get_logger
from emulator.interface import EmulatorInterface
from emulator.game_state import GameState, GameMode
from .agent import Agent, AgentAction

# Get logger for this module
logger = logging.getLogger(__name__)

class NavigationMode(Enum):
    """Different modes of navigation."""
    EXPLORE = auto()  # Free exploration
    PATHFIND = auto()  # Following a specific path
    BACKTRACK = auto()  # Return to previous location

@dataclass
class MapLocation:
    """Represents a location in the game world."""
    name: str
    x: int
    y: int
    map_id: str
    connections: List[str] = None  # Names of connected locations
    
    def __post_init__(self):
        if self.connections is None:
            self.connections = []
            
    def __eq__(self, other):
        if not isinstance(other, MapLocation):
            return False
        return (self.x == other.x and 
                self.y == other.y and 
                self.map_id == other.map_id)
                
    def __hash__(self):
        return hash((self.x, self.y, self.map_id))
        
    def distance_to(self, other: 'MapLocation') -> float:
        """Calculate Manhattan distance to another location.
        
        Args:
            other: Target location
            
        Returns:
            Manhattan distance
        """
        if self.map_id != other.map_id:
            return float('inf')
        return abs(self.x - other.x) + abs(self.y - other.y)

class NavigationAgent(Agent):
    """Agent specialized for handling overworld navigation."""
    
    def __init__(self, name: str, emulator: EmulatorInterface, mode: NavigationMode = NavigationMode.EXPLORE,
                 target_x: Optional[int] = None, target_y: Optional[int] = None):
        """Initialize the navigation agent.
        
        Args:
            name: Agent name
            emulator: EmulatorInterface instance
            mode: Navigation mode to use
            target_x: Optional target X coordinate
            target_y: Optional target Y coordinate
        """
        super().__init__(name, emulator)
        self.mode = mode
        self.target_x = target_x
        self.target_y = target_y
        self.current_location = None
        self.target_location = None
        self.known_locations = {}  # Map ID -> List[MapLocation]
        logger.info(f"Initialized navigation agent with mode: {mode}")
    
    def analyze_state(self, state: GameState) -> Optional[AgentAction]:
        """Analyze the current state and determine navigation action.
        
        Args:
            state: Current game state
            
        Returns:
            AgentAction if one should be taken, None otherwise
        """
        if state.mode != GameMode.OVERWORLD:
            logger.debug(f"Agent {self.name} cannot handle non-overworld state")
            return None
        
        # Check if we've reached target
        if self._at_target(state):
            logger.info(f"Agent {self.name} reached target location")
            return None
        
        # Determine movement direction
        if self._should_move(state):
            logger.debug(f"Agent {self.name} deciding movement direction")
            return AgentAction.MOVE
        
        return None
    
    def execute_action(self, action: AgentAction, state: GameState) -> bool:
        """Execute the specified navigation action.
        
        Args:
            action: Action to execute
            state: Current game state
            
        Returns:
            True if action was executed successfully
        """
        if action != AgentAction.MOVE:
            logger.warning(f"Agent {self.name} received invalid action: {action}")
            return False
        
        return self._handle_movement(state)
    
    def _at_target(self, state: GameState) -> bool:
        """Check if we've reached the target location.
        
        Args:
            state: Current game state
            
        Returns:
            True if at target location
        """
        if self.target_x is None or self.target_y is None:
            return False
        
        return (state.player.x_position == self.target_x and 
                state.player.y_position == self.target_y)
    
    def _should_move(self, state: GameState) -> bool:
        """Determine if movement is needed.
        
        Args:
            state: Current game state
            
        Returns:
            True if movement is needed
        """
        if self.mode == NavigationMode.EXPLORE:
            return True
        
        if self.mode == NavigationMode.PATHFIND:
            return not self._at_target(state)
        
        return False
    
    def _handle_movement(self, state: GameState) -> bool:
        """Handle movement in the appropriate direction.
        
        Args:
            state: Current game state
            
        Returns:
            True if movement was successful
        """
        try:
            if self.mode == NavigationMode.EXPLORE:
                return self._handle_exploration(state)
            elif self.mode == NavigationMode.PATHFIND:
                return self._handle_pathfinding(state)
            else:
                return self._handle_backtracking(state)
            
        except Exception as e:
            logger.error(f"Error handling movement: {e}")
            return False
    
    def _handle_exploration(self, state: GameState) -> bool:
        """Handle free exploration movement.
        
        Args:
            state: Current game state
            
        Returns:
            True if movement was successful
        """
        # TODO: Implement smarter exploration
        # For now, just move in a random valid direction
        self.emulator.press_button('right')
        return True
    
    def _handle_pathfinding(self, state: GameState) -> bool:
        """Handle pathfinding movement.
        
        Args:
            state: Current game state
            
        Returns:
            True if movement was successful
        """
        if self.target_x is None or self.target_y is None:
            logger.warning("No target location set for pathfinding")
            return False
        
        # Calculate direction to target
        dx = self.target_x - state.player.x_position
        dy = self.target_y - state.player.y_position
        
        # Move in the direction of larger difference
        if abs(dx) > abs(dy):
            button = 'right' if dx > 0 else 'left'
        else:
            button = 'down' if dy > 0 else 'up'
        
        self.emulator.press_button(button)
        return True
    
    def _handle_backtracking(self, state: GameState) -> bool:
        """Handle backtracking movement.
        
        Args:
            state: Current game state
            
        Returns:
            True if movement was successful
        """
        # TODO: Implement backtracking logic
        logger.warning("Backtracking not yet implemented")
        return False

    def set_current_location(self, location: MapLocation):
        """Set the current location.
        
        Args:
            location: Current location
        """
        self.current_location = location
        if location.map_id not in self.known_locations:
            self.known_locations[location.map_id] = []
        if location not in self.known_locations[location.map_id]:
            self.known_locations[location.map_id].append(location)
            
    def set_target_location(self, location: MapLocation) -> bool:
        """Set the target location.
        
        Args:
            location: Target location
            
        Returns:
            True if target is reachable
        """
        self.target_location = location
        return self.is_reachable(location)
        
    def is_reachable(self, location: MapLocation) -> bool:
        """Check if a location is reachable from current position.
        
        Args:
            location: Target location
            
        Returns:
            True if location is reachable
        """
        if not self.current_location:
            return False
            
        # Same map
        if location.map_id == self.current_location.map_id:
            return True
            
        # Check connections
        return any(loc.name in self.current_location.connections 
                  for loc in self.known_locations.get(location.map_id, []))
                  
    def get_next_move(self) -> Optional[str]:
        """Get the next movement action.
        
        Returns:
            Movement action or None if no move needed
        """
        if not self.current_location or not self.target_location:
            return None
            
        if self.current_location == self.target_location:
            return None
            
        dx = self.target_location.x - self.current_location.x
        dy = self.target_location.y - self.current_location.y
        
        if abs(dx) > abs(dy):
            return "MOVE_RIGHT" if dx > 0 else "MOVE_LEFT"
        else:
            return "MOVE_DOWN" if dy > 0 else "MOVE_UP" 