"""
Memory reader for accessing mGBA emulator memory
"""

import os
import platform
import subprocess
import struct
from typing import Optional, Dict, Any, List, Union
from utils.logger import get_logger
from emulator.memory_map import MemoryMap, GameVersion

logger = get_logger("pokemon_player")

class MemoryReader:
    """Reads memory from mGBA emulator process"""
    
    def __init__(self, pid: int, version: GameVersion = GameVersion.EMERALD):
        """Initialize memory reader.
        
        Args:
            pid: Process ID of mGBA emulator
            version: Pokemon game version
        """
        self.pid = pid
        self.memory_map = MemoryMap(version)
        self.is_macos = platform.system() == "Darwin"
        
    def read_memory(self, address: int, size: int) -> bytes:
        """Read raw memory from emulator.
        
        Args:
            address: Memory address to read
            size: Number of bytes to read
            
        Returns:
            Raw bytes from memory
        """
        try:
            if self.is_macos:
                # Use lldb on macOS
                cmd = [
                    'lldb',
                    '-p', str(self.pid),
                    '-o', f'memory read --size {size} --format x --count 1 {hex(address)}',
                    '-o', 'quit'
                ]
            else:
                # Use gdb on Linux/Windows
                cmd = [
                    'gdb',
                    '-p', str(self.pid),
                    '-ex', f'x/{size}xb {hex(address)}',
                    '-ex', 'quit'
                ]
                
            result = subprocess.check_output(cmd, stderr=subprocess.PIPE)
            
            # Parse output and extract bytes
            # TODO: Implement proper parsing based on debugger output format
            return result
            
        except Exception as e:
            logger.error(f"Error reading memory at {hex(address)}: {e}")
            raise
            
    def read_game_state(self) -> Dict[str, Any]:
        """Read current game state.
        
        Returns:
            Dictionary containing game state data
        """
        try:
            state = {
                "game_state": self.read_u32(self.memory_map.addresses.game_state),
                "battle_type": self.read_u32(self.memory_map.addresses.battle_type),
                "menu_state": self.read_u32(self.memory_map.addresses.menu_state),
                "player": {
                    "x": self.read_u16(self.memory_map.addresses.player_x),
                    "y": self.read_u16(self.memory_map.addresses.player_y),
                    "direction": self.read_u8(self.memory_map.addresses.player_direction),
                    "money": self.read_u32(self.memory_map.addresses.player_money)
                }
            }
            return state
            
        except Exception as e:
            logger.error(f"Error reading game state: {e}")
            return {}
            
    def read_party_data(self) -> Dict[str, Any]:
        """Read Pokemon party data.
        
        Returns:
            Dictionary containing party data
        """
        try:
            party_count = self.read_u8(self.memory_map.addresses.party_count)
            party = []
            
            for i in range(party_count):
                addr = self.memory_map.calculate_party_pokemon_address(i)
                pokemon = self.read_pokemon_data(addr)
                party.append(pokemon)
                
            return {
                "count": party_count,
                "pokemon": party
            }
            
        except Exception as e:
            logger.error(f"Error reading party data: {e}")
            return {"count": 0, "pokemon": []}
            
    def read_pokemon_data(self, address: int) -> Dict[str, Any]:
        """Read Pokemon data structure.
        
        Args:
            address: Memory address of Pokemon data
            
        Returns:
            Dictionary containing Pokemon data
        """
        try:
            data = {}
            for field, offset, size in self.memory_map.get_pokemon_data_structure():
                addr = address + offset
                if field == "moves":
                    moves = []
                    for j in range(4):
                        move_addr = addr + (j * 2)
                        moves.append(self.read_u16(move_addr))
                    data[field] = moves
                elif field == "pp":
                    pp = []
                    for j in range(4):
                        pp_addr = addr + j
                        pp.append(self.read_u8(pp_addr))
                    data[field] = pp
                elif size == 1:
                    data[field] = self.read_u8(addr)
                elif size == 2:
                    data[field] = self.read_u16(addr)
                    
            return data
            
        except Exception as e:
            logger.error(f"Error reading Pokemon data at {hex(address)}: {e}")
            return {}
            
    def read_u8(self, address: int) -> int:
        """Read unsigned 8-bit value."""
        data = self.read_memory(address, 1)
        return struct.unpack('B', data)[0]
        
    def read_u16(self, address: int) -> int:
        """Read unsigned 16-bit value."""
        data = self.read_memory(address, 2)
        return struct.unpack('H', data)[0]
        
    def read_u32(self, address: int) -> int:
        """Read unsigned 32-bit value."""
        data = self.read_memory(address, 4)
        return struct.unpack('I', data)[0] 