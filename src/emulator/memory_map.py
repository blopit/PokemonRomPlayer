from dataclasses import dataclass
from typing import Dict, List, Tuple
from enum import Enum

class GameVersion(Enum):
    """Supported Pokemon game versions."""
    RUBY = "ruby"
    SAPPHIRE = "sapphire"
    EMERALD = "emerald"
    FIRERED = "firered"
    LEAFGREEN = "leafgreen"

@dataclass
class MemoryAddresses:
    """Memory addresses for various game data."""
    # Game state addresses
    game_state: int
    battle_type: int
    menu_state: int
    
    # Player data
    player_x: int
    player_y: int
    player_direction: int
    player_money: int
    
    # Party data
    party_count: int
    party_data_start: int
    
    # Battle data
    battle_type: int
    opponent_pokemon_data: int
    active_pokemon_data: int

class MemoryMap:
    """Handles memory mapping for different Pokemon game versions."""
    
    # Memory address maps for different game versions
    VERSION_MAPS: Dict[GameVersion, MemoryAddresses] = {
        GameVersion.EMERALD: MemoryAddresses(
            # Game state
            game_state=0x03004E50,
            battle_type=0x0202402C,
            menu_state=0x03004E54,
            
            # Player data
            player_x=0x02037364,
            player_y=0x02037368,
            player_direction=0x0203736C,
            player_money=0x02025E44,
            
            # Party data
            party_count=0x02024029,
            party_data_start=0x0202402C,
            
            # Battle data
            battle_type=0x0202402C,
            opponent_pokemon_data=0x02024744,
            active_pokemon_data=0x02023F8C
        ),
        # Add other version mappings as needed
    }
    
    def __init__(self, version: GameVersion):
        """Initialize memory map for specific game version.
        
        Args:
            version: Pokemon game version
        """
        if version not in self.VERSION_MAPS:
            raise ValueError(f"Unsupported game version: {version}")
        self.version = version
        self.addresses = self.VERSION_MAPS[version]
    
    def get_pokemon_data_structure(self) -> List[Tuple[str, int, int]]:
        """Get the memory structure for Pokemon data.
        
        Returns:
            List of tuples containing (field_name, offset, size)
        """
        return [
            ("species", 0x00, 2),
            ("item", 0x02, 2),
            ("moves", 0x04, 8),  # 4 moves, 2 bytes each
            ("pp", 0x0C, 4),    # 4 PP values, 1 byte each
            ("level", 0x10, 1),
            ("status", 0x11, 1),
            ("hp", 0x12, 2),
            ("max_hp", 0x14, 2),
            ("attack", 0x16, 2),
            ("defense", 0x18, 2),
            ("speed", 0x1A, 2),
            ("sp_attack", 0x1C, 2),
            ("sp_defense", 0x1E, 2)
        ]
    
    def get_item_data_structure(self) -> List[Tuple[str, int, int]]:
        """Get the memory structure for item data.
        
        Returns:
            List of tuples containing (field_name, offset, size)
        """
        return [
            ("id", 0x00, 2),
            ("count", 0x02, 2)
        ]
    
    def calculate_party_pokemon_address(self, index: int) -> int:
        """Calculate memory address for a specific party Pokemon.
        
        Args:
            index: Party position index (0-5)
            
        Returns:
            Memory address for the Pokemon data
        """
        if not 0 <= index <= 5:
            raise ValueError("Party index must be between 0 and 5")
        pokemon_data_size = 100  # Size of Pokemon data structure
        return self.addresses.party_data_start + (index * pokemon_data_size) 