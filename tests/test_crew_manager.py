"""
Tests for the Crew Manager

This module contains tests for the CrewManager class.
"""

import unittest
from unittest.mock import Mock, patch
import tempfile
import os
from pathlib import Path

from src.emulator.interface import EmulatorInterface, GameState
from src.game_state.manager import GameStateManager
from src.agents.crew_manager import CrewManager
from src.agents.battle_agent import BattleAgent
from src.agents.base_agent import BaseAgent

class MockAgent(BaseAgent):
    """Mock agent for testing."""
    
    def __init__(self, *args, can_handle_state=False, act_success=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.can_handle_state = can_handle_state
        self.act_success = act_success
        self.act_called = False
    
    def can_handle(self, state):
        return self.can_handle_state
    
    def act(self, state):
        self.act_called = True
        return self.act_success

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
        self.assertIsInstance(self.crew.agents, dict)
        self.assertIsNone(self.crew.active_agent)
        
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
        """Test agent selection."""
        # Create test state
        test_state = GameState()
        
        # Create mock agents with different capabilities
        agent1 = MockAgent(self.mock_emulator, {}, can_handle_state=True)
        agent2 = MockAgent(self.mock_emulator, {}, can_handle_state=False)
        
        # Register agents
        self.crew.register_agent("agent1", agent1)
        self.crew.register_agent("agent2", agent2)
        
        # Get appropriate agent
        selected_agent = self.crew.get_appropriate_agent(test_state)
        
        # Verify selection
        self.assertEqual(selected_agent, agent1)
    
    def test_update_success(self):
        """Test successful update cycle."""
        # Set up test state
        test_state = GameState(in_battle=True)
        self.mock_state_manager.current_state = test_state
        
        # Create mock agent
        mock_agent = MockAgent(
            self.mock_emulator,
            {},
            can_handle_state=True,
            act_success=True
        )
        self.crew.register_agent("test_agent", mock_agent)
        
        # Perform update
        result = self.crew.update()
        
        # Verify update
        self.assertTrue(result)
        self.assertTrue(mock_agent.act_called)
        self.assertEqual(self.crew.active_agent, mock_agent)
    
    def test_update_failure(self):
        """Test update cycle failure."""
        # Set up test state
        test_state = GameState(in_battle=True)
        self.mock_state_manager.current_state = test_state
        
        # Create mock agent that fails
        mock_agent = MockAgent(
            self.mock_emulator,
            {},
            can_handle_state=True,
            act_success=False
        )
        self.crew.register_agent("test_agent", mock_agent)
        
        # Perform update
        result = self.crew.update()
        
        # Verify update
        self.assertFalse(result)
        self.assertTrue(mock_agent.act_called)
    
    def test_state_change_detection(self):
        """Test state change detection."""
        # Create initial state
        initial_state = GameState(
            in_battle=False,
            in_menu=False,
            current_map=1
        )
        self.crew.last_state = initial_state
        
        # Test with same state
        self.assertFalse(self.crew._state_changed(initial_state))
        
        # Test with different battle state
        new_state = GameState(
            in_battle=True,
            in_menu=False,
            current_map=1
        )
        self.assertTrue(self.crew._state_changed(new_state))
        
        # Test with different menu state
        new_state = GameState(
            in_battle=False,
            in_menu=True,
            current_map=1
        )
        self.assertTrue(self.crew._state_changed(new_state))
        
        # Test with different map
        new_state = GameState(
            in_battle=False,
            in_menu=False,
            current_map=2
        )
        self.assertTrue(self.crew._state_changed(new_state))
    
    def test_get_status(self):
        """Test status reporting."""
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
        mock_agent = MockAgent(
            self.mock_emulator,
            {},
            can_handle_state=True
        )
        mock_agent.act = Mock(side_effect=Exception("Agent error"))
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