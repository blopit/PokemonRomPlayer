"""
Game State Manager Module

This module handles tracking and managing the game state, including progress tracking,
save states, and state transitions.
"""

import logging
import json
from typing import Dict, List, Optional, Any
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from ..emulator.interface import GameState, EmulatorInterface

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class Progress:
    """Tracks overall game progress."""
    badges: List[str] = None
    pokedex_caught: int = 0
    pokedex_seen: int = 0
    story_progress: str = "START"
    current_objective: str = "BEGIN_JOURNEY"
    pokemon_levels: Dict[str, int] = None
    play_time: float = 0.0
    save_count: int = 0
    last_save: Optional[datetime] = None
    
    def __post_init__(self):
        """Initialize default values for collections."""
        if self.badges is None:
            self.badges = []
        if self.pokemon_levels is None:
            self.pokemon_levels = {}

class GameStateManager:
    """Manages game state and progress tracking."""
    
    def __init__(self, emulator: EmulatorInterface, save_dir: str = "saves"):
        """
        Initialize the game state manager.
        
        Args:
            emulator: Interface to the GBA emulator
            save_dir: Directory to store save states and progress
        """
        self.emulator = emulator
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.progress = Progress()
        self.current_state = None
        self.state_history: List[GameState] = []
        self.max_history = 1000
        logger.info(f"Initialized GameStateManager with save directory: {save_dir}")
        
    def update(self) -> None:
        """Update the current game state and progress."""
        new_state = self.emulator.get_game_state()
        self._update_progress(new_state)
        self._update_history(new_state)
        self.current_state = new_state
        
    def save_progress(self, slot: Optional[int] = None) -> bool:
        """
        Save current progress and game state.
        
        Args:
            slot: Optional save slot number
            
        Returns:
            True if save was successful
        """
        try:
            # Save emulator state
            if slot is not None:
                self.emulator.save_state(slot)
            
            # Save progress data
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_name = f"progress_{timestamp}.json" if slot is None else f"progress_slot_{slot}.json"
            save_path = self.save_dir / save_name
            
            progress_data = {
                "progress": asdict(self.progress),
                "timestamp": timestamp,
                "slot": slot
            }
            
            with open(save_path, 'w') as f:
                json.dump(progress_data, f, indent=2, default=str)
            
            self.progress.save_count += 1
            self.progress.last_save = datetime.now()
            logger.info(f"Saved progress to {save_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save progress: {e}")
            return False
    
    def load_progress(self, slot: Optional[int] = None) -> bool:
        """
        Load progress and game state.
        
        Args:
            slot: Optional save slot number
            
        Returns:
            True if load was successful
        """
        try:
            # Find the appropriate save file
            if slot is not None:
                save_path = self.save_dir / f"progress_slot_{slot}.json"
            else:
                # Load the most recent save
                save_files = list(self.save_dir.glob("progress_*.json"))
                if not save_files:
                    logger.warning("No save files found")
                    return False
                save_path = max(save_files, key=lambda p: p.stat().st_mtime)
            
            # Load progress data
            with open(save_path, 'r') as f:
                progress_data = json.load(f)
            
            # Load emulator state if slot specified
            if slot is not None:
                self.emulator.load_state(slot)
            
            # Update progress
            self.progress = Progress(**progress_data["progress"])
            logger.info(f"Loaded progress from {save_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load progress: {e}")
            return False
    
    def get_objective(self) -> str:
        """Get the current objective."""
        return self.progress.current_objective
    
    def set_objective(self, objective: str) -> None:
        """
        Set the current objective.
        
        Args:
            objective: New objective string
        """
        logger.info(f"Setting objective: {objective}")
        self.progress.current_objective = objective
    
    def _update_progress(self, state: GameState) -> None:
        """
        Update progress based on new game state.
        
        Args:
            state: New game state
        """
        # Update play time
        self.progress.play_time += 1/60  # Assuming 60 fps
        
        # TODO: Implement progress updates based on game state
        # - Check for new badges
        # - Update Pokedex counts
        # - Track Pokemon levels
        # - Update story progress
    
    def _update_history(self, state: GameState) -> None:
        """
        Update state history.
        
        Args:
            state: New game state
        """
        self.state_history.append(state)
        if len(self.state_history) > self.max_history:
            self.state_history.pop(0)
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of current progress.
        
        Returns:
            Dictionary containing progress summary
        """
        return {
            "badges": len(self.progress.badges),
            "pokedex": {
                "caught": self.progress.pokedex_caught,
                "seen": self.progress.pokedex_seen,
                "completion": f"{(self.progress.pokedex_caught/386)*100:.1f}%"
            },
            "story": self.progress.story_progress,
            "objective": self.progress.current_objective,
            "play_time": f"{self.progress.play_time/3600:.1f} hours",
            "pokemon_count": len(self.progress.pokemon_levels),
            "max_level_count": sum(1 for level in self.progress.pokemon_levels.values() if level >= 100)
        } 