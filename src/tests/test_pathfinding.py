import unittest
import numpy as np

from ai.pathfinding import PathFinder
from ai.navigation_agent import MapLocation

class TestPathFinder(unittest.TestCase):
    """Test cases for the PathFinder class."""
    
    def setUp(self):
        """Set up test cases."""
        # Create a simple test map
        # 1 = walkable, 0 = wall
        self.test_map = np.array([
            [1, 1, 1, 1, 1],
            [1, 0, 0, 0, 1],
            [1, 1, 1, 1, 1],
            [1, 0, 0, 0, 1],
            [1, 1, 1, 1, 1]
        ], dtype=bool)
        
        self.pathfinder = PathFinder(self.test_map)
    
    def test_direct_path(self):
        """Test finding a direct path with no obstacles."""
        start = MapLocation(0, 0, 0)
        goal = MapLocation(4, 0, 0)
        
        path = self.pathfinder.find_path(start, goal)
        
        self.assertEqual(len(path), 5)
        self.assertEqual(path[0], (0, 0))
        self.assertEqual(path[-1], (4, 0))
    
    def test_path_around_obstacle(self):
        """Test finding a path around obstacles."""
        start = MapLocation(0, 1, 0)
        goal = MapLocation(4, 1, 0)
        
        path = self.pathfinder.find_path(start, goal)
        
        # Path should go around the wall
        self.assertTrue(len(path) > 5)  # Longer than direct path
        self.assertEqual(path[0], (0, 1))
        self.assertEqual(path[-1], (4, 1))
    
    def test_no_path_possible(self):
        """Test when no path is possible."""
        # Create a map with no valid path
        blocked_map = np.zeros((5, 5), dtype=bool)
        blocked_map[0, 0] = True
        blocked_map[4, 4] = True
        
        pathfinder = PathFinder(blocked_map)
        start = MapLocation(0, 0, 0)
        goal = MapLocation(4, 4, 0)
        
        path = pathfinder.find_path(start, goal)
        self.assertEqual(len(path), 0)
    
    def test_invalid_coordinates(self):
        """Test handling of invalid coordinates."""
        start = MapLocation(-1, 0, 0)
        goal = MapLocation(0, 0, 0)
        
        path = self.pathfinder.find_path(start, goal)
        self.assertEqual(len(path), 0)
        
        start = MapLocation(0, 0, 0)
        goal = MapLocation(10, 0, 0)
        
        path = self.pathfinder.find_path(start, goal)
        self.assertEqual(len(path), 0)
    
    def test_path_optimality(self):
        """Test that the path found is optimal (shortest possible)."""
        # Create a map with multiple possible paths
        multi_path_map = np.ones((5, 5), dtype=bool)
        pathfinder = PathFinder(multi_path_map)
        
        start = MapLocation(0, 0, 0)
        goal = MapLocation(4, 4, 0)
        
        path = pathfinder.find_path(start, goal)
        
        # Manhattan distance is optimal for grid movement
        optimal_length = abs(goal.x - start.x) + abs(goal.y - start.y) + 1
        self.assertEqual(len(path), optimal_length)
    
    def test_diagonal_movement_disabled(self):
        """Test that diagonal movement is not allowed."""
        start = MapLocation(0, 0, 0)
        goal = MapLocation(1, 1, 0)
        
        path = self.pathfinder.find_path(start, goal)
        
        # Path should be 3 steps (right, down) or (down, right)
        self.assertEqual(len(path), 3)
        # Check that each step only moves in one direction
        for i in range(len(path) - 1):
            dx = abs(path[i+1][0] - path[i][0])
            dy = abs(path[i+1][1] - path[i][1])
            self.assertTrue((dx == 1 and dy == 0) or (dx == 0 and dy == 1))

if __name__ == '__main__':
    unittest.main() 