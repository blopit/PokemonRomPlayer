"""
Crew Manager Module

This module manages and orchestrates all AI agents in the system.
It determines which agent should handle the current game state and manages transitions.
"""

import logging
from typing import Dict, List, Optional, Type
from .base_agent import BaseAgent
from .battle_agent import BattleAgent
from ..emulator.interface import EmulatorInterface, GameState
from ..game_state.manager import GameStateManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CrewManager:
    """Manages and orchestrates all AI agents."""
    
    def __init__(self, emulator: EmulatorInterface, state_manager: GameStateManager):
        """
        Initialize the crew manager.
        
        Args:
            emulator: Interface to the GBA emulator
            state_manager: Game state manager
        """
        self.emulator = emulator
        self.state_manager = state_manager
        self.agents: Dict[str, BaseAgent] = {}
        self.active_agent: Optional[BaseAgent] = None
        self.last_state = None
        logger.info("Initializing Crew Manager")
        
        # Initialize default agents
        self._init_default_agents()
    
    def _init_default_agents(self) -> None:
        """Initialize the default set of agents."""
        # Battle Agent
        self.register_agent(
            "battle",
            BattleAgent(
                self.emulator,
                {
                    "strategy": "AGGRESSIVE",
                    "switch_threshold": 0.2,
                    "status_move_weight": 0.3
                }
            )
        )
        
        # TODO: Add more agents
        # - Navigation Agent
        # - Story Progress Agent
        # - Pokemon Catching Agent
        # - Training Agent
        # - Menu Navigation Agent
        
        logger.info(f"Initialized {len(self.agents)} default agents")
    
    def register_agent(self, name: str, agent: BaseAgent) -> None:
        """
        Register a new agent with the crew.
        
        Args:
            name: Name identifier for the agent
            agent: Agent instance to register
        """
        self.agents[name] = agent
        logger.info(f"Registered agent: {name}")
    
    def unregister_agent(self, name: str) -> None:
        """
        Remove an agent from the crew.
        
        Args:
            name: Name of the agent to remove
        """
        if name in self.agents:
            del self.agents[name]
            logger.info(f"Unregistered agent: {name}")
    
    def get_appropriate_agent(self, state: GameState) -> Optional[BaseAgent]:
        """
        Determine which agent should handle the current state.
        
        Args:
            state: Current game state
            
        Returns:
            Most appropriate agent for the state or None if no agent can handle it
        """
        candidates = []
        
        for name, agent in self.agents.items():
            if agent.can_handle(state):
                candidates.append((name, agent))
        
        if not candidates:
            return None
        
        # TODO: Implement more sophisticated agent selection
        # For now, just return the first capable agent
        logger.debug(f"Selected agent: {candidates[0][0]}")
        return candidates[0][1]
    
    def update(self) -> bool:
        """
        Update the crew's state and execute appropriate agent actions.
        
        Returns:
            True if update was successful
        """
        try:
            # Update game state
            self.state_manager.update()
            current_state = self.state_manager.current_state
            
            # Check for state changes
            if self._state_changed(current_state):
                self._handle_state_change(current_state)
            
            # Get appropriate agent
            agent = self.get_appropriate_agent(current_state)
            
            if agent is not None:
                if agent != self.active_agent:
                    logger.info(f"Switching to agent: {agent.__class__.__name__}")
                    self.active_agent = agent
                
                # Execute agent action
                success = agent.act(current_state)
                if not success:
                    logger.warning(f"Agent {agent.__class__.__name__} action failed")
                return success
            else:
                logger.warning("No agent available to handle current state")
                return False
                
        except Exception as e:
            logger.error(f"Error in crew update: {e}")
            return False
    
    def _state_changed(self, current_state: GameState) -> bool:
        """
        Check if the game state has significantly changed.
        
        Args:
            current_state: Current game state
            
        Returns:
            True if state has significantly changed
        """
        if self.last_state is None:
            return True
            
        # TODO: Implement more sophisticated state change detection
        # For now, just check basic state changes
        changed = (
            current_state.in_battle != self.last_state.in_battle or
            current_state.in_menu != self.last_state.in_menu or
            current_state.current_map != self.last_state.current_map
        )
        
        self.last_state = current_state
        return changed
    
    def _handle_state_change(self, new_state: GameState) -> None:
        """
        Handle a significant state change.
        
        Args:
            new_state: New game state
        """
        logger.info("Game state changed")
        # TODO: Implement state change handling
        # - Save progress if appropriate
        # - Update objectives
        # - Notify agents of state change
    
    def get_status(self) -> Dict:
        """
        Get the current status of the crew.
        
        Returns:
            Dictionary containing crew status information
        """
        return {
            "active_agent": self.active_agent.__class__.__name__ if self.active_agent else None,
            "registered_agents": list(self.agents.keys()),
            "game_state": self.state_manager.get_summary()
        }
    
    def shutdown(self) -> None:
        """Clean up and shut down the crew."""
        logger.info("Shutting down Crew Manager")
        # TODO: Implement cleanup
        # - Save final progress
        # - Clean up agents
        # - Close emulator 