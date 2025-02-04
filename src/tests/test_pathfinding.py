"""
Tests for the pathfinding module.
"""

import unittest
from pathlib import Path
import sys

# Add src directory to Python path
src_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(src_dir))

from ai.pathfinding import PathFinder
from ai.navigation_agent import MapLocation

class TestPathFinder(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.pathfinder = PathFinder()
        
        # Create test locations
        self.loc_a = MapLocation("A", 0, 0, "map1")
        self.loc_b = MapLocation("B", 1, 0, "map1")
        self.loc_c = MapLocation("C", 0, 1, "map1")
        self.loc_d = MapLocation("D", 1, 1, "map1")
        
        # Add connections
        self.loc_a.connections = ["B", "C"]
        self.loc_b.connections = ["A", "D"]
        self.loc_c.connections = ["A", "D"]
        self.loc_d.connections = ["B", "C"]
        
        # Add locations to pathfinder
        for loc in [self.loc_a, self.loc_b, self.loc_c, self.loc_d]:
            self.pathfinder.add_location(loc)

    def test_add_location(self):
        """Test adding locations."""
        # New location
        loc_e = MapLocation("E", 2, 0, "map1")
        self.pathfinder.add_location(loc_e)
        self.assertIn(loc_e, self.pathfinder.known_locations["map1"])
        
        # Duplicate location
        self.pathfinder.add_location(self.loc_a)
        count = sum(1 for loc in self.pathfinder.known_locations["map1"] 
                   if loc == self.loc_a)
        self.assertEqual(count, 1)

    def test_get_neighbors(self):
        """Test getting neighboring locations."""
        neighbors = self.pathfinder.get_neighbors(self.loc_a)
        self.assertEqual(len(neighbors), 2)
        self.assertIn(self.loc_b, neighbors)
        self.assertIn(self.loc_c, neighbors)

    def test_find_path_same_location(self):
        """Test finding path when start equals goal."""
        path = self.pathfinder.find_path(self.loc_a, self.loc_a)
        self.assertEqual(len(path), 1)
        self.assertEqual(path[0], self.loc_a)

    def test_find_path_adjacent(self):
        """Test finding path between adjacent locations."""
        path = self.pathfinder.find_path(self.loc_a, self.loc_b)
        self.assertEqual(len(path), 2)
        self.assertEqual(path[0], self.loc_a)
        self.assertEqual(path[1], self.loc_b)

    def test_find_path_diagonal(self):
        """Test finding path between diagonal locations."""
        path = self.pathfinder.find_path(self.loc_a, self.loc_d)
        self.assertEqual(len(path), 3)
        self.assertEqual(path[0], self.loc_a)
        self.assertIn(path[1], [self.loc_b, self.loc_c])
        self.assertEqual(path[2], self.loc_d)

    def test_find_path_different_maps(self):
        """Test finding path between locations on different maps."""
        loc_x = MapLocation("X", 0, 0, "map2", connections=["A"])
        loc_y = MapLocation("Y", 1, 0, "map2", connections=["B"])
        self.loc_a.connections.append("X")
        self.loc_b.connections.append("Y")
        
        self.pathfinder.add_location(loc_x)
        self.pathfinder.add_location(loc_y)
        
        path = self.pathfinder.find_path(self.loc_a, loc_y)
        self.assertIsNotNone(path)
        self.assertEqual(path[0], self.loc_a)
        self.assertEqual(path[-1], loc_y)

    def test_get_next_move(self):
        """Test getting next movement action."""
        # Move right
        move = self.pathfinder.get_next_move(self.loc_a, self.loc_b)
        self.assertEqual(move, "MOVE_RIGHT")
        
        # Move down
        move = self.pathfinder.get_next_move(self.loc_a, self.loc_c)
        self.assertEqual(move, "MOVE_DOWN")
        
        # No move needed
        move = self.pathfinder.get_next_move(self.loc_a, self.loc_a)
        self.assertIsNone(move)
        
        # No path exists
        unreachable = MapLocation("Z", 10, 10, "map3")
        move = self.pathfinder.get_next_move(self.loc_a, unreachable)
        self.assertIsNone(move)

if __name__ == '__main__':
    unittest.main() 