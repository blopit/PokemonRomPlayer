from typing import List, Optional, Tuple, Dict
from dataclasses import dataclass
import numpy as np

from utils.logger import logger
from emulator.interface import EmulatorInterface
from emulator.game_state import GameState, GameMode
from .agent import Agent, AgentAction
from .pathfinding import PathFinder

@dataclass
class MapLocation:
    """Represents a location on the game map."""
    x: int
    y: int
    map_id: int
    name: str = ""
    
    def distance_to(self, other: 'MapLocation') -> float:
        """Calculate Manhattan distance to another location."""
        if self.map_id != other.map_id:
            return float('inf')
        return abs(self.x - other.x) + abs(self.y - other.y)

@dataclass
class NavigationTarget:
    """Target destination for navigation."""
    location: MapLocation
    required_conditions: Dict[str, bool] = None  # e.g., {"has_surf": True}

class NavigationAgent(Agent):
    """Agent responsible for overworld navigation and pathfinding."""
    
    # Action types
    MOVE = "move"
    INTERACT = "interact"
    USE_ITEM = "use_item"
    
    # Movement directions
    DIRECTIONS = ['up', 'down', 'left', 'right']
    
    def __init__(self, emulator: EmulatorInterface):
        """Initialize the navigation agent.
        
        Args:
            emulator: EmulatorInterface instance
        """
        super().__init__(emulator, name="NavigationAgent")
        self.current_path: List[Tuple[int, int]] = []
        self.current_target: Optional[NavigationTarget] = None
        self.map_data: Dict[int, np.ndarray] = {}  # Map ID -> Collision map
        self.pathfinders: Dict[int, PathFinder] = {}  # Map ID -> PathFinder
    
    def set_target(self, target: NavigationTarget) -> None:
        """Set a new navigation target.
        
        Args:
            target: Target to navigate to
        """
        self.current_target = target
        self.current_path = []
        logger.info(f"Set new navigation target: {target.location.name}")
    
    def analyze_state(self, state: GameState) -> Optional[AgentAction]:
        """Analyze the current state and decide on movement.
        
        Args:
            state: Current game state
            
        Returns:
            Movement action to take
        """
        if state.mode != GameMode.OVERWORLD or self.current_target is None:
            return None
        
        current_location = MapLocation(
            x=state.player.x_position,
            y=state.player.y_position,
            map_id=state.current_map_id
        )
        
        # Check if we've reached the target
        if current_location.distance_to(self.current_target.location) == 0:
            logger.info("Reached navigation target")
            self.current_target = None
            return None
        
        # Update or calculate path if needed
        if not self.current_path:
            self.current_path = self._calculate_path(
                current_location,
                self.current_target.location
            )
            if not self.current_path:
                logger.error("Could not find path to target")
                return None
        
        # Get next step in path
        next_x, next_y = self.current_path[0]
        dx = next_x - current_location.x
        dy = next_y - current_location.y
        
        # Determine direction to move
        if dx > 0:
            direction = 'right'
        elif dx < 0:
            direction = 'left'
        elif dy > 0:
            direction = 'down'
        elif dy < 0:
            direction = 'up'
        else:
            return None
        
        return AgentAction(
            action_type=self.MOVE,
            parameters={"direction": direction},
            priority=1
        )
    
    def execute_action(self, action: AgentAction) -> bool:
        """Execute a navigation action.
        
        Args:
            action: Action to execute
            
        Returns:
            True if action was successful
        """
        try:
            if action.action_type == self.MOVE:
                return self._execute_move(action.parameters["direction"])
            
            elif action.action_type == self.INTERACT:
                return self._execute_interact()
            
            elif action.action_type == self.USE_ITEM:
                return self._execute_use_item(action.parameters["item_id"])
            
            else:
                logger.error(f"Unknown action type: {action.action_type}")
                return False
            
        except Exception as e:
            self.handle_error(e)
            return False
    
    def _calculate_path(self, start: MapLocation, goal: MapLocation) -> List[Tuple[int, int]]:
        """Calculate path from start to goal using A* pathfinding.
        
        Args:
            start: Starting location
            goal: Goal location
            
        Returns:
            List of (x, y) coordinates forming the path
        """
        if start.map_id != goal.map_id:
            logger.error("Cannot pathfind between different maps yet")
            return []
        
        # Get or create pathfinder for current map
        if start.map_id not in self.pathfinders:
            collision_map = self.map_data.get(start.map_id)
            if collision_map is None:
                logger.error("No collision map data for current map")
                return []
            self.pathfinders[start.map_id] = PathFinder(collision_map)
        
        pathfinder = self.pathfinders[start.map_id]
        return pathfinder.find_path(start, goal)
    
    def _execute_move(self, direction: str) -> bool:
        """Execute a movement in a direction.
        
        Args:
            direction: Direction to move
            
        Returns:
            True if successful
        """
        try:
            # Hold direction button briefly
            self.emulator.press_button(direction, duration=0.2)
            
            # Update path if move was successful
            if self.current_path:
                self.current_path.pop(0)
            
            return True
            
        except Exception as e:
            logger.error(f"Error executing move: {e}")
            return False
    
    def _execute_interact(self) -> bool:
        """Execute an interaction with an object/NPC.
        
        Returns:
            True if successful
        """
        try:
            self.emulator.press_button('a')
            return True
        except Exception as e:
            logger.error(f"Error executing interact: {e}")
            return False
    
    def _execute_use_item(self, item_id: int) -> bool:
        """Execute using a field move/item.
        
        Args:
            item_id: ID of item/move to use
            
        Returns:
            True if successful
        """
        # TODO: Implement field move/item usage
        return False
    
    def load_map_data(self, map_id: int, collision_data: np.ndarray) -> None:
        """Load collision map data for a map.
        
        Args:
            map_id: Map identifier
            collision_data: 2D numpy array of collision data
        """
        self.map_data[map_id] = collision_data
        # Clear cached pathfinder to force recreation with new data
        self.pathfinders.pop(map_id, None)
        logger.info(f"Loaded collision data for map {map_id}")
    
    def clear_map_data(self) -> None:
        """Clear all stored map data."""
        self.map_data.clear()
        self.pathfinders.clear()
        logger.info("Cleared all map data") 