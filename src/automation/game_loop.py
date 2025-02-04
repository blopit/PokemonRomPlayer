"""
Game Automation Loop

This module implements the core sense-process-actuate loop for game automation:
1. Sense: Capture screenshot of emulator window
2. Process: Use LLM to determine required actions
3. Actuate: Send keyboard inputs to emulator
"""

import time
import logging
import os
from pathlib import Path
from typing import Optional, List, Dict, Any

import cv2
import numpy as np

from emulator.interface import EmulatorInterface
from utils.llm_api import query_llm

logger = logging.getLogger(__name__)

class GameLoop:
    """Main automation loop for Pokemon game."""
    
    def __init__(self, rom_path: str, emulator_path: Optional[str] = None):
        """Initialize the game loop.
        
        Args:
            rom_path: Path to Pokemon ROM file
            emulator_path: Optional path to mGBA executable
        """
        self.emulator = EmulatorInterface(rom_path, emulator_path)
        
    def start(self):
        """Start the automation loop."""
        logger.info("Starting automation loop...")
        
        try:
            # Start emulator
            self.emulator.start()
            
            # Main loop
            while True:
                try:
                    # Get current screen state
                    screen = self.emulator.get_screen_state()
                    
                    # Process screen with LLM
                    actions = self.process_state(screen)
                    
                    # Execute actions
                    for action in actions:
                        self.execute_action(action)
                        
                    # Brief pause
                    time.sleep(0.1)
                    
                except KeyboardInterrupt:
                    logger.info("Stopping automation loop")
                    break
                except Exception as e:
                    logger.error(f"Error in automation loop: {e}")
                    time.sleep(1)  # Wait before retrying
                    
        finally:
            # Clean up
            self.emulator.stop()
            
    def process_state(self, screen: np.ndarray) -> List[Dict[str, Any]]:
        """Process the current game state and determine actions.
        
        Args:
            screen: Screenshot of current game state
            
        Returns:
            List of actions to execute
        """
        # Save screenshot for LLM
        os.makedirs("screenshots", exist_ok=True)
        timestamp = int(time.time())
        screenshot_path = f"screenshots/screen_{timestamp}.png"
        cv2.imwrite(screenshot_path, screen)
        
        # Query LLM for next actions
        prompt = """
        Analyze this Pokemon game screenshot and determine the next actions.
        The screenshot shows the current game state.
        
        You must respond with a valid Python list of dictionaries containing actions.
        Each action should be a dictionary with the following keys:
        - "action": either "press_button" or "wait"
        - "button": (for press_button only) one of: "up", "down", "left", "right", "a", "b", "start", "select"
        - "duration": time in seconds (float)
        
        Example response:
        [{"action": "press_button", "button": "a", "duration": 0.1}, {"action": "wait", "duration": 1.0}]
        
        Respond with ONLY the Python list, no other text.
        """
        
        try:
            response = query_llm(prompt, provider="openai", image_path=screenshot_path)
            # Clean up response to ensure it's valid Python
            response = response.strip()
            if not response.startswith("[") or not response.endswith("]"):
                logger.error("Invalid response format from LLM")
                return []
            
            # Parse response
            actions = eval(response)  # Convert string response to list
            
            # Validate actions
            valid_actions = []
            for action in actions:
                if not isinstance(action, dict):
                    continue
                
                action_type = action.get("action")
                if action_type not in ["press_button", "wait"]:
                    continue
                
                if action_type == "press_button":
                    if "button" not in action:
                        continue
                    if action["button"] not in ["up", "down", "left", "right", "a", "b", "start", "select"]:
                        continue
                    
                if "duration" not in action:
                    continue
                
                valid_actions.append(action)
            
            return valid_actions
        
        except Exception as e:
            logger.error(f"Error processing state with LLM: {e}")
            return []  # Return empty list on error
            
    def execute_action(self, action: Dict[str, Any]):
        """Execute a single action.
        
        Args:
            action: Action dictionary with type and parameters
        """
        action_type = action.get("action")
        
        if action_type == "press_button":
            button = action.get("button")
            duration = action.get("duration", 0.1)
            self.emulator.send_input(button, duration)
            
        elif action_type == "wait":
            duration = action.get("duration", 1.0)
            time.sleep(duration)
            
        else:
            logger.warning(f"Unknown action type: {action_type}")
            
def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Pokemon game automation")
    parser.add_argument("rom_path", help="Path to Pokemon ROM file")
    parser.add_argument("--emulator-path", help="Path to mGBA executable")
    
    args = parser.parse_args()
    
    try:
        loop = GameLoop(args.rom_path, args.emulator_path)
        loop.start()
    except Exception as e:
        logger.error(f"Error running automation: {e}")
        raise
        
if __name__ == "__main__":
    main() 