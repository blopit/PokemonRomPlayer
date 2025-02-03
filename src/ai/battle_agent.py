from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from utils.logger import logger
from emulator.interface import EmulatorInterface
from emulator.game_state import GameState, GameMode, Pokemon, BattleState
from .agent import Agent, AgentAction

@dataclass
class BattleStrategy:
    """Configuration for battle decision making."""
    aggressive: bool = True  # Prefer attacking over status moves
    switch_threshold: float = 0.3  # HP percentage to trigger switching
    use_items: bool = True  # Whether to use items in battle
    catch_wild: bool = True  # Whether to try catching wild Pokemon

class BattleAgent(Agent):
    """Agent responsible for handling Pokemon battles."""
    
    # Action types
    ATTACK = "attack"
    SWITCH = "switch"
    USE_ITEM = "use_item"
    RUN = "run"
    CATCH = "catch"
    
    def __init__(self, emulator: EmulatorInterface, strategy: Optional[BattleStrategy] = None):
        """Initialize the battle agent.
        
        Args:
            emulator: EmulatorInterface instance
            strategy: Optional battle strategy configuration
        """
        super().__init__(emulator, name="BattleAgent")
        self.strategy = strategy or BattleStrategy()
    
    def analyze_state(self, state: GameState) -> Optional[AgentAction]:
        """Analyze the battle state and decide on an action.
        
        Args:
            state: Current game state
            
        Returns:
            Action to take in battle
        """
        if not state.is_in_battle() or state.battle is None:
            return None
        
        # Get battle participants
        active_pokemon = state.battle.active_pokemon
        opponent = state.battle.opponent_pokemon
        
        if active_pokemon is None or opponent is None:
            logger.error("Battle state missing Pokemon data")
            return None
        
        # Check if we should try to catch the Pokemon
        if (self.strategy.catch_wild and 
            state.battle.is_wild_battle and 
            self._should_catch_pokemon(opponent)):
            return AgentAction(
                action_type=self.CATCH,
                parameters={},
                priority=3
            )
        
        # Check if we need to switch Pokemon
        if (active_pokemon.hp / active_pokemon.max_hp <= self.strategy.switch_threshold and
            self._has_healthy_pokemon(state)):
            switch_target = self._choose_switch_target(state, opponent)
            if switch_target is not None:
                return AgentAction(
                    action_type=self.SWITCH,
                    parameters={"target_index": switch_target},
                    priority=2
                )
        
        # Choose best move
        best_move = self._choose_best_move(active_pokemon, opponent)
        if best_move is not None:
            return AgentAction(
                action_type=self.ATTACK,
                parameters={"move_index": best_move},
                priority=1
            )
        
        # If no good options, try to run from wild battles
        if state.battle.is_wild_battle:
            return AgentAction(
                action_type=self.RUN,
                parameters={},
                priority=0
            )
        
        return None
    
    def execute_action(self, action: AgentAction) -> bool:
        """Execute a battle action.
        
        Args:
            action: Action to execute
            
        Returns:
            True if action was successful
        """
        try:
            if action.action_type == self.ATTACK:
                return self._execute_attack(action.parameters["move_index"])
            
            elif action.action_type == self.SWITCH:
                return self._execute_switch(action.parameters["target_index"])
            
            elif action.action_type == self.USE_ITEM:
                return self._execute_use_item(
                    action.parameters["item_id"],
                    action.parameters.get("target_index")
                )
            
            elif action.action_type == self.RUN:
                return self._execute_run()
            
            elif action.action_type == self.CATCH:
                return self._execute_catch()
            
            else:
                logger.error(f"Unknown action type: {action.action_type}")
                return False
            
        except Exception as e:
            self.handle_error(e)
            return False
    
    def _should_catch_pokemon(self, pokemon: Pokemon) -> bool:
        """Determine if we should try to catch a Pokemon.
        
        Args:
            pokemon: The opponent Pokemon
            
        Returns:
            True if we should try to catch it
        """
        # TODO: Implement catch decision logic
        return True
    
    def _has_healthy_pokemon(self, state: GameState) -> bool:
        """Check if we have any healthy Pokemon to switch to.
        
        Args:
            state: Current game state
            
        Returns:
            True if we have healthy Pokemon
        """
        if not state.player.party:
            return False
        
        return any(p for p in state.player.party 
                  if not p.is_fainted() and 
                  p.hp / p.max_hp > self.strategy.switch_threshold)
    
    def _choose_switch_target(self, state: GameState, opponent: Pokemon) -> Optional[int]:
        """Choose the best Pokemon to switch to.
        
        Args:
            state: Current game state
            opponent: Opponent's Pokemon
            
        Returns:
            Index of Pokemon to switch to, or None if no good target
        """
        # TODO: Implement switch target selection logic
        return None
    
    def _choose_best_move(self, active: Pokemon, opponent: Pokemon) -> Optional[int]:
        """Choose the best move to use.
        
        Args:
            active: Our active Pokemon
            opponent: Opponent's Pokemon
            
        Returns:
            Index of move to use, or None if no good moves
        """
        # TODO: Implement move selection logic
        return 0 if active.moves else None
    
    def _execute_attack(self, move_index: int) -> bool:
        """Execute an attack move.
        
        Args:
            move_index: Index of move to use
            
        Returns:
            True if successful
        """
        try:
            # Navigate to move
            self.emulator.press_button('a')  # Enter fight menu
            
            # Select move (assuming default cursor position)
            if move_index == 1:
                self.emulator.press_button('right')
            elif move_index == 2:
                self.emulator.press_button('down')
            elif move_index == 3:
                self.emulator.press_button('right')
                self.emulator.press_button('down')
            
            # Execute move
            self.emulator.press_button('a')
            return True
            
        except Exception as e:
            logger.error(f"Error executing attack: {e}")
            return False
    
    def _execute_switch(self, target_index: int) -> bool:
        """Execute a Pokemon switch.
        
        Args:
            target_index: Index of Pokemon to switch to
            
        Returns:
            True if successful
        """
        try:
            # Open Pokemon menu
            self.emulator.press_buttons(['select', 'right'])
            
            # Navigate to target Pokemon
            for _ in range(target_index):
                self.emulator.press_button('down')
            
            # Select Pokemon
            self.emulator.press_button('a')
            return True
            
        except Exception as e:
            logger.error(f"Error executing switch: {e}")
            return False
    
    def _execute_use_item(self, item_id: int, target_index: Optional[int] = None) -> bool:
        """Execute using an item.
        
        Args:
            item_id: ID of item to use
            target_index: Optional target Pokemon index
            
        Returns:
            True if successful
        """
        # TODO: Implement item usage
        return False
    
    def _execute_run(self) -> bool:
        """Execute running from battle.
        
        Returns:
            True if successful
        """
        try:
            # Navigate to Run option
            self.emulator.press_button('right')
            self.emulator.press_button('down')
            
            # Select Run
            self.emulator.press_button('a')
            return True
            
        except Exception as e:
            logger.error(f"Error executing run: {e}")
            return False
    
    def _execute_catch(self) -> bool:
        """Execute catching a Pokemon.
        
        Returns:
            True if successful
        """
        try:
            # Navigate to Bag
            self.emulator.press_button('right')
            
            # Select Pokeballs pocket
            self.emulator.press_button('a')
            
            # Select first available ball
            self.emulator.press_button('a')
            
            # Confirm throw
            self.emulator.press_button('a')
            return True
            
        except Exception as e:
            logger.error(f"Error executing catch: {e}")
            return False 