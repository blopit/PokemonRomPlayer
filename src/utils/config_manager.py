import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass

@dataclass
class EmulatorConfig:
    """Emulator configuration settings."""
    executable_path: str
    window_title: str
    key_mappings: Dict[str, str]
    save_state_dir: str

@dataclass
class GameConfig:
    """Game-specific configuration settings."""
    rom_path: str
    game_version: str
    memory_map_version: str
    save_file_path: Optional[str] = None

@dataclass
class AIConfig:
    """AI behavior configuration settings."""
    battle_strategy: str = "aggressive"  # aggressive, defensive, balanced
    catch_strategy: str = "all"         # all, new, none
    training_strategy: str = "efficient" # efficient, thorough, balanced
    max_level: int = 100
    min_hp_percent: float = 30.0
    max_money_spend: int = 10000

class ConfigManager:
    """Manages configuration settings for the Pokemon ROM player."""
    
    DEFAULT_CONFIG = {
        "emulator": {
            "executable_path": "mgba",
            "window_title": "mGBA",
            "key_mappings": {
                "a": "x",
                "b": "z",
                "start": "enter",
                "select": "backspace",
                "up": "up",
                "down": "down",
                "left": "left",
                "right": "right",
                "l": "a",
                "r": "s"
            },
            "save_state_dir": "saves"
        },
        "game": {
            "rom_path": "",
            "game_version": "emerald",
            "memory_map_version": "emerald",
            "save_file_path": None
        },
        "ai": {
            "battle_strategy": "aggressive",
            "catch_strategy": "all",
            "training_strategy": "efficient",
            "max_level": 100,
            "min_hp_percent": 30.0,
            "max_money_spend": 10000
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration manager.
        
        Args:
            config_path: Optional path to configuration file
        """
        self.config_path = Path(config_path) if config_path else Path("config.json")
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default.
        
        Returns:
            Configuration dictionary
        """
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                # Merge with defaults to ensure all fields exist
                return self._merge_with_defaults(config)
        return self.DEFAULT_CONFIG.copy()
    
    def save_config(self) -> None:
        """Save current configuration to file."""
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=4)
    
    def _merge_with_defaults(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge provided config with defaults to ensure all fields exist.
        
        Args:
            config: Configuration to merge
            
        Returns:
            Merged configuration
        """
        merged = self.DEFAULT_CONFIG.copy()
        
        for section in merged:
            if section in config:
                merged[section].update(config[section])
        
        return merged
    
    def get_emulator_config(self) -> EmulatorConfig:
        """Get emulator configuration.
        
        Returns:
            EmulatorConfig object
        """
        return EmulatorConfig(**self.config["emulator"])
    
    def get_game_config(self) -> GameConfig:
        """Get game configuration.
        
        Returns:
            GameConfig object
        """
        return GameConfig(**self.config["game"])
    
    def get_ai_config(self) -> AIConfig:
        """Get AI configuration.
        
        Returns:
            AIConfig object
        """
        return AIConfig(**self.config["ai"])
    
    def update_emulator_config(self, **kwargs) -> None:
        """Update emulator configuration settings.
        
        Args:
            **kwargs: Configuration key-value pairs to update
        """
        self.config["emulator"].update(kwargs)
        self.save_config()
    
    def update_game_config(self, **kwargs) -> None:
        """Update game configuration settings.
        
        Args:
            **kwargs: Configuration key-value pairs to update
        """
        self.config["game"].update(kwargs)
        self.save_config()
    
    def update_ai_config(self, **kwargs) -> None:
        """Update AI configuration settings.
        
        Args:
            **kwargs: Configuration key-value pairs to update
        """
        self.config["ai"].update(kwargs)
        self.save_config()
    
    def validate_config(self) -> bool:
        """Validate the current configuration.
        
        Returns:
            True if configuration is valid
        """
        try:
            game_config = self.get_game_config()
            if not os.path.exists(game_config.rom_path):
                return False
            
            emulator_config = self.get_emulator_config()
            if not os.path.exists(emulator_config.save_state_dir):
                os.makedirs(emulator_config.save_state_dir)
            
            return True
        except Exception:
            return False 