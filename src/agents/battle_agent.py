"""
Battle Agent Module

This module contains the BattleAgent class for handling Pokemon battles.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from .base_agent import BaseAgent
from ..emulator.interface import GameState
from src.emulator.interface import EmulatorInterface
from src.emulator.game_state import GameMode

# Configure logging
logger = logging.getLogger("pokemon_player")

# Type effectiveness chart (simplified for example)
TYPE_CHART = {
    "NORMAL": {"ROCK": 0.5, "GHOST": 0, "STEEL": 0.5},
    "FIRE": {"FIRE": 0.5, "WATER": 0.5, "GRASS": 2, "ICE": 2, "BUG": 2, "ROCK": 0.5, "DRAGON": 0.5, "STEEL": 2},
    "WATER": {"FIRE": 2, "WATER": 0.5, "GRASS": 0.5, "GROUND": 2, "ROCK": 2, "DRAGON": 0.5},
    # Add more type matchups as needed
}

class BattleAgent(BaseAgent):
    """Agent responsible for handling Pokemon battles."""
    
    def __init__(self, name: str, emulator: EmulatorInterface):
        """Initialize the battle agent.
        
        Args:
            name: The name of the agent
            emulator: The emulator interface to use
        """
        super().__init__(name, emulator)
        self.strategy = "AGGRESSIVE"
        self.current_battle = None
        self.logger = logger
        logger.info(f"Battle Agent initialized with strategy: {self.strategy}")
    
    def can_handle(self, state: GameState) -> bool:
        """Check if this agent can handle the current game state.
        
        Args:
            state: The current game state
            
        Returns:
            bool: True if the agent can handle this state
        """
        return state.is_in_battle()
    
    def analyze_state(self, state: GameState) -> Optional[Dict[str, Any]]:
        """Analyze the current battle state and decide on an action.
        
        Args:
            state: The current game state
            
        Returns:
            Optional[Dict[str, Any]]: The action to take, or None if no valid action
        """
        if not state.battle:
            return None

        self.current_battle = {
            "active_pokemon": state.battle.player_pokemon,
            "opponent_pokemon": state.battle.opponent_pokemon,
            "available_moves": state.battle.available_moves
        }

        if self._should_switch():
            return {"action": "switch", "target": self._get_best_switch_target()}

        move_index = self._get_best_move()
        if move_index is not None:
            return {"action": "move", "move_index": move_index}

        return None
    
    def execute_action(self, action: Dict[str, Any]) -> bool:
        """Execute the chosen battle action.
        
        Args:
            action: The action to execute
            
        Returns:
            bool: True if action was executed successfully
        """
        try:
            if action["action"] == "move":
                self._execute_move(action["move_index"])
            elif action["action"] == "switch":
                self._execute_switch(action["target"])
            return True
        except Exception as e:
            self.logger.error(f"Error executing battle action: {e}")
            return False
        
    def _calculate_move_score(self, move: Dict[str, Any]) -> float:
        """Calculate a score for a given move.
        
        Args:
            move: The move to score
            
        Returns:
            float: The calculated score
        """
        base_score = move["power"]
        
        # Type effectiveness multiplier
        multiplier = self._get_type_effectiveness(
            move["type"], 
            self.current_battle["opponent_pokemon"]["type"]
        )
        
        return base_score * multiplier
    
    def _get_best_move(self) -> Optional[int]:
        """Get the index of the best available move.
        
        Returns:
            Optional[int]: Index of the best move, or None if no moves available
        """
        if not self.current_battle["available_moves"]:
            return None

        move_scores = [
            (i, self._calculate_move_score(move))
            for i, move in enumerate(self.current_battle["available_moves"])
        ]
        
        if not move_scores:
            return None
            
        return max(move_scores, key=lambda x: x[1])[0]
    
    def _should_switch(self) -> bool:
        """Determine if we should switch Pokemon.
        
        Returns:
            bool: True if we should switch
        """
        if not self.current_battle:
            return False
            
        hp_percent = self.current_battle["active_pokemon"]["hp_percent"]
        return hp_percent < 20  # Switch if HP is below 20%
    
    def _get_best_switch_target(self) -> Optional[int]:
        """Get the best Pokemon to switch to.
        
        Returns:
            Optional[int]: Index of the best Pokemon to switch to
        """
        # TODO: Implement proper switching logic
        return 0
    
    def _execute_move(self, move_index: int) -> None:
        """Execute a battle move.
        
        Args:
            move_index: Index of the move to use
        """
        # Navigate to move
        self.emulator.press_button("A")  # Enter fight menu
        
        # Select move
        for _ in range(move_index):
            self.emulator.press_button("DOWN")
        self.emulator.press_button("A")

    def _execute_switch(self, target_index: int) -> None:
        """Execute a Pokemon switch.
        
        Args:
            target_index: Index of the Pokemon to switch to
        """
        # Navigate to Pokemon menu
        self.emulator.press_button("B")  # Exit current menu if in one
        self.emulator.press_button("RIGHT")  # Go to Pokemon menu
        self.emulator.press_button("A")  # Enter Pokemon menu
        
        # Select target Pokemon
        for _ in range(target_index):
            self.emulator.press_button("DOWN")
        self.emulator.press_button("A")  # Select Pokemon
        self.emulator.press_button("A")  # Confirm switch

    def _get_type_effectiveness(self, move_type: str, defender_types: list) -> float:
        """Calculate type effectiveness multiplier.
        
        Args:
            move_type: The type of the move
            defender_types: List of defender's types
            
        Returns:
            float: The type effectiveness multiplier
        """
        # TODO: Implement full type chart
        type_chart = {
            "FIRE": {
                "GRASS": 2.0,
                "WATER": 0.5
            },
            "WATER": {
                "FIRE": 2.0,
                "GRASS": 0.5
            },
            "GRASS": {
                "WATER": 2.0,
                "FIRE": 0.5
            }
        }
        
        # Default to neutral effectiveness
        if move_type not in type_chart:
            return 1.0
            
        multiplier = 1.0
        for def_type in defender_types:
            if def_type in type_chart[move_type]:
                multiplier *= type_chart[move_type][def_type]
                
        return multiplier 