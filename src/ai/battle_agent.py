"""
Battle management agent
"""

from typing import List, Dict, Any, Optional
from utils.command_queue import CommandQueue, GameCommand
from utils.logger import get_logger
from ai.agent import Agent
from utils.llm_api import get_provider
import json

logger = get_logger("pokemon_player")

BATTLE_PROMPT = """You are a Pokemon battle expert. Your task is to make strategic battle decisions based on the current state.

Current screen state:
{screen_state}

Game state:
{game_state}

Battle context:
{context}

Generate battle commands considering:
1. Type matchups
2. Move effectiveness
3. Pokemon stats and status
4. HP management
5. Strategic switching
6. Item usage

Return your response in this exact format:
{
    "commands": [
        {"type": "button_press", "button": "up", "duration": 0.1, "delay": 0.0},
        {"type": "button_press", "button": "a", "duration": 0.1, "delay": 0.2},
        ...
    ],
    "reasoning": "Explanation of battle strategy and move choices"
}"""

class BattleAgent(Agent):
    """Agent specialized in battle management"""
    
    def __init__(self, provider: str = "openai"):
        """Initialize battle agent.
        
        Args:
            provider: LLM provider to use
        """
        super().__init__("BattleAgent")
        self.llm = get_provider(provider)
        
    def can_handle(self, screen_state: Dict[str, Any], game_state: Dict[str, Any]) -> bool:
        """Check if current state is a battle that needs handling.
        
        Args:
            screen_state: Current screen analysis results
            game_state: Current game memory state
            
        Returns:
            True if in a battle state
        """
        # Check if in battle based on screen analysis
        if screen_state.get("screen_type") == "battle":
            return True
            
        # Check if in battle based on memory
        if game_state.get("battle_type"):
            return True
            
        return False
        
    def generate_commands(self, 
                         screen_state: Dict[str, Any],
                         game_state: Dict[str, Any],
                         context: Optional[Dict[str, Any]] = None) -> List[GameCommand]:
        """Generate battle commands.
        
        Args:
            screen_state: Current screen analysis results
            game_state: Current game memory state
            context: Optional additional context
            
        Returns:
            List of commands for battle actions
        """
        try:
            # Enrich context with battle-specific info
            battle_context = context or {}
            if game_state:
                # Add active Pokemon data
                active_pokemon = game_state.get("active_pokemon", {})
                battle_context["active_pokemon"] = active_pokemon
                
                # Add opponent Pokemon data
                opponent_pokemon = game_state.get("opponent_pokemon", {})
                battle_context["opponent_pokemon"] = opponent_pokemon
                
                # Add party status
                party_data = game_state.get("party", {})
                battle_context["party"] = party_data
            
            # Format prompt with current state
            prompt = BATTLE_PROMPT.format(
                screen_state=screen_state,
                game_state=game_state,
                context=battle_context
            )
            
            # Get battle commands from LLM
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
                    logger.info(f"Battle strategy reasoning: {data['reasoning']}")
                    
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
                logger.error(f"Error parsing battle commands: {e}")
                return []
                
        except Exception as e:
            logger.error(f"Error generating battle strategy: {e}")
            return [] 