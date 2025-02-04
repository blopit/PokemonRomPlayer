"""
Game State Manager Module

This module manages the game state and its updates.
"""

from typing import Dict, Optional, List, Any
from dataclasses import dataclass, field
from pathlib import Path
import json
import time
from datetime import datetime

from utils.logger import get_logger
from emulator.interface import EmulatorInterface
from emulator.game_state import GameState, GameMode

# Get logger for this module
logger = get_logger("game_state")

@dataclass
class Progress:
    """Class for tracking game progress."""
    badges: List[str] = field(default_factory=list)
    pokedex_caught: int = 0
    pokedex_seen: int = 0
    story_progress: str = ""
    current_objective: str = ""
    pokemon_levels: Dict[str, int] = field(default_factory=dict)
    play_time: float = 0.0
    save_count: int = 0

class GameStateManager:
    """Manages and updates the game state."""
    
    def __init__(self, emulator: EmulatorInterface, save_dir: str = "saves"):
        """Initialize the game state manager.
        
        Args:
            emulator: EmulatorInterface instance
            save_dir: Directory for saving progress
        """
        self.emulator = emulator
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(exist_ok=True)
        
        self.current_state = None
        self.state_history = []
        self.max_history = 100
        self.progress = Progress()
        
        logger.info("Game state manager initialized")
    
    def update(self) -> bool:
        """Update the game state.
        
        Returns:
            True if update was successful
        """
        try:
            # Get current state from emulator
            state = self.emulator.get_game_state()
            
            # Update state history
            self.current_state = state
            self.state_history.append(state)
            
            # Limit history size
            if len(self.state_history) > self.max_history:
                self.state_history = self.state_history[-self.max_history:]
            
            # Update progress based on state
            self._update_progress(state)
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating game state: {e}")
            return False
    
    def _update_progress(self, state: GameState):
        """Update progress based on current state.
        
        Args:
            state: Current game state
        """
        # Update play time
        self.progress.play_time += 0.1  # Assuming 100ms update interval
        
        # Update other progress metrics based on state
        if state.mode == GameMode.BATTLE:
            # Handle battle progress
            pass
        elif state.mode == GameMode.OVERWORLD:
            # Handle overworld progress
            pass
    
    def save_progress(self, slot: int = 0) -> bool:
        """Save current progress to file.
        
        Args:
            slot: Save slot number
            
        Returns:
            True if save was successful
        """
        try:
            # Create save data
            save_data = {
                "progress": {
                    "badges": self.progress.badges,
                    "pokedex_caught": self.progress.pokedex_caught,
                    "pokedex_seen": self.progress.pokedex_seen,
                    "story_progress": self.progress.story_progress,
                    "current_objective": self.progress.current_objective,
                    "pokemon_levels": self.progress.pokemon_levels,
                    "play_time": self.progress.play_time,
                    "save_count": self.progress.save_count + 1
                },
                "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
                "slot": slot
            }
            
            # Save to file
            save_path = self.save_dir / f"progress_slot_{slot}.json"
            with open(save_path, 'w') as f:
                json.dump(save_data, f, indent=2)
            
            self.progress.save_count += 1
            logger.info(f"Progress saved to slot {slot}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving progress: {e}")
            return False
    
    def load_progress(self, slot: int = 0) -> bool:
        """Load progress from file.
        
        Args:
            slot: Save slot number
            
        Returns:
            True if load was successful
        """
        try:
            # Load from file
            save_path = self.save_dir / f"progress_slot_{slot}.json"
            with open(save_path, 'r') as f:
                save_data = json.load(f)
            
            # Update progress
            progress_data = save_data["progress"]
            self.progress.badges = progress_data["badges"]
            self.progress.pokedex_caught = progress_data["pokedex_caught"]
            self.progress.pokedex_seen = progress_data["pokedex_seen"]
            self.progress.story_progress = progress_data["story_progress"]
            self.progress.current_objective = progress_data["current_objective"]
            self.progress.pokemon_levels = progress_data["pokemon_levels"]
            self.progress.play_time = progress_data["play_time"]
            self.progress.save_count = progress_data["save_count"]
            
            logger.info(f"Progress loaded from slot {slot}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading progress: {e}")
            return False
    
    def get_objective(self) -> str:
        """Get current objective.
        
        Returns:
            Current objective string
        """
        return self.progress.current_objective
    
    def set_objective(self, objective: str):
        """Set current objective.
        
        Args:
            objective: New objective string
        """
        self.progress.current_objective = objective
        logger.info(f"New objective set: {objective}")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get progress summary.
        
        Returns:
            Summary dictionary
        """
        # Count Pokemon at max level
        max_level_count = sum(1 for level in self.progress.pokemon_levels.values() if level == 100)
        
        return {
            "badges": len(self.progress.badges),
            "pokedex": {
                "caught": self.progress.pokedex_caught,
                "seen": self.progress.pokedex_seen
            },
            "story": self.progress.story_progress,
            "pokemon_count": len(self.progress.pokemon_levels),
            "max_level_count": max_level_count,
            "play_time": f"{self.progress.play_time / 3600:.1f} hours"
        } 