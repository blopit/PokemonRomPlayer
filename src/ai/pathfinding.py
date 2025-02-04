"""
Pathfinding Module

This module implements pathfinding algorithms for navigation.
"""

import heapq
from typing import List, Dict, Set, Optional
import logging

from .navigation_agent import MapLocation

logger = logging.getLogger(__name__)

class PathFinder:
    """A* pathfinding implementation."""
    
    def __init__(self):
        """Initialize pathfinder."""
        self.known_locations = {}  # Map ID -> List[MapLocation]
        
    def add_location(self, location: MapLocation):
        """Add a location to the known locations.
        
        Args:
            location: Location to add
        """
        if location.map_id not in self.known_locations:
            self.known_locations[location.map_id] = []
        if location not in self.known_locations[location.map_id]:
            self.known_locations[location.map_id].append(location)
            
    def get_neighbors(self, location: MapLocation) -> List[MapLocation]:
        """Get neighboring locations.
        
        Args:
            location: Current location
            
        Returns:
            List of neighboring locations
        """
        neighbors = []
        
        # Same map neighbors
        for loc in self.known_locations.get(location.map_id, []):
            if loc != location and loc.distance_to(location) == 1:
                neighbors.append(loc)
                
        # Connected map neighbors
        for map_id, locations in self.known_locations.items():
            if map_id != location.map_id:
                for loc in locations:
                    if loc.name in location.connections:
                        neighbors.append(loc)
                        
        return neighbors
        
    def find_path(self, start: MapLocation, goal: MapLocation) -> Optional[List[MapLocation]]:
        """Find path between two locations using A*.
        
        Args:
            start: Starting location
            goal: Target location
            
        Returns:
            List of locations forming the path, or None if no path exists
        """
        if not start or not goal:
            return None
            
        # A* algorithm
        frontier = [(0, start)]  # Priority queue of (f_score, location)
        came_from = {start: None}
        g_score = {start: 0}  # Cost from start
        f_score = {start: start.distance_to(goal)}  # Estimated total cost
        
        while frontier:
            current = heapq.heappop(frontier)[1]
            
            if current == goal:
                # Reconstruct path
                path = []
                while current:
                    path.append(current)
                    current = came_from[current]
                path.reverse()
                return path
                
            for neighbor in self.get_neighbors(current):
                tentative_g = g_score[current] + current.distance_to(neighbor)
                
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f = tentative_g + neighbor.distance_to(goal)
                    f_score[neighbor] = f
                    heapq.heappush(frontier, (f, neighbor))
                    
        return None  # No path found
        
    def get_next_move(self, current: MapLocation, target: MapLocation) -> Optional[str]:
        """Get next movement action towards target.
        
        Args:
            current: Current location
            target: Target location
            
        Returns:
            Movement action or None if no move needed/possible
        """
        path = self.find_path(current, target)
        if not path or len(path) < 2:
            return None
            
        next_loc = path[1]
        dx = next_loc.x - current.x
        dy = next_loc.y - current.y
        
        if dx > 0:
            return "MOVE_RIGHT"
        elif dx < 0:
            return "MOVE_LEFT"
        elif dy > 0:
            return "MOVE_DOWN"
        elif dy < 0:
            return "MOVE_UP"
        else:
            return None 