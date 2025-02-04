"""
Keyboard Input Module

This module provides functionality for simulating keyboard input on macOS using the Quartz framework.
"""

import time
import logging
import subprocess
from typing import Optional
from Quartz import (
    CGEventCreateKeyboardEvent,
    CGEventPostToPid,
    CGEventSetFlags,
    kCGHIDEventTap,
    kCGEventFlagMaskCommand
)

logger = logging.getLogger(__name__)

# Mapping of characters to macOS virtual key codes (US layout)
VK_MAP = {
    'a': 0, 's': 1, 'd': 2, 'f': 3, 'h': 4, 'g': 5, 'z': 6, 'x': 7, 'c': 8, 'v': 9,
    'b': 11, 'q': 12, 'w': 13, 'e': 14, 'r': 15, 'y': 16, 't': 17, '1': 18, '2': 19,
    '3': 20, '4': 21, '6': 22, '5': 23, '=': 24, '9': 25, '7': 26, '-': 27, '8': 28,
    '0': 29, ']': 30, 'o': 31, 'u': 32, '[': 33, 'i': 34, 'p': 35, 'l': 37, 'j': 38,
    "'": 39, 'k': 40, ';': 41, '\\': 42, ',': 43, '/': 44, 'n': 45, 'm': 46, '.': 47,
    ' ': 49
}

# Default key mappings for mGBA
KEY_MAPPINGS = {
    'up': 'up',
    'down': 'down',
    'left': 'left',
    'right': 'right',
    'a': 'x',
    'b': 'z',
    'start': 'return',
    'select': 'tab'
}

def get_pid(app_name: str) -> int:
    """Get the process ID of a running application.
    
    Args:
        app_name: Name of the application (must match exactly)
        
    Returns:
        Process ID if found, None otherwise
    """
    script = f'tell application "System Events" to get unix id of process "{app_name}"'
    result = subprocess.run(["osascript", "-e", script],
                          capture_output=True, text=True)
    try:
        return int(result.stdout.strip())
    except ValueError:
        print(f"Could not find process: {app_name}")
        return None

def send_key(pid: int, key_code: int, key_down: bool, flags: int = 0) -> None:
    """Send a keyboard event to a process.
    
    Args:
        pid: Target process ID
        key_code: Virtual key code
        key_down: True for key press, False for release
        flags: Event flags (e.g., for modifier keys)
    """
    event = CGEventCreateKeyboardEvent(None, key_code, key_down)
    if flags:
        CGEventSetFlags(event, flags)
    CGEventPostToPid(pid, event)

def send_cmd_enter(pid: int) -> None:
    """Send Cmd+Enter key combination to a process.
    
    Args:
        pid: Target process ID
    """
    CMD_KEY_CODE = 55  # Virtual key code for left Command
    ENTER_KEY_CODE = 36  # Virtual key code for Return/Enter
    modifier_flag = kCGEventFlagMaskCommand

    send_key(pid, CMD_KEY_CODE, True)
    time.sleep(0.01)
    send_key(pid, ENTER_KEY_CODE, True, flags=modifier_flag)
    time.sleep(0.01)
    send_key(pid, ENTER_KEY_CODE, False, flags=modifier_flag)
    time.sleep(0.01)
    send_key(pid, CMD_KEY_CODE, False)

def send_string(pid: int, text: str, delay_between_keys: float = 0.05) -> None:
    """Simulate typing a string by sending key events.
    
    Args:
        pid: Target process ID
        text: String to type
        delay_between_keys: Delay between keystrokes in seconds
    """
    for char in text:
        char_lower = char.lower()
        if char_lower in VK_MAP:
            vk = VK_MAP[char_lower]
            send_key(pid, vk, True)
            time.sleep(0.01)
            send_key(pid, vk, False)
            time.sleep(delay_between_keys)
        else:
            print(f"Character '{char}' not mapped. Skipping.")
            time.sleep(delay_between_keys)

def send_key_to_pid(pid: int, key: str, duration: float = 0.1) -> bool:
    """
    Send a keyboard input to a specific process.
    
    Args:
        pid: Process ID to send key to
        key: Key to send
        duration: How long to hold the key
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Map the key if it's in our mappings
        mapped_key = KEY_MAPPINGS.get(key.lower(), key)
        
        # Use osascript to send the key event
        script = f'''
        tell application "System Events"
            tell process "mGBA"
                key down "{mapped_key}"
                delay {duration}
                key up "{mapped_key}"
            end tell
        end tell
        '''
        result = subprocess.run(['osascript', '-e', script], 
                              capture_output=True, text=True)
                              
        if result.returncode != 0:
            logger.error(f"Failed to send key: {result.stderr}")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"Error sending key: {e}")
        return False

def send_string(text: str, delay: float = 0.1) -> bool:
    """
    Send a string of text as keyboard input.
    
    Args:
        text: String to send
        delay: Delay between characters
        
    Returns:
        True if successful, False otherwise
    """
    try:
        script = f'''
        tell application "System Events"
            keystroke "{text}" delay {delay}
        end tell
        '''
        result = subprocess.run(['osascript', '-e', script],
                              capture_output=True, text=True)
                              
        if result.returncode != 0:
            logger.error(f"Failed to send string: {result.stderr}")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"Error sending string: {e}")
        return False

class KeyboardAutomator:
    """Class for automating keyboard input."""
    
    def __init__(self, app_name: str):
        """Initialize the automator.
        
        Args:
            app_name: Target application name
        """
        self.app_name = app_name
        self.pid = get_pid(app_name)
        self.running = False
        self.threads = []
    
    def start_cmd_enter_task(self, interval_seconds: float = 11) -> None:
        """Start sending periodic Cmd+Enter.
        
        Args:
            interval_seconds: Interval between commands in seconds
        """
        def task():
            while self.running:
                send_cmd_enter(self.pid)
                time.sleep(interval_seconds)
                print("CMD + ENTER")
        
        thread = threading.Thread(target=task)
        thread.daemon = True
        self.threads.append(thread)
        thread.start()
    
    def start_continue_task(self, interval_minutes: float = 2, 
                          message: str = "continue", 
                          delay_between_keys: float = 0.05) -> None:
        """Start sending periodic continue messages.
        
        Args:
            interval_minutes: Interval between messages in minutes
            message: Message to send
            delay_between_keys: Delay between keystrokes in seconds
        """
        def task():
            while self.running:
                send_string(self.pid, message, delay_between_keys)
                send_key(self.pid, 36, True)  # Enter key
                time.sleep(0.01)
                send_key(self.pid, 36, False)
                time.sleep(interval_minutes * 60)
                print("=== continue ===")
        
        thread = threading.Thread(target=task)
        thread.daemon = True
        self.threads.append(thread)
        thread.start()
    
    def start(self) -> bool:
        """Start the automation.
        
        Returns:
            True if started successfully, False otherwise
        """
        if self.pid is None:
            print(f"Could not find process: {self.app_name}")
            return False
        
        print(f"Target app '{self.app_name}' (pid: {self.pid}) found.")
        self.running = True
        return True
    
    def stop(self) -> None:
        """Stop the automation."""
        self.running = False
        for thread in self.threads:
            thread.join(timeout=1.0)
        self.threads.clear() 