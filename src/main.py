"""
Main Entry Point

This module serves as the main entry point for the Pokemon ROM Player system.
It initializes all components and manages the main game loop.
"""

import argparse
import logging
import os
import sys
import time
from pathlib import Path
from typing import Optional

from utils.logger import logger
from utils.config_manager import ConfigManager
from emulator.interface import EmulatorInterface
from game_state.manager import GameStateManager
from agents.crew_manager import CrewManager
from emulator.game_state import GameState, GameMode
from ai.agent_manager import AgentManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("pokemon_player.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Pokemon ROM Player")
    parser.add_argument("--rom", type=str, help="Path to Pokemon ROM file")
    parser.add_argument("--config", type=str, help="Path to configuration file")
    parser.add_argument("--save-dir", type=str, help="Directory for save states")
    parser.add_argument("--log-dir", type=str, help="Directory for log files")
    return parser.parse_args()

def initialize_system(args: argparse.Namespace) -> tuple[ConfigManager, EmulatorInterface, AgentManager]:
    """Initialize the system components.
    
    Args:
        args: Command line arguments
        
    Returns:
        Tuple of (ConfigManager, EmulatorInterface, AgentManager)
    """
    # Initialize configuration
    config_manager = ConfigManager(args.config)
    
    # Update configuration from command line arguments
    if args.rom:
        config_manager.update_game_config(rom_path=args.rom)
    if args.save_dir:
        config_manager.update_emulator_config(save_state_dir=args.save_dir)
    
    # Validate configuration
    if not config_manager.validate_config():
        logger.error("Invalid configuration")
        sys.exit(1)
    
    # Initialize emulator
    game_config = config_manager.get_game_config()
    emulator_config = config_manager.get_emulator_config()
    
    emulator = EmulatorInterface(
        rom_path=game_config.rom_path,
        save_state_dir=emulator_config.save_state_dir
    )
    
    # Initialize agent manager
    agent_manager = AgentManager(emulator, config_manager.get_ai_config())
    
    return config_manager, emulator, agent_manager

def main() -> None:
    """Main entry point for the Pokemon ROM player."""
    # Parse command line arguments
    args = parse_arguments()
    
    # Set up logging
    if args.log_dir:
        logger.__init__(log_dir=args.log_dir)
    
    logger.info("Starting Pokemon ROM Player")
    
    try:
        # Initialize system
        config_manager, emulator, agent_manager = initialize_system(args)
        
        # Start emulator
        if not emulator.start():
            logger.error("Failed to start emulator")
            sys.exit(1)
        
        logger.info("System initialized successfully")
        
        # Main game loop
        last_update = time.time()
        update_interval = 1.0 / 30  # 30 FPS
        
        while True:
            current_time = time.time()
            if current_time - last_update < update_interval:
                continue
            
            # Get current game state
            game_state = emulator.get_game_state()
            
            # Update agents
            if not agent_manager.update(game_state):
                # No agent took action, small delay to prevent busy loop
                time.sleep(0.016)
            
            last_update = current_time
            
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
    finally:
        # Clean up
        emulator.stop()
        logger.info("Cleanup complete")

if __name__ == "__main__":
    main() 