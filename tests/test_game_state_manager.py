"""
Tests for the Game State Manager

This module contains tests for the GameStateManager class.
"""

import unittest
from unittest.mock import Mock, patch
import tempfile
import os
import json
from datetime import datetime
from pathlib import Path

from src.emulator.interface import EmulatorInterface
from src.emulator.game_state import GameState, GameMode, BattleState
from src.game_state.manager import GameStateManager, Progress

class TestGameStateManager(unittest.TestCase):
    """Test cases for GameStateManager."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.mock_emulator = Mock(spec=EmulatorInterface)
        self.manager = GameStateManager(self.mock_emulator, self.temp_dir)
    
    def tearDown(self):
        """Clean up test environment."""
        for file in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, file))
        os.rmdir(self.temp_dir)
    
    def test_initialization(self):
        """Test game state manager initialization."""
        self.assertEqual(self.manager.emulator, self.mock_emulator)
        self.assertEqual(str(self.manager.save_dir), self.temp_dir)
        self.assertIsInstance(self.manager.progress, Progress)
        self.assertIsNone(self.manager.current_state)
        self.assertEqual(len(self.manager.state_history), 0)
    
    def test_update(self):
        """Test state update functionality."""
        # Create a test game state
        test_state = GameState(
            mode=GameMode.BATTLE,
            battle=BattleState(),
            success=True
        )
        
        # Mock emulator response
        self.mock_emulator.get_game_state.return_value = test_state
        
        # Update state
        self.manager.update()
        
        # Verify state was updated
        self.assertEqual(self.manager.current_state, test_state)
        self.assertEqual(len(self.manager.state_history), 1)
        self.assertEqual(self.manager.state_history[0], test_state)
    
    def test_save_progress(self):
        """Test progress saving functionality."""
        # Set up some progress
        self.manager.progress.badges = ["BOULDER", "CASCADE"]
        self.manager.progress.pokedex_caught = 50
        self.manager.progress.story_progress = "ROUTE_1"
        
        # Save to a specific slot
        result = self.manager.save_progress(slot=1)
        self.assertTrue(result)
        
        # Verify save file exists
        save_path = os.path.join(self.temp_dir, "progress_slot_1.json")
        self.assertTrue(os.path.exists(save_path))
        
        # Verify save contents
        with open(save_path, 'r') as f:
            save_data = json.load(f)
            self.assertEqual(save_data["progress"]["badges"], ["BOULDER", "CASCADE"])
            self.assertEqual(save_data["progress"]["pokedex_caught"], 50)
            self.assertEqual(save_data["progress"]["story_progress"], "ROUTE_1")
    
    def test_load_progress(self):
        """Test progress loading functionality."""
        # Create a test save file
        test_progress = {
            "progress": {
                "badges": ["BOULDER", "CASCADE"],
                "pokedex_caught": 50,
                "pokedex_seen": 75,
                "story_progress": "ROUTE_1",
                "current_objective": "DEFEAT_BROCK",
                "pokemon_levels": {"PIKACHU": 20},
                "play_time": 3600.0,
                "save_count": 1
            },
            "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "slot": 1
        }
        
        save_path = os.path.join(self.temp_dir, "progress_slot_1.json")
        with open(save_path, 'w') as f:
            json.dump(test_progress, f, indent=2)
        
        # Load progress
        result = self.manager.load_progress(slot=1)
        self.assertTrue(result)
        
        # Verify loaded progress
        self.assertEqual(self.manager.progress.badges, test_progress["progress"]["badges"])
        self.assertEqual(self.manager.progress.pokedex_caught, test_progress["progress"]["pokedex_caught"])
        self.assertEqual(self.manager.progress.story_progress, test_progress["progress"]["story_progress"])
    
    def test_state_history_limit(self):
        """Test state history size limiting."""
        # Create test states
        test_states = [
            GameState(mode=GameMode.OVERWORLD)
            for _ in range(self.manager.max_history + 10)
        ]
        
        # Add states to history
        for state in test_states:
            self.mock_emulator.get_game_state.return_value = state
            self.manager.update()
        
        # Verify history size is limited
        self.assertEqual(len(self.manager.state_history), self.manager.max_history)
        
        # Verify we have the most recent states
        self.assertEqual(
            self.manager.state_history[-1].mode,
            test_states[-1].mode
        )
    
    def test_get_objective(self):
        """Test objective getting."""
        test_objective = "DEFEAT_BROCK"
        self.manager.progress.current_objective = test_objective
        self.assertEqual(self.manager.get_objective(), test_objective)
    
    def test_set_objective(self):
        """Test objective setting."""
        test_objective = "DEFEAT_MISTY"
        self.manager.set_objective(test_objective)
        self.assertEqual(self.manager.progress.current_objective, test_objective)
    
    def test_get_summary(self):
        """Test progress summary generation."""
        # Set up test progress
        self.manager.progress.badges = ["BOULDER", "CASCADE"]
        self.manager.progress.pokedex_caught = 50
        self.manager.progress.pokedex_seen = 75
        self.manager.progress.story_progress = "ROUTE_1"
        self.manager.progress.pokemon_levels = {
            "PIKACHU": 100,
            "CHARIZARD": 50
        }
        self.manager.progress.play_time = 3600.0  # 1 hour
        
        # Get summary
        summary = self.manager.get_summary()
        
        # Verify summary contents
        self.assertEqual(summary["badges"], 2)
        self.assertEqual(summary["pokedex"]["caught"], 50)
        self.assertEqual(summary["pokedex"]["seen"], 75)
        self.assertEqual(summary["story"], "ROUTE_1")
        self.assertEqual(summary["pokemon_count"], 2)
        self.assertEqual(summary["max_level_count"], 1)
        self.assertEqual(summary["play_time"], "1.0 hours")
    
    def test_error_handling(self):
        """Test error handling in state management."""
        # Test save with invalid directory
        self.manager.save_dir = Path("/nonexistent/directory")
        result = self.manager.save_progress()
        self.assertFalse(result)
        
        # Test load with non-existent save
        result = self.manager.load_progress(slot=999)
        self.assertFalse(result)
        
        # Test update with emulator error
        self.mock_emulator.get_game_state.side_effect = Exception("Emulator error")
        try:
            self.manager.update()
        except Exception as e:
            self.fail(f"update() raised {type(e).__name__} unexpectedly!")

if __name__ == '__main__':
    unittest.main() 