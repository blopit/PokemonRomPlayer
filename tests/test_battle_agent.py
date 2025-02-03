"""
Tests for the Battle Agent

This module contains tests for the BattleAgent class.
"""

import unittest
from unittest.mock import Mock, patch
from src.agents.battle_agent import BattleAgent
from src.emulator.interface import EmulatorInterface, GameState

class TestBattleAgent(unittest.TestCase):
    """Test cases for BattleAgent."""
    
    def setUp(self):
        """Set up test environment."""
        self.mock_emulator = Mock(spec=EmulatorInterface)
        self.config = {
            "strategy": "AGGRESSIVE",
            "switch_threshold": 0.2,
            "status_move_weight": 0.3
        }
        self.agent = BattleAgent(self.mock_emulator, self.config)
    
    def test_initialization(self):
        """Test battle agent initialization."""
        self.assertEqual(self.agent.emulator, self.mock_emulator)
        self.assertEqual(self.agent.config, self.config)
        self.assertEqual(self.agent.strategy, "AGGRESSIVE")
        self.assertIsNone(self.agent.current_battle)
    
    def test_can_handle(self):
        """Test state handling determination."""
        # Test battle state
        battle_state = GameState(in_battle=True)
        self.assertTrue(self.agent.can_handle(battle_state))
        
        # Test non-battle state
        normal_state = GameState(in_battle=False)
        self.assertFalse(self.agent.can_handle(normal_state))
    
    def test_calculate_move_score(self):
        """Test move scoring calculation."""
        # Set up test battle state
        self.agent.current_battle = {
            "opponent_pokemon": {"type": ["WATER"]}
        }
        
        # Test super effective move
        grass_move = {
            "power": 100,
            "type": "GRASS",
            "pp": 10,
            "category": "PHYSICAL"
        }
        grass_score = self.agent._calculate_move_score(grass_move)
        
        # Test not very effective move
        fire_move = {
            "power": 100,
            "type": "FIRE",
            "pp": 10,
            "category": "PHYSICAL"
        }
        fire_score = self.agent._calculate_move_score(fire_move)
        
        # Test status move
        status_move = {
            "power": 0,
            "type": "NORMAL",
            "pp": 10,
            "category": "STATUS"
        }
        status_score = self.agent._calculate_move_score(status_move)
        
        # Verify scores
        self.assertGreater(grass_score, fire_score)  # Super effective should score higher
        self.assertEqual(status_score, 0)  # Status moves currently score 0
    
    def test_get_best_move(self):
        """Test best move selection."""
        # Set up test battle state with moves
        self.agent.current_battle = {
            "opponent_pokemon": {"type": ["WATER"]},
            "available_moves": [
                {"power": 100, "type": "GRASS", "pp": 10, "category": "PHYSICAL"},
                {"power": 100, "type": "FIRE", "pp": 10, "category": "PHYSICAL"},
                {"power": 0, "type": "NORMAL", "pp": 10, "category": "STATUS"}
            ]
        }
        
        # Get best move
        best_move = self.agent._get_best_move()
        
        # Should select the Grass move (index 0)
        self.assertEqual(best_move, 0)
        
        # Test with no moves available
        self.agent.current_battle["available_moves"] = []
        self.assertIsNone(self.agent._get_best_move())
    
    def test_should_switch(self):
        """Test Pokemon switching decision."""
        # Test low HP scenario
        self.agent.current_battle = {
            "active_pokemon": {"hp_percent": 15, "type": ["FIRE"]},
            "opponent_pokemon": {"type": ["WATER"]}
        }
        self.assertTrue(self.agent._should_switch())
        
        # Test healthy HP but type disadvantage
        self.agent.current_battle["active_pokemon"]["hp_percent"] = 100
        self.assertTrue(self.agent._should_switch())
        
        # Test healthy HP and no type disadvantage
        self.agent.current_battle["active_pokemon"]["type"] = ["GRASS"]
        self.assertFalse(self.agent._should_switch())
    
    def test_act_battle_sequence(self):
        """Test full battle action sequence."""
        # Set up game state
        battle_state = GameState(in_battle=True)
        
        # Set up battle scenario
        self.agent.current_battle = {
            "active_pokemon": {"hp_percent": 100, "type": ["GRASS"]},
            "opponent_pokemon": {"type": ["WATER"]},
            "available_moves": [
                {"power": 100, "type": "GRASS", "pp": 10, "category": "PHYSICAL"}
            ]
        }
        
        # Mock emulator responses
        self.mock_emulator.press_button.return_value = None
        
        # Test battle action
        result = self.agent.act(battle_state)
        self.assertTrue(result)
        
        # Test with no valid moves
        self.agent.current_battle["available_moves"] = []
        result = self.agent.act(battle_state)
        self.assertFalse(result)
    
    def test_error_handling(self):
        """Test error handling in battle actions."""
        battle_state = GameState(in_battle=True)
        
        # Test with None battle state
        self.agent.current_battle = None
        result = self.agent.act(battle_state)
        self.assertFalse(result)
        
        # Test with emulator error
        self.mock_emulator.press_button.side_effect = Exception("Emulator error")
        result = self.agent.act(battle_state)
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main() 