"""
Webhook handler for processing screenshots and receiving game commands
"""

import os
import json
import requests
import time
from typing import List, Dict, Optional
from utils.logger import get_logger
from utils.command_queue import GameCommand, CommandQueue

# Get logger for this module
logger = get_logger("pokemon_player")

# Button name mapping from webhook to our internal names
BUTTON_MAP = {
    'a': 'x',       # Map A button to X key
    'b': 'z',       # Map B button to Z key
    'up': 'up',     # Keep directional buttons as is
    'down': 'down',
    'left': 'left',
    'right': 'right',
    'start': 'enter',    # Map START to Enter key
    'select': 'backspace', # Map SELECT to Backspace key
    'l': 'a',       # Map L button to A key
    'r': 's'        # Map R button to S key
}

def format_box(text: str, width: int = 80) -> str:
    """Format text in a nice box for logging"""
    lines = []
    lines.append("┌" + "─" * (width - 2) + "┐")
    
    # Word wrap the text
    words = text.split()
    current_line = "│ "
    for word in words:
        if len(current_line) + len(word) + 1 > width - 2:
            lines.append(current_line + " " * (width - len(current_line) - 1) + "│")
            current_line = "│ " + word
        else:
            current_line += " " + word if current_line != "│ " else word
    lines.append(current_line + " " * (width - len(current_line) - 1) + "│")
    
    lines.append("└" + "─" * (width - 2) + "┘")
    return "\n".join(lines)

class WebhookHandler:
    """Handles communication with the AI command webhook"""
    
    def __init__(self, webhook_url: str = "https://blopit.app.n8n.cloud/webhook/command-list"):
        """Initialize webhook handler
        
        Args:
            webhook_url: URL of the command webhook
        """
        self.webhook_url = webhook_url
        
    def process_screenshot(self, screenshot_path: str) -> Optional[List[GameCommand]]:
        """Upload screenshot and get command list from webhook
        
        Args:
            screenshot_path: Path to screenshot file
            
        Returns:
            List of GameCommand objects if successful, None if failed
        """
        try:
            # Verify file exists
            if not os.path.exists(screenshot_path):
                logger.error(f"Screenshot file not found: {screenshot_path}")
                return None
                
            # Upload file to webhook using curl-like format
            with open(screenshot_path, 'rb') as f:
                # Create multipart form data that matches curl's format
                files = {
                    'file': (
                        os.path.basename(screenshot_path),
                        f.read(),
                        'image/png'
                    )
                }
                logger.debug(f"Sending request to {self.webhook_url}")
                response = requests.post(
                    self.webhook_url,
                    files=files,
                    headers={
                        'User-Agent': 'curl/8.7.1',
                        'Accept': '*/*'
                    }
                )
                
            # Check response
            if response.status_code != 200:
                logger.error(f"Webhook error {response.status_code}: {response.text}")
                return None
                
            # Parse response
            try:
                data = response.json()
                logger.debug(f"Webhook response: {data}")
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON response: {response.text}")
                return None
                
            # Log the AI's reasoning in a nice box
            if 'reasoning' in data:
                reasoning_box = format_box(f"🤖 AI's Plan: {data['reasoning']}")
                logger.info("\n" + reasoning_box)  # Add newline before box
                
            commands = data.get('commands', [])
            if not commands:
                logger.warning("No commands in webhook response")
                return None
                
            # Convert to GameCommand objects
            game_commands = []
            for cmd in commands:
                try:
                    if cmd['type'] in ['press', 'hold', 'button_press']:
                        # Convert button name to lowercase and map to internal button name
                        button_name = cmd['button'].lower()
                        button = BUTTON_MAP.get(button_name)
                        
                        if not button:
                            logger.error(f"Unknown button: {cmd['button']} (mapped from {button_name})")
                            continue
                        
                        game_commands.append(GameCommand(
                            command_type='button_press',
                            args={
                                'button': button,
                                'duration': cmd['duration']
                            },
                            delay=cmd.get('delay', 0.0)
                        ))
                    elif cmd['type'] == 'wait':
                        # Handle wait commands by creating a dummy command that just sleeps
                        game_commands.append(GameCommand(
                            command_type='wait',
                            args={
                                'duration': cmd['duration']
                            },
                            delay=cmd.get('delay', 0.0)
                        ))
                    else:
                        logger.warning(f"Unknown command type: {cmd['type']}")
                except KeyError as e:
                    logger.error(f"Missing required field in command: {e}")
                    continue
                    
            if not game_commands:
                logger.warning("No valid commands found in response")
                return None
                
            logger.info(f"Successfully processed {len(game_commands)} commands")
            return game_commands
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error processing screenshot: {e}")
            return None
            
    def process_screenshot_to_queue(self, screenshot_path: str, command_queue: CommandQueue) -> bool:
        """Process screenshot and add resulting commands to queue
        
        Args:
            screenshot_path: Path to screenshot file
            command_queue: CommandQueue to add commands to
            
        Returns:
            True if commands were added successfully
        """
        commands = self.process_screenshot(screenshot_path)
        if commands:
            command_queue.add_commands(commands)
            return True
        return False 