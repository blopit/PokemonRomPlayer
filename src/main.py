"""
Main Entry Point

This module serves as the main entry point for the Pokemon ROM Player system.
It initializes all components and manages the main game loop.
"""

import argparse
import json
import sys
import time
import os
import logging
from pathlib import Path

from utils.logger import init_logger, get_logger, setup_logging
from utils.config_manager import ConfigManager
from emulator.interface import EmulatorInterface
from game_state.manager import GameStateManager
from agents.crew_manager import CrewManager
from emulator.game_state import GameState, GameMode
from ai.agent_manager import AgentManager

logger = logging.getLogger('pokemon_player')

def parse_args():
    """Parse command line arguments.
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(description='Pokemon ROM Player')
    parser.add_argument('--config', type=str, required=True,
                       help='Path to configuration file')
    return parser.parse_args()

def load_config(config_path):
    """Load configuration from file.
    
    Args:
        config_path: Path to config file
        
    Returns:
        dict: Configuration settings
    """
    try:
        with open(config_path) as f:
            config = json.load(f)
            
        # Validate required fields
        required_fields = ['rom_path', 'emulator_path', 'ai_config']
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Missing required config field: {field}")
                
        return config
        
    except Exception as e:
        logger.error(f"Failed to load config: {str(e)}")
        raise

def initialize_system(config):
    """Initialize system components.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        tuple: (EmulatorInterface, AgentManager)
    """
    try:
        logger.info("Initializing system components...")
        
        # Initialize emulator
        emulator = EmulatorInterface(
            rom_path=config['rom_path'],
            emulator_path=config['emulator_path']
        )
        
        # Initialize agent manager
        agent_manager = AgentManager(
            emulator=emulator,
            config=config['ai_config']
        )
        
        return emulator, agent_manager
        
    except Exception as e:
        logger.error(f"Failed to initialize system: {str(e)}")
        raise

def cleanup(emulator=None):
    """Clean up system resources.
    
    Args:
        emulator: EmulatorInterface instance
    """
    try:
        logger.info("Cleaning up...")
        if emulator:
            emulator.stop()
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")
    finally:
        logger.info("Shutdown complete")

def main():
    """Main program entry point."""
    try:
        # Set up logging
        setup_logging()
        logger.info("Starting Pokemon ROM Player")
        
        # Parse arguments and load config
        args = parse_args()
        config = load_config(args.config)
        
        # Initialize system
        emulator, agent_manager = initialize_system(config)
        
        # Start emulator
        emulator.start()
        
        # Main loop
        try:
            while True:
                # Get current game state
                game_state = emulator.get_game_state()
                
                # Let agent manager handle the state
                agent_manager.update(game_state)
                
                # Small delay to prevent busy waiting
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
            
        finally:
            cleanup(emulator)
            
    except Exception as e:
        logger.error(f"Critical error: {str(e)}")
        cleanup()
        sys.exit(1)

if __name__ == '__main__':
    main() 