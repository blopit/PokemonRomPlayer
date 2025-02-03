from typing import Dict, List, Optional, Type
from dataclasses import dataclass, field

from utils.logger import logger
from utils.config_manager import AIConfig
from emulator.interface import EmulatorInterface
from emulator.game_state import GameState, GameMode
from .agent import Agent, AgentAction
from .battle_agent import BattleAgent, BattleStrategy
from .navigation_agent import NavigationAgent

@dataclass
class AgentPriority:
    """Priority configuration for different game modes."""
    battle: int = 100
    navigation: int = 50
    menu: int = 75
    dialog: int = 90

@dataclass
class AgentManager:
    """Manages and coordinates multiple AI agents."""
    
    emulator: EmulatorInterface
    config: AIConfig
    priorities: AgentPriority = field(default_factory=AgentPriority)
    
    def __post_init__(self):
        """Initialize agents after construction."""
        # Create agents
        self.battle_agent = BattleAgent(
            self.emulator,
            BattleStrategy(
                aggressive=(self.config.battle_strategy == "aggressive"),
                catch_wild=(self.config.catch_strategy == "all")
            )
        )
        
        self.navigation_agent = NavigationAgent(self.emulator)
        
        # Map game modes to agents
        self.mode_agents: Dict[GameMode, List[Agent]] = {
            GameMode.BATTLE: [self.battle_agent],
            GameMode.OVERWORLD: [self.navigation_agent],
            GameMode.MENU: [],  # TODO: Add menu agent
            GameMode.DIALOG: []  # TODO: Add dialog agent
        }
        
        logger.info("Initialized AgentManager with all agents")
    
    def update(self, state: GameState) -> bool:
        """Update all relevant agents with current game state.
        
        Args:
            state: Current game state
            
        Returns:
            True if any agent took action
        """
        try:
            # Get relevant agents for current mode
            active_agents = self.mode_agents.get(state.mode, [])
            if not active_agents:
                logger.debug(f"No agents registered for mode: {state.mode}")
                return False
            
            # Collect actions from all active agents
            actions = []
            for agent in active_agents:
                action = agent.analyze_state(state)
                if action is not None:
                    # Add mode-based priority bonus
                    if state.mode == GameMode.BATTLE:
                        action.priority += self.priorities.battle
                    elif state.mode == GameMode.OVERWORLD:
                        action.priority += self.priorities.navigation
                    elif state.mode == GameMode.MENU:
                        action.priority += self.priorities.menu
                    elif state.mode == GameMode.DIALOG:
                        action.priority += self.priorities.dialog
                    
                    actions.append((agent, action))
            
            if not actions:
                return False
            
            # Sort actions by priority (highest first)
            actions.sort(key=lambda x: x[1].priority, reverse=True)
            
            # Execute highest priority action
            agent, action = actions[0]
            logger.info(f"Executing {action.action_type} from {agent.name}")
            return agent.execute_action(action)
            
        except Exception as e:
            logger.error(f"Error in agent manager update: {e}")
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