"""
Game State Module

This module defines classes for representing the game state.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any, List

class GameMode(Enum):
    """Enum for different game modes/states."""
    UNKNOWN = "unknown"
    BATTLE = "battle"
    DIALOG = "dialog"
    MENU = "menu"
    OVERWORLD = "overworld"

@dataclass
class Pokemon:
    """Pokemon data."""
    species: str
    level: int
    hp: int
    max_hp: int
    moves: List[str]
    
    def is_fainted(self) -> bool:
        """Check if Pokemon is fainted."""
        return self.hp <= 0

@dataclass
class Player:
    """Player data."""
    x_position: int = 0
    y_position: int = 0
    party: List[Pokemon] = None
    
    def __post_init__(self):
        if self.party is None:
            self.party = []

@dataclass
class BattleState:
    """Class for tracking battle state."""
    player_pokemon: Optional[Dict[str, Any]] = None
    opponent_pokemon: Optional[Dict[str, Any]] = None
    available_moves: List[str] = None
    turn_count: int = 0
    is_wild_battle: bool = False

@dataclass
class GameState:
    """Class for tracking overall game state."""
    mode: GameMode = GameMode.UNKNOWN
    success: bool = False
    analysis: str = ""
    battle: Optional[BattleState] = None
    location: Optional[str] = None
    inventory: Optional[Dict[str, int]] = None
    party: Optional[List[Dict[str, Any]]] = None
    pokedex: Optional[Dict[str, bool]] = None
    badges: Optional[List[bool]] = None
    money: Optional[int] = None
    play_time: Optional[float] = None
    save_state: Optional[Dict[str, Any]] = None
    player: Optional[Player] = None
    error: Optional[str] = None
    
    def is_in_battle(self) -> bool:
        """Check if in battle mode."""
        return self.mode == GameMode.BATTLE
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GameState':
        """Create GameState from dictionary data.
        
        Args:
            data: Dictionary containing game state data
            
        Returns:
            GameState instance
        """
        # Determine mode
        if data.get("is_battle"):
            mode = GameMode.BATTLE
        elif data.get("is_menu"):
            mode = GameMode.MENU
        elif data.get("is_dialog"):
            mode = GameMode.DIALOG
        elif data.get("is_overworld"):
            mode = GameMode.OVERWORLD
        else:
            mode = GameMode.UNKNOWN
        
        # Create player data
        player_data = data.get("player")
        if player_data and isinstance(player_data, dict):
            player = Player(
                x_position=player_data.get("x_position", 0),
                y_position=player_data.get("y_position", 0),
                party=player_data.get("party", [])
            )
        elif player_data and isinstance(player_data, Player):
            player = player_data
        else:
            player = Player()
        
        # Create battle state if in battle
        battle = None
        if mode == GameMode.BATTLE:
            battle = BattleState(
                player_pokemon=data.get("player_pokemon"),
                opponent_pokemon=data.get("opponent_pokemon"),
                available_moves=data.get("available_moves", []),
                turn_count=data.get("turn_count", 0),
                is_wild_battle=data.get("is_wild_battle", False)
            )
        
        return cls(
            mode=mode,
            player=player,
            battle=battle,
            success=data.get("success", True),
            error=data.get("error"),
            analysis=data.get("analysis"),
            location=data.get("location"),
            inventory=data.get("inventory"),
            party=data.get("party"),
            pokedex=data.get("pokedex"),
            badges=data.get("badges"),
            money=data.get("money"),
            play_time=data.get("play_time"),
            save_state=data.get("save_state")
        ) 