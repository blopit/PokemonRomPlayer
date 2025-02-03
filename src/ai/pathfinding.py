from typing import List, Tuple, Set, Dict, Optional
import heapq
import numpy as np

from utils.logger import logger
from .navigation_agent import MapLocation

class Node:
    """A node in the pathfinding graph."""
    
    def __init__(self, x: int, y: int, g_cost: float = float('inf'), 
                 h_cost: float = 0.0, parent: Optional['Node'] = None):
        """Initialize a node.
        
        Args:
            x: X coordinate
            y: Y coordinate
            g_cost: Cost from start to this node
            h_cost: Estimated cost from this node to goal
            parent: Parent node in the path
        """
        self.x = x
        self.y = y
        self.g_cost = g_cost
        self.h_cost = h_cost
        self.parent = parent
    
    @property
    def f_cost(self) -> float:
        """Total estimated cost (g_cost + h_cost)."""
        return self.g_cost + self.h_cost
    
    def __lt__(self, other: 'Node') -> bool:
        """Compare nodes by f_cost for priority queue."""
        return self.f_cost < other.f_cost
    
    def __eq__(self, other: object) -> bool:
        """Compare nodes by position."""
        if not isinstance(other, Node):
            return NotImplemented
        return self.x == other.x and self.y == other.y
    
    def __hash__(self) -> int:
        """Hash node by position."""
        return hash((self.x, self.y))

class PathFinder:
    """A* pathfinding implementation."""
    
    # Movement costs
    STRAIGHT_COST = 1.0
    DIAGONAL_COST = 1.4  # sqrt(2)
    
    def __init__(self, collision_map: np.ndarray):
        """Initialize pathfinder.
        
        Args:
            collision_map: 2D numpy array where True indicates walkable tiles
        """
        self.collision_map = collision_map
        self.height, self.width = collision_map.shape
    
    def find_path(self, start: MapLocation, goal: MapLocation) -> List[Tuple[int, int]]:
        """Find a path from start to goal using A*.
        
        Args:
            start: Starting location
            goal: Goal location
            
        Returns:
            List of (x, y) coordinates forming the path
        """
        # Validate coordinates
        if not self._is_valid_position(start.x, start.y):
            logger.error(f"Invalid start position: ({start.x}, {start.y})")
            return []
        if not self._is_valid_position(goal.x, goal.y):
            logger.error(f"Invalid goal position: ({goal.x}, {goal.y})")
            return []
        
        # Initialize start node
        start_node = Node(start.x, start.y, g_cost=0.0, 
                         h_cost=self._calculate_h_cost(start.x, start.y, goal.x, goal.y))
        
        # Initialize open and closed sets
        open_set: List[Node] = [start_node]  # Priority queue
        closed_set: Set[Node] = set()
        
        # Track all nodes for updating
        all_nodes: Dict[Tuple[int, int], Node] = {(start.x, start.y): start_node}
        
        while open_set:
            # Get node with lowest f_cost
            current = heapq.heappop(open_set)
            
            # Check if we've reached the goal
            if current.x == goal.x and current.y == goal.y:
                return self._reconstruct_path(current)
            
            closed_set.add(current)
            
            # Check all neighbors
            for dx, dy in self._get_neighbors():
                new_x, new_y = current.x + dx, current.y + dy
                
                # Skip if position is invalid or not walkable
                if not self._is_valid_position(new_x, new_y):
                    continue
                if not self.collision_map[new_y, new_x]:
                    continue
                
                # Calculate cost to neighbor
                move_cost = self.DIAGONAL_COST if dx != 0 and dy != 0 else self.STRAIGHT_COST
                tentative_g_cost = current.g_cost + move_cost
                
                # Get or create neighbor node
                neighbor_pos = (new_x, new_y)
                if neighbor_pos not in all_nodes:
                    neighbor = Node(
                        new_x, new_y,
                        h_cost=self._calculate_h_cost(new_x, new_y, goal.x, goal.y)
                    )
                    all_nodes[neighbor_pos] = neighbor
                else:
                    neighbor = all_nodes[neighbor_pos]
                
                # Skip if we've found a better path already
                if neighbor in closed_set and tentative_g_cost >= neighbor.g_cost:
                    continue
                
                # Update neighbor if we found a better path
                if tentative_g_cost < neighbor.g_cost:
                    neighbor.parent = current
                    neighbor.g_cost = tentative_g_cost
                    
                    if neighbor not in open_set:
                        heapq.heappush(open_set, neighbor)
        
        logger.warning("No path found")
        return []
    
    def _is_valid_position(self, x: int, y: int) -> bool:
        """Check if a position is within map bounds.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            True if position is valid
        """
        return (0 <= x < self.width and 
                0 <= y < self.height)
    
    def _calculate_h_cost(self, x1: int, y1: int, x2: int, y2: int) -> float:
        """Calculate heuristic cost between two points.
        
        Uses Manhattan distance for better performance.
        
        Args:
            x1, y1: First point coordinates
            x2, y2: Second point coordinates
            
        Returns:
            Estimated cost between points
        """
        return abs(x2 - x1) + abs(y2 - y1)
    
    def _get_neighbors(self) -> List[Tuple[int, int]]:
        """Get relative coordinates of neighboring tiles.
        
        Returns:
            List of (dx, dy) tuples for adjacent tiles
        """
        # Only allow cardinal directions (no diagonals)
        return [(0, 1), (1, 0), (0, -1), (-1, 0)]
    
    def _reconstruct_path(self, end_node: Node) -> List[Tuple[int, int]]:
        """Reconstruct path from end node by following parent pointers.
        
        Args:
            end_node: Final node in path
            
        Returns:
            List of (x, y) coordinates from start to end
        """
        path = []
        current = end_node
        
        while current is not None:
            path.append((current.x, current.y))
            current = current.parent
        
        return list(reversed(path)) 