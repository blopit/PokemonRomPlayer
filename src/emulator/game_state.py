from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum

class GameMode(Enum):
    """Different modes/states the game can be in."""
    OVERWORLD = "overworld"
    BATTLE = "battle"
    MENU = "menu"
    DIALOG = "dialog"
    UNKNOWN = "unknown"

@dataclass
class Pokemon:
    """Represents a Pokemon's data."""
    species_id: int
    level: int
    hp: int
    max_hp: int
    status: Optional[str] = None
    moves: List[str] = None
    
    def is_fainted(self) -> bool:
        """Check if the Pokemon is fainted."""
        return self.hp <= 0

@dataclass
class BattleState:
    """Represents the state during a battle."""
    opponent_pokemon: Optional[Pokemon] = None
    active_pokemon: Optional[Pokemon] = None
    is_wild_battle: bool = False
    turn_count: int = 0

@dataclass
class PlayerState:
    """Represents the player's current state."""
    x_position: int = 0
    y_position: int = 0
    direction: str = "down"
    money: int = 0
    badges: List[str] = None
    party: List[Pokemon] = None
    items: Dict[str, int] = None

@dataclass
class GameState:
    """Represents the complete game state."""
    mode: GameMode = GameMode.UNKNOWN
    player: PlayerState = None
    battle: Optional[BattleState] = None
    
    def __post_init__(self):
        """Initialize default values for nested objects."""
        if self.player is None:
            self.player = PlayerState(
                badges=[],
                party=[],
                items={}
            )
    
    def update_from_memory(self, memory_values: Dict[str, Any]) -> None:
        """Update the game state using memory values from the emulator.
        
        Args:
            memory_values: Dictionary of memory addresses and their values
        """
        # TODO: Implement memory parsing logic
        pass
    
    def is_in_battle(self) -> bool:
        """Check if currently in a battle."""
        return self.mode == GameMode.BATTLE
    
    def can_catch_pokemon(self) -> bool:
        """Check if conditions are right to catch a Pokemon."""
        return (self.is_in_battle() and 
                self.battle is not None and 
                self.battle.is_wild_battle and
                self.battle.opponent_pokemon is not None) 