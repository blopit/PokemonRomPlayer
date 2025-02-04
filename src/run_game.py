"""
Main entry point for Pokemon ROM automation
"""

import argparse
import logging
import os
import signal
import sys
import time
from typing import Optional
import cv2
from dotenv import load_dotenv

# Add the project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables from .env file
load_dotenv()

from utils.logger import setup_logger, get_logger
from utils.screen_analyzer import ScreenAnalyzer
from utils.command_queue import CommandQueue
from ai.command_generator import CommandGenerator
from emulator.interface import EmulatorInterface
from utils.screenshot import capture_window, take_screenshot

logger = get_logger("pokemon_player")

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Pokemon ROM automation")
    parser.add_argument("rom_path", help="Path to ROM file")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--screenshot-interval", type=float, default=1.0, 
                      help="Interval between screenshots in seconds")
    return parser.parse_args()

def main():
    """Main entry point"""
    # Parse arguments
    args = parse_args()
    
    # Setup logging
    setup_logger(debug=args.debug)
    
    # Initialize components
    emulator = EmulatorInterface(args.rom_path)
    command_queue = CommandQueue()
    command_generator = CommandGenerator()
    
    if not emulator.start():
        sys.exit(1)
        
    # Initialize screen analyzer
    screen_analyzer = ScreenAnalyzer(pid=emulator.pid)
    
    # Register signal handlers
    def signal_handler(signum, frame):
        logger.info("Shutting down...")
        emulator.stop()
        sys.exit(0)
        
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("Starting automation loop...")
    
    try:
        # Game state context
        context = {
            "inventory": {},
            "party": {},
            "location": None,
            "objectives": []
        }
        
        last_screenshot_time = 0
        
        # Create screenshots directory
        os.makedirs("screenshots", exist_ok=True)
        
        # Main game loop
        while True:
            try:
                # Get current screen state
                screen = emulator.get_screen_state()
                screen_state = screen_analyzer.analyze_screen(screen)
                
                # Save screenshot periodically
                current_time = time.time()
                if current_time - last_screenshot_time >= args.screenshot_interval:
                    try:
                        # Capture window using process ID
                        img = capture_window(pid=emulator.process.pid if emulator.process else None)
                        
                        # Save the screenshot
                        timestamp = time.strftime("%Y%m%d-%H%M%S")
                        screenshot_path = os.path.join("screenshots", f"screenshot_{timestamp}.png")
                        cv2.imwrite(screenshot_path, img)
                        logger.info(f"Saved screenshot to {screenshot_path}")
                    except Exception as e:
                        logger.error(f"Failed to save screenshot: {e}")
                    last_screenshot_time = current_time
                
                # If queue is empty, generate next batch of commands
                if command_queue.is_empty():
                    commands = command_generator.generate_commands(screen_state, context)
                    if commands:
                        logger.info(f"Generated {len(commands)} new commands")
                        command_queue.add_commands(commands)
                    else:
                        logger.warning("No commands generated, waiting...")
                        time.sleep(1)
                        continue
                    
                    # Update context based on screen state
                    context.update({
                        "last_screen": screen_state,
                        "timestamp": current_time
                    })
                
                # Process queued commands
                command_queue.process_commands(emulator)
                
                # Small delay to prevent CPU overload
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error in game loop: {e}")
                time.sleep(1)
                continue
                
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        emulator.stop()
            
if __name__ == "__main__":
    main() 