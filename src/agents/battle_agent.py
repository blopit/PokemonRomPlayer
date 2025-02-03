"""
Battle Agent Module

This module implements the battle agent responsible for handling Pokemon battles.
It uses type matchups, move selection, and battle strategies to win battles.
"""

import logging
from typing import Dict, List, Optional, Tuple
from .base_agent import BaseAgent
from ..emulator.interface import GameState

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Type effectiveness chart (simplified for example)
TYPE_CHART = {
    "NORMAL": {"ROCK": 0.5, "GHOST": 0, "STEEL": 0.5},
    "FIRE": {"FIRE": 0.5, "WATER": 0.5, "GRASS": 2, "ICE": 2, "BUG": 2, "ROCK": 0.5, "DRAGON": 0.5, "STEEL": 2},
    "WATER": {"FIRE": 2, "WATER": 0.5, "GRASS": 0.5, "GROUND": 2, "ROCK": 2, "DRAGON": 0.5},
    # Add more type matchups as needed
}

class BattleAgent(BaseAgent):
    """Agent responsible for handling Pokemon battles."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_battle = None
        self.strategy = self.config.get("strategy", "AGGRESSIVE")
        logger.info(f"Battle Agent initialized with strategy: {self.strategy}")
    
    def can_handle(self, state: GameState) -> bool:
        """Check if we're in a battle state."""
        return state.in_battle
    
    def act(self, state: GameState) -> bool:
        """
        Handle the current battle situation.
        
        Args:
            state: Current game state
            
        Returns:
            True if action was successful
        """
        try:
            # Update battle state
            self._update_battle_state(state)
            
            # Check if we need to switch Pokemon
            if self._should_switch():
                return self._switch_pokemon()
            
            # Select and use the best move
            return self._use_best_move()
            
        except Exception as e:
            logger.error(f"Error in battle action: {e}")
            return False
    
    def _update_battle_state(self, state: GameState) -> None:
        """
        Update internal battle state tracking.
        
        Args:
            state: Current game state
        """
        # Extract battle information from game state
        # TODO: Implement battle state parsing
        self.current_battle = {
            "active_pokemon": None,
            "opponent_pokemon": None,
            "available_moves": [],
            "team_status": []
        }
        logger.debug("Updated battle state")
    
    def _calculate_move_score(self, move: Dict) -> float:
        """
        Calculate a score for a potential move.
        
        Args:
            move: Move information dictionary
            
        Returns:
            Score value for the move
        """
        score = move.get("power", 0)
        
        # Apply type effectiveness
        move_type = move.get("type", "NORMAL")
        opponent_type = self.current_battle["opponent_pokemon"].get("type", ["NORMAL"])
        
        for type_ in opponent_type:
            if move_type in TYPE_CHART and type_ in TYPE_CHART[move_type]:
                score *= TYPE_CHART[move_type][type_]
        
        # Consider PP
        pp_left = move.get("pp", 0)
        if pp_left <= 0:
            score = 0
        
        # Consider status moves
        if move.get("category") == "STATUS":
            # TODO: Implement status move scoring
            pass
        
        return score
    
    def _get_best_move(self) -> Optional[int]:
        """
        Select the best move for the current situation.
        
        Returns:
            Index of the best move or None if no moves available
        """
        if not self.current_battle["available_moves"]:
            return None
            
        move_scores = [
            (i, self._calculate_move_score(move))
            for i, move in enumerate(self.current_battle["available_moves"])
        ]
        
        best_move = max(move_scores, key=lambda x: x[1])
        return best_move[0] if best_move[1] > 0 else None
    
    def _should_switch(self) -> bool:
        """
        Determine if we should switch Pokemon.
        
        Returns:
            True if we should switch Pokemon
        """
        if not self.current_battle:
            return False
            
        active = self.current_battle["active_pokemon"]
        opponent = self.current_battle["opponent_pokemon"]
        
        # Check health percentage
        if active.get("hp_percent", 100) < 20:
            return True
            
        # Check type disadvantage
        active_type = active.get("type", ["NORMAL"])
        opponent_type = opponent.get("type", ["NORMAL"])
        
        type_disadvantage = False
        for opp_type in opponent_type:
            if opp_type in TYPE_CHART:
                for act_type in active_type:
                    if act_type in TYPE_CHART[opp_type] and TYPE_CHART[opp_type][act_type] > 1:
                        type_disadvantage = True
                        break
        
        return type_disadvantage and self._has_better_matchup()
    
    def _has_better_matchup(self) -> bool:
        """
        Check if we have a better Pokemon for the current matchup.
        
        Returns:
            True if a better matchup is available
        """
        # TODO: Implement team analysis for better matchups
        return False
    
    def _switch_pokemon(self) -> bool:
        """
        Switch to a better Pokemon.
        
        Returns:
            True if switch was successful
        """
        try:
            # Open Pokemon menu
            self._safe_execute("open_menu", self.emulator.press_button, "START")
            
            # TODO: Implement Pokemon switching logic
            # - Select best Pokemon based on matchup
            # - Navigate menu to switch
            # - Confirm switch
            
            logger.info("Switched Pokemon")
            return True
            
        except Exception as e:
            logger.error(f"Failed to switch Pokemon: {e}")
            return False
    
    def _use_best_move(self) -> bool:
        """
        Use the best available move.
        
        Returns:
            True if move was successfully used
        """
        best_move = self._get_best_move()
        if best_move is None:
            logger.warning("No valid moves available")
            return False
            
        try:
            # Select and use move
            # TODO: Implement move selection and execution
            logger.info(f"Using move {best_move}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to use move: {e}")
            return False 