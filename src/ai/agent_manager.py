"""
Agent Manager Module

This module manages AI agents and their interactions with the game.
"""

from typing import Dict, List, Optional, Type
from dataclasses import dataclass, field

from utils.logger import get_logger
from utils.config_manager import AIConfig
from emulator.interface import EmulatorInterface
from emulator.game_state import GameState, GameMode
from .agent import Agent, AgentAction
from .battle_agent import BattleAgent, BattleStrategy
from .navigation_agent import NavigationAgent, NavigationMode

# Get logger for this module
logger = get_logger("ai")

@dataclass
class AgentPriority:
    """Priority configuration for different game modes."""
    battle: int = 100
    navigation: int = 50
    menu: int = 75
    dialog: int = 90

@dataclass
class AIConfig:
    """Configuration for AI behavior."""
    battle_strategy: BattleStrategy = BattleStrategy.BALANCED
    navigation_mode: NavigationMode = NavigationMode.EXPLORE
    switch_threshold: float = 0.3
    status_move_weight: float = 0.4

@dataclass
class AgentManager:
    """Manages AI agents and their interactions with the game."""
    
    emulator: EmulatorInterface
    config: Dict = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize agents after dataclass initialization."""
        # Parse configuration
        ai_config = AIConfig()
        if "battle_strategy" in self.config:
            try:
                ai_config.battle_strategy = BattleStrategy[self.config["battle_strategy"].upper()]
            except KeyError:
                logger.warning(f"Invalid battle strategy: {self.config['battle_strategy']}")
        
        if "navigation_mode" in self.config:
            try:
                ai_config.navigation_mode = NavigationMode[self.config["navigation_mode"].upper()]
            except KeyError:
                logger.warning(f"Invalid navigation mode: {self.config['navigation_mode']}")
        
        ai_config.switch_threshold = self.config.get("switch_threshold", 0.3)
        ai_config.status_move_weight = self.config.get("status_move_weight", 0.4)
        
        # Initialize agents
        self.battle_agent = BattleAgent(
            name="BattleAgent",
            emulator=self.emulator,
            strategy=ai_config.battle_strategy,
            switch_threshold=ai_config.switch_threshold,
            status_move_weight=ai_config.status_move_weight
        )
        
        self.navigation_agent = NavigationAgent(
            name="NavigationAgent",
            emulator=self.emulator,
            mode=ai_config.navigation_mode
        )
        
        logger.info("Initialized AgentManager")
    
    def update(self, state: GameState) -> bool:
        """Update agents with current game state.
        
        Args:
            state: Current game state
            
        Returns:
            True if any agent took action
        """
        try:
            # Select appropriate agent based on game mode
            if state.mode == GameMode.BATTLE:
                return self.battle_agent.update(state)
            elif state.mode == GameMode.OVERWORLD:
                return self.navigation_agent.update(state)
            else:
                logger.debug(f"No agent available for mode: {state.mode}")
                return False
            
        except Exception as e:
            logger.error(f"Error in agent update: {e}")
            return False
    
    def register_agent(self, mode: GameMode, agent: Agent) -> None:
        """Register a new agent for a game mode.
        
        Args:
            mode: Game mode to register for
            agent: Agent to register
        """
        if mode not in self.mode_agents:
            self.mode_agents[mode] = []
        
        if agent not in self.mode_agents[mode]:
            self.mode_agents[mode].append(agent)
            logger.info(f"Registered {agent.name} for {mode}")
    
    def unregister_agent(self, mode: GameMode, agent: Agent) -> None:
        """Unregister an agent from a game mode.
        
        Args:
            mode: Game mode to unregister from
            agent: Agent to unregister
        """
        if mode in self.mode_agents and agent in self.mode_agents[mode]:
            self.mode_agents[mode].remove(agent)
            logger.info(f"Unregistered {agent.name} from {mode}")
    
    def get_agent(self, agent_type: Type[Agent]) -> Optional[Agent]:
        """Get an agent of the specified type.
        
        Args:
            agent_type: Type of agent to get
            
        Returns:
            Agent instance if found, None otherwise
        """
        for agents in self.mode_agents.values():
            for agent in agents:
                if isinstance(agent, agent_type):
                    return agent
        return None
    
    def set_navigation_target(self, target_location: str) -> bool:
        """Set a new navigation target.
        
        Args:
            target_location: Name or description of target location
            
        Returns:
            True if target was set successfully
        """
        nav_agent = self.get_agent(NavigationAgent)
        if nav_agent is None:
            logger.error("No navigation agent registered")
            return False
        
        # TODO: Convert location name to MapLocation
        return False
    
    def handle_error(self, error: Exception) -> None:
        """Handle an error that occurred during agent management.
        
        Args:
            error: Exception that occurred
        """
        logger.error(f"Agent manager error: {error}")
        # TODO: Implement error recovery strategies 