"""
Crew Manager Module

This module manages a crew of specialized agents for different tasks.
"""

from typing import Dict, List, Optional, Type, Any
from dataclasses import dataclass, field

from utils.logger import get_logger
from emulator.interface import EmulatorInterface
from emulator.game_state import GameState, GameMode
from game_state.manager import GameStateManager
from .base_agent import BaseAgent
from .battle_agent import BattleAgent

# Get logger for this module
logger = get_logger("agents")

@dataclass
class AgentPriority:
    """Priority configuration for different game modes."""
    battle: int = 100
    navigation: int = 50
    menu: int = 75
    dialog: int = 90

class CrewManager:
    """Manages a crew of specialized agents."""
    
    def __init__(self, emulator: EmulatorInterface, state_manager: GameStateManager):
        """Initialize the crew manager.
        
        Args:
            emulator: EmulatorInterface instance
            state_manager: GameStateManager instance
        """
        self.emulator = emulator
        self.state_manager = state_manager
        self.agents: Dict[str, BaseAgent] = {}
        self.priorities = AgentPriority()
        self.active_agent = None
        self.last_state = None
        
        # Initialize default agents
        self._init_default_agents()
        logger.info("Initialized CrewManager")
    
    def _init_default_agents(self):
        """Initialize default agents."""
        # Initialize battle agent
        battle_agent = BattleAgent("battle", self.emulator)
        self.register_agent("battle", battle_agent)
    
    def register_agent(self, name: str, agent: BaseAgent) -> None:
        """Register an agent.
        
        Args:
            name: Agent name/identifier
            agent: Agent instance
        """
        if name not in self.agents:
            self.agents[name] = agent
            logger.info(f"Registered agent: {name}")
    
    def unregister_agent(self, name: str) -> None:
        """Unregister an agent.
        
        Args:
            name: Agent name/identifier
        """
        if name in self.agents:
            del self.agents[name]
            logger.info(f"Unregistered agent: {name}")
    
    def get_appropriate_agent(self, state: GameState) -> Optional[BaseAgent]:
        """Get the most appropriate agent for the current state.
        
        Args:
            state: Current game state
            
        Returns:
            Most appropriate agent or None
        """
        # Check each agent in priority order
        for agent_name, agent in sorted(
            self.agents.items(),
            key=lambda x: self._get_priority_for_mode(state.mode)
        ):
            if agent.can_handle(state):
                return agent
        return None
    
    def update(self) -> bool:
        """Update the crew with the current game state.
        
        Returns:
            True if any agent took action
        """
        try:
            # Get current state
            state = self.state_manager.current_state
            
            # Check for state change
            if not self._state_changed(state):
                return False
                
            # Get appropriate agent
            agent = self.get_appropriate_agent(state)
            if not agent:
                return False
                
            # Update agent
            self.active_agent = agent
            return agent.update(state)
            
        except Exception as e:
            logger.error(f"Error in crew manager update: {e}")
            return False
    
    def _state_changed(self, state: GameState) -> bool:
        """Check if game state has changed significantly.
        
        Args:
            state: Current game state
            
        Returns:
            True if state has changed
        """
        if not self.last_state:
            self.last_state = state
            return True
            
        # Check for mode change
        if state.mode != self.last_state.mode:
            self.last_state = state
            return True
            
        # Check for battle state change
        if state.is_in_battle() != self.last_state.is_in_battle():
            self.last_state = state
            return True
            
        return False
    
    def _get_priority_for_mode(self, mode: GameMode) -> int:
        """Get priority value for a game mode.
        
        Args:
            mode: Game mode
            
        Returns:
            Priority value
        """
        if mode == GameMode.BATTLE:
            return self.priorities.battle
        elif mode == GameMode.DIALOG:
            return self.priorities.dialog
        elif mode == GameMode.MENU:
            return self.priorities.menu
        return 0
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the crew.
        
        Returns:
            Status dictionary
        """
        return {
            "active_agent": self.active_agent.__class__.__name__ if self.active_agent else None,
            "registered_agents": list(self.agents.keys()),
            "game_state": self.state_manager.get_summary() if self.state_manager else {}
        }
    
    def shutdown(self):
        """Clean up resources."""
        self.active_agent = None
        self.agents.clear()
        logger.info("Crew manager shut down") 