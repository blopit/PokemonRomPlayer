"""
Tests for the Battle Agent

This module contains tests for the BattleAgent class.
"""

import unittest
from unittest.mock import Mock
from src.emulator.interface import EmulatorInterface
from src.emulator.game_state import GameState, GameMode, BattleState
from src.agents.battle_agent import BattleAgent

class TestBattleAgent(unittest.TestCase):
    """Test cases for BattleAgent."""
    
    def setUp(self):
        """Set up test environment."""
        self.mock_emulator = Mock(spec=EmulatorInterface)
        self.agent = BattleAgent("test", self.mock_emulator)
    
    def test_initialization(self):
        """Test battle agent initialization."""
        self.assertEqual(self.agent.name, "test")
        self.assertEqual(self.agent.emulator, self.mock_emulator)
        self.assertEqual(self.agent.strategy, "AGGRESSIVE")
        self.assertIsNone(self.agent.current_battle)
    
    def test_can_handle(self):
        """Test state handling determination."""
        # Test battle state
        battle_state = GameState(mode=GameMode.BATTLE, battle=BattleState())
        self.assertTrue(self.agent.can_handle(battle_state))
        
        # Test non-battle state
        normal_state = GameState(mode=GameMode.OVERWORLD)
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
    
    def test_battle_sequence(self):
        """Test full battle action sequence."""
        # Set up game state
        battle_state = GameState(
            mode=GameMode.BATTLE,
            battle=BattleState(
                player_pokemon={"hp_percent": 100, "type": ["GRASS"]},
                opponent_pokemon={"type": ["WATER"]},
                available_moves=[
                    {"power": 100, "type": "GRASS", "pp": 10, "category": "PHYSICAL"}
                ]
            )
        )
        
        # Test analyze_state
        action = self.agent.analyze_state(battle_state)
        self.assertIsNotNone(action)
        self.assertEqual(action["action"], "move")
        self.assertEqual(action["move_index"], 0)  # Should choose Grass move
        
        # Test execute_action
        result = self.agent.execute_action(action)
        self.assertTrue(result)
        self.mock_emulator.press_button.assert_called()
    
    def test_error_handling(self):
        """Test error handling in battle actions."""
        # Set up game state
        battle_state = GameState(
            mode=GameMode.BATTLE,
            battle=BattleState(
                player_pokemon={"hp_percent": 100},
                opponent_pokemon={"type": ["WATER"]},
                available_moves=[]  # No moves available
            )
        )
        
        # Test analyze_state with no moves
        action = self.agent.analyze_state(battle_state)
        self.assertIsNone(action)
        
        # Test execute_action with emulator error
        self.mock_emulator.press_button.side_effect = Exception("Emulator error")
        result = self.agent.execute_action({"action": "move", "move_index": 0})
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main() 