"""
Menu navigation agent
"""

from typing import List, Dict, Any, Optional
from utils.command_queue import CommandQueue, GameCommand
from utils.logger import get_logger
from ai.agent import Agent
from utils.llm_api import get_provider
import json

logger = get_logger("pokemon_player")

MENU_PROMPT = """You are a menu navigation expert for Pokemon games. Your task is to navigate menus efficiently to achieve objectives.

Current screen state:
{screen_state}

Game state:
{game_state}

Context:
{context}

Generate a sequence of button presses to navigate the menu. Consider:
1. Current menu position
2. Target menu item
3. Most efficient path
4. Menu wrapping (up/down)
5. Menu hierarchy (back with B)

Return your response in this exact format:
{
    "commands": [
        {"type": "button_press", "button": "up", "duration": 0.1, "delay": 0.0},
        {"type": "button_press", "button": "a", "duration": 0.1, "delay": 0.2},
        ...
    ],
    "reasoning": "Explanation of menu navigation strategy"
}"""

class MenuAgent(Agent):
    """Agent specialized in menu navigation"""
    
    def __init__(self, provider: str = "openai"):
        """Initialize menu agent.
        
        Args:
            provider: LLM provider to use
        """
        super().__init__("MenuAgent")
        self.llm = get_provider(provider)
        
    def can_handle(self, screen_state: Dict[str, Any], game_state: Dict[str, Any]) -> bool:
        """Check if current state is a menu that needs navigation.
        
        Args:
            screen_state: Current screen analysis results
            game_state: Current game memory state
            
        Returns:
            True if in a menu state
        """
        # Check if in menu based on screen analysis
        if screen_state.get("screen_type") == "menu":
            return True
            
        # Check if in menu based on memory
        if game_state.get("menu_state"):
            return True
            
        return False
        
    def generate_commands(self, 
                         screen_state: Dict[str, Any],
                         game_state: Dict[str, Any],
                         context: Optional[Dict[str, Any]] = None) -> List[GameCommand]:
        """Generate menu navigation commands.
        
        Args:
            screen_state: Current screen analysis results
            game_state: Current game memory state
            context: Optional additional context
            
        Returns:
            List of commands for menu navigation
        """
        try:
            # Format prompt with current state
            prompt = MENU_PROMPT.format(
                screen_state=screen_state,
                game_state=game_state,
                context=context or {}
            )
            
            # Get navigation commands from LLM
            response = self.llm.query(prompt)
            
            # Parse commands
            try:
                # Extract JSON from response
                start = response.find('{')
                end = response.rfind('}') + 1
                if start >= 0 and end > start:
                    json_str = response[start:end]
                    data = json.loads(json_str)
                else:
                    raise ValueError("No JSON object found in response")
                    
                # Log reasoning
                if "reasoning" in data:
                    logger.info(f"Menu navigation reasoning: {data['reasoning']}")
                    
                # Convert to commands
                commands = []
                for cmd in data.get("commands", []):
                    if cmd["type"] == "button_press":
                        command = CommandQueue.create_button_press(
                            button=cmd["button"],
                            duration=cmd.get("duration", 0.1),
                            delay=cmd.get("delay", 0.0)
                        )
                        commands.append(command)
                    elif cmd["type"] == "wait":
                        command = CommandQueue.create_wait(
                            duration=cmd["duration"],
                            delay=cmd.get("delay", 0.0)
                        )
                        commands.append(command)
                        
                return commands
                
            except Exception as e:
                logger.error(f"Error parsing menu navigation commands: {e}")
                return []
                
        except Exception as e:
            logger.error(f"Error generating menu navigation: {e}")
            return [] 