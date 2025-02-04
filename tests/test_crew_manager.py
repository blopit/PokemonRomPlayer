"""
Tests for the Crew Manager

This module contains tests for the CrewManager class.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
from pathlib import Path
from typing import Dict, Any, Optional

from src.emulator.interface import EmulatorInterface
from src.emulator.game_state import GameState, GameMode, BattleState
from src.game_state.manager import GameStateManager
from src.agents.crew_manager import CrewManager
from src.agents.battle_agent import BattleAgent
from src.agents.base_agent import BaseAgent

class MockAgent(BaseAgent):
    """Mock agent for testing."""
    
    def __init__(self, emulator: EmulatorInterface, config: Dict[str, Any], can_handle_state: bool = False):
        """Initialize mock agent.
        
        Args:
            emulator: EmulatorInterface instance
            config: Configuration dictionary
            can_handle_state: Whether the agent can handle states
        """
        super().__init__("mock_agent", emulator)
        self.config = config
        self._can_handle_state = can_handle_state
        self.analyze_called = False
        self.execute_called = False
    
    def can_handle(self, state: GameState) -> bool:
        """Check if agent can handle state."""
        return self._can_handle_state
    
    def analyze_state(self, state: GameState) -> Optional[Dict[str, Any]]:
        """Analyze game state."""
        self.analyze_called = True
        return {"action": "test_action"}
    
    def execute_action(self, action_params: Dict[str, Any]) -> bool:
        """Execute action."""
        self.execute_called = True
        return True

class TestCrewManager(unittest.TestCase):
    """Test cases for CrewManager."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.mock_emulator = Mock(spec=EmulatorInterface)
        self.mock_state_manager = Mock(spec=GameStateManager)
        self.crew = CrewManager(self.mock_emulator, self.mock_state_manager)
    
    def tearDown(self):
        """Clean up test environment."""
        for file in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, file))
        os.rmdir(self.temp_dir)
    
    def test_initialization(self):
        """Test crew manager initialization."""
        self.assertEqual(self.crew.emulator, self.mock_emulator)
        self.assertEqual(self.crew.state_manager, self.mock_state_manager)
        self.assertIsNotNone(self.crew.agents)
        self.assertIsNone(self.crew.active_agent)
        self.assertIsNone(self.crew.last_state)
        
        # Verify default agents were initialized
        self.assertIn("battle", self.crew.agents)
        self.assertIsInstance(self.crew.agents["battle"], BattleAgent)
    
    def test_register_agent(self):
        """Test agent registration."""
        # Create a mock agent
        mock_agent = MockAgent(self.mock_emulator, {})
        
        # Register the agent
        self.crew.register_agent("test_agent", mock_agent)
        
        # Verify registration
        self.assertIn("test_agent", self.crew.agents)
        self.assertEqual(self.crew.agents["test_agent"], mock_agent)
    
    def test_unregister_agent(self):
        """Test agent unregistration."""
        # Create and register a mock agent
        mock_agent = MockAgent(self.mock_emulator, {})
        self.crew.register_agent("test_agent", mock_agent)
        
        # Unregister the agent
        self.crew.unregister_agent("test_agent")
        
        # Verify unregistration
        self.assertNotIn("test_agent", self.crew.agents)
    
    def test_get_appropriate_agent(self):
        """Test agent selection based on game state."""
        # Create mock agents
        battle_agent = MockAgent(self.mock_emulator, {}, True)
        battle_agent.can_handle = lambda state: state.mode == GameMode.BATTLE
        
        dialog_agent = MockAgent(self.mock_emulator, {}, True)
        dialog_agent.can_handle = lambda state: state.mode == GameMode.DIALOG
        
        # Register agents
        self.crew.register_agent("battle", battle_agent)
        self.crew.register_agent("dialog", dialog_agent)
        
        # Test battle state
        battle_state = GameState(mode=GameMode.BATTLE, battle=BattleState())
        agent = self.crew.get_appropriate_agent(battle_state)
        self.assertEqual(agent, battle_agent)
        
        # Test dialog state
        dialog_state = GameState(mode=GameMode.DIALOG)
        agent = self.crew.get_appropriate_agent(dialog_state)
        self.assertEqual(agent, dialog_agent)
        
        # Test unknown state
        unknown_state = GameState(mode=GameMode.UNKNOWN)
        agent = self.crew.get_appropriate_agent(unknown_state)
        self.assertIsNone(agent)
    
    def test_update_success(self):
        """Test successful update cycle."""
        # Set up test state
        test_state = GameState(mode=GameMode.BATTLE, battle=BattleState())
        self.mock_state_manager.current_state = test_state
        
        # Create mock agent
        mock_agent = MockAgent(self.mock_emulator, {})
        self.crew.register_agent("test_agent", mock_agent)
        
        # Perform update
        result = self.crew.update()
        
        # Verify update
        self.assertTrue(result)
        self.assertTrue(mock_agent.analyze_called)
        self.assertTrue(mock_agent.execute_called)
        self.assertEqual(self.crew.active_agent, mock_agent)
    
    def test_update_failure(self):
        """Test update cycle failure."""
        # Set up test state
        test_state = GameState(mode=GameMode.BATTLE, battle=BattleState())
        self.mock_state_manager.current_state = test_state
        
        # Create mock agent that fails
        mock_agent = MockAgent(self.mock_emulator, {}, True)
        mock_agent.analyze_state = MagicMock(return_value=None)
        self.crew.register_agent("test_agent", mock_agent)
        
        # Perform update
        result = self.crew.update()
        
        # Verify update
        self.assertFalse(result)
        self.assertTrue(mock_agent.analyze_called)
    
    def test_state_change_detection(self):
        """Test state change detection."""
        # Create initial state
        initial_state = GameState(mode=GameMode.OVERWORLD)
        self.crew.last_state = initial_state
        
        # Test with same state
        self.assertFalse(self.crew._state_changed(initial_state))
        
        # Test with different battle state
        new_state = GameState(mode=GameMode.BATTLE, battle=BattleState())
        self.assertTrue(self.crew._state_changed(new_state))
        
        # Test with different dialog state
        new_state = GameState(mode=GameMode.DIALOG)
        self.assertTrue(self.crew._state_changed(new_state))
        
        # Test with different menu state
        new_state = GameState(mode=GameMode.MENU)
        self.assertTrue(self.crew._state_changed(new_state))
    
    def test_get_status(self):
        """Test status retrieval."""
        # Create and activate a mock agent
        mock_agent = MockAgent(self.mock_emulator, {})
        self.crew.register_agent("test_agent", mock_agent)
        self.crew.active_agent = mock_agent
        
        # Mock state manager summary
        self.mock_state_manager.get_summary.return_value = {
            "test": "summary"
        }
        
        # Get status
        status = self.crew.get_status()
        
        # Verify status contents
        self.assertEqual(status["active_agent"], "MockAgent")
        self.assertIn("test_agent", status["registered_agents"])
        self.assertEqual(status["game_state"], {"test": "summary"})
    
    def test_error_handling(self):
        """Test error handling in crew management."""
        # Test update with state manager error
        self.mock_state_manager.update.side_effect = Exception("State manager error")
        result = self.crew.update()
        self.assertFalse(result)
        
        # Test update with agent error
        self.mock_state_manager.update.side_effect = None
        mock_agent = MockAgent(self.mock_emulator, {}, True)
        mock_agent.analyze_state = MagicMock(side_effect=Exception("Agent error"))
        self.crew.register_agent("test_agent", mock_agent)
        
        result = self.crew.update()
        self.assertFalse(result)
    
    def test_shutdown(self):
        """Test crew shutdown."""
        # Just ensure it doesn't raise any exceptions
        try:
            self.crew.shutdown()
        except Exception as e:
            self.fail(f"shutdown() raised {type(e).__name__} unexpectedly!")

if __name__ == '__main__':
    unittest.main() 