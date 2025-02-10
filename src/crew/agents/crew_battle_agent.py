"""
CrewAI Battle Agent

This module provides a CrewAI wrapper around the existing battle agent,
integrating it into the CrewAI task pipeline while preserving its core functionality.
"""

from typing import List, Dict, Any, Optional
from crewai import Agent
from utils.logger import get_logger
from ai.battle_agent import BattleAgent as CoreBattleAgent
from utils.command_queue import GameCommand

logger = get_logger("crew")

class CrewBattleAgent(Agent):
    """CrewAI wrapper for the battle management agent."""
    
    def __init__(self, 
                 name: str = "CrewBattleAgent",
                 goal: str = "Execute optimal battle strategies in Pokemon battles",
                 backstory: str = "Expert Pokemon battle strategist specializing in type matchups and move selection",
                 verbose: bool = True,
                 llm_provider: str = "openai"):
        """Initialize the CrewAI battle agent.
        
        Args:
            name: Agent name
            goal: Agent's primary goal
            backstory: Agent's background story
            verbose: Whether to enable verbose logging
            llm_provider: LLM provider to use
        """
        super().__init__(
            name=name,
            goal=goal,
            backstory=backstory,
            verbose=verbose
        )
        
        # Initialize core battle agent
        self.core_agent = CoreBattleAgent(provider=llm_provider)
        logger.info(f"Initialized {name} with {llm_provider} provider")
        
    def analyze_battle_state(self, screen_state: Dict[str, Any], game_state: Dict[str, Any]) -> bool:
        """Analyze if current state requires battle handling.
        
        Args:
            screen_state: Current screen analysis results
            game_state: Current game memory state
            
        Returns:
            True if battle state needs handling
        """
        return self.core_agent.can_handle(screen_state, game_state)
        
    def execute_battle_turn(self, 
                          screen_state: Dict[str, Any],
                          game_state: Dict[str, Any],
                          context: Optional[Dict[str, Any]] = None) -> List[GameCommand]:
        """Execute a battle turn using the core battle agent.
        
        Args:
            screen_state: Current screen analysis results
            game_state: Current game memory state
            context: Optional additional context
            
        Returns:
            List of game commands for the turn
        """
        try:
            # Generate commands using core agent
            commands = self.core_agent.generate_commands(
                screen_state=screen_state,
                game_state=game_state,
                context=context
            )
            
            if commands:
                logger.info(f"Generated {len(commands)} battle commands")
            else:
                logger.warning("No battle commands generated")
                
            return commands
            
        except Exception as e:
            logger.error(f"Error executing battle turn: {e}")
            return []
            
    def handle_error(self, error: Exception) -> None:
        """Handle errors during battle execution.
        
        Args:
            error: The error that occurred
        """
        logger.error(f"Battle agent error: {error}")
        # TODO: Implement error recovery strategies
        
    def __str__(self) -> str:
        """String representation of the agent.
        
        Returns:
            Agent description string
        """
        return f"{self.name} - Battle Strategy Expert" 