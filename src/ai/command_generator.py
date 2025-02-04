"""
Command generation for game automation
"""

from typing import List, Dict, Any, Optional
import json
import os
from utils.command_queue import CommandQueue, GameCommand
from utils.logger import get_logger
from utils.llm_api import get_provider

logger = get_logger("pokemon_player")

SYSTEM_PROMPT = """You are an expert Pokemon game automation system. Your role is to control a Pokemon game by generating sequences of button commands to achieve objectives.

Your capabilities:
1. Button presses: a, b, start, select, up, down, left, right
2. Timing control: You can specify duration of button presses and delays between actions

Your responsibilities:
1. Navigate menus and dialogues efficiently
2. Handle battles strategically
3. Manage inventory and Pokemon party
4. Progress through the game story
5. Catch and train Pokemon
6. Handle error cases and unexpected states

Guidelines:
1. Generate commands in batches of 5-10 to reduce API calls
2. Include appropriate delays between actions (0.1s for quick presses, longer for animations)
3. Group related commands together (e.g. menu navigation sequences)
4. Always provide reasoning for your command choices
5. Consider the current game state and context for decision making
6. Handle edge cases and potential errors
7. Optimize for efficient progress while maintaining reliability

IMPORTANT: You must respond with a valid JSON object containing 'commands' and 'reasoning' fields. Each command must have 'type', 'button'/'duration', and optional 'delay' fields."""

USER_PROMPT = """Based on the current game state, generate the next batch of commands.

Current screen state:
{screen_state}

Game context:
{context}

You must respond with a valid JSON object in this exact format:
{{
    "commands": [
        {{"type": "button_press", "button": "a", "duration": 0.1, "delay": 0.0}},
        {{"type": "wait", "duration": 0.5, "delay": 0.0}},
        ...
    ],
    "reasoning": "Detailed explanation of why these commands were chosen"
}}"""

class CommandGenerator:
    """Generates game commands based on screen state"""
    
    def __init__(self, provider: str = "openai"):
        """Initialize command generator.
        
        Args:
            provider: LLM provider to use (always openai)
        """
        self.llm = get_provider("openai")  # Force OpenAI
        
    def generate_commands(self, screen_state: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> List[GameCommand]:
        """Generate commands based on current state.
        
        Args:
            screen_state: Current screen analysis results
            context: Optional additional context
            
        Returns:
            List of commands to execute
        """
        try:
            # Format prompt with current state
            prompt = self._format_prompt(screen_state, context)
            
            # Get commands from OpenAI
            response = self.llm.query(prompt)
            
            # Parse commands
            return self._parse_commands(response)
            
        except Exception as e:
            logger.error(f"Error generating commands: {e}")
            return self._generate_fallback_commands(screen_state)
            
    def _generate_fallback_commands(self, screen_state: Dict[str, Any]) -> List[GameCommand]:
        """Generate basic navigation commands when LLM is unavailable.
        
        Args:
            screen_state: Current screen analysis results
            
        Returns:
            List of basic navigation commands
        """
        # Basic navigation - press A to advance text/menus
        return [
            CommandQueue.create_button_press("a", duration=0.1, delay=0.5)
        ]
        
    def _format_prompt(self, screen_state: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> str:
        """Format prompt for LLM.
        
        Args:
            screen_state: Current screen analysis results
            context: Optional additional context
            
        Returns:
            Formatted prompt string
        """
        return f"""You are a Pokemon game expert. Generate commands to progress through the game.

Current screen state:
{screen_state}

Context:
{context or {}}

Generate a sequence of button presses to advance the game. Consider:
1. Current screen type (battle, menu, overworld)
2. Text boxes and dialog
3. Menu navigation
4. Battle actions

Return your response in this exact format:
{{
    "commands": [
        {{"type": "button_press", "button": "up", "duration": 0.1, "delay": 0.0}},
        {{"type": "button_press", "button": "a", "duration": 0.1, "delay": 0.2}},
        ...
    ],
    "reasoning": "Explanation of command sequence"
}}"""
        
    def _parse_commands(self, response: str) -> List[GameCommand]:
        """Parse LLM response into commands.
        
        Args:
            response: LLM response string
            
        Returns:
            List of parsed commands
        """
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
                logger.info(f"Command generation reasoning: {data['reasoning']}")
                
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
            logger.error(f"Error parsing commands: {e}")
            return self._generate_fallback_commands({}) 