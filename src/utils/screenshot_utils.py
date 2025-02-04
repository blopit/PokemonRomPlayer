"""
Screenshot Utilities Module

This module provides utilities for capturing and analyzing game screenshots.
"""

import os
import time
import cv2
import numpy as np
import pyautogui
import platform
from pathlib import Path
from typing import Optional, Dict, Any
import logging

from utils.logger import get_logger

# Get logger for this module
logger = get_logger("pokemon_player")

def take_screenshot_sync(window_title=None, output_path=None, width=None, height=None):
    """Take a screenshot of the game window.
    
    Args:
        window_title (str): Title of the window to capture. Not used on macOS.
        output_path (str): Path to save the screenshot.
        width (int): Width to resize the screenshot to.
        height (int): Height to resize the screenshot to.
        
    Returns:
        str: Path to the saved screenshot.
    """
    try:
        # Create screenshots directory if it doesn't exist
        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
        else:
            screenshots_dir = Path("screenshots")
            screenshots_dir.mkdir(exist_ok=True)
            timestamp = int(time.time() * 1000)  # Use milliseconds for uniqueness
            output_path = str(screenshots_dir / f"screenshot_{timestamp}.png")
            
        # Take screenshot
        screenshot = pyautogui.screenshot()
        screenshot.save(output_path)
        logger.info(f"Screenshot saved to {output_path}")
            
        # Resize if dimensions are provided
        if width is not None and height is not None:
            img = cv2.imread(output_path)
            img = cv2.resize(img, (width, height))
            cv2.imwrite(output_path, img)
                
        return output_path
            
    except Exception as e:
        logger.error(f"Error taking screenshot: {str(e)}")
        raise

def analyze_screenshot(image_path, prompt):
    """Analyze a screenshot using OpenAI's vision model.
    
    Args:
        image_path (str): Path to the screenshot image.
        prompt (str): Prompt for the vision model.
        
    Returns:
        str: Analysis result from the vision model.
    """
    try:
        from utils.llm_api import query_llm
        
        # Read image
        with open(image_path, 'rb') as f:
            image_data = f.read()
            
        # Query vision model
        response = query_llm(prompt, provider="openai", image_path=image_path)
        return response
        
    except Exception as e:
        logger.error(f"Error analyzing screenshot: {str(e)}")
        raise

def detect_game_state(image_path):
    """Detect the current game state from a screenshot.
    
    Args:
        image_path (str): Path to the screenshot image.
        
    Returns:
        dict: Detected game state information.
    """
    prompt = """Analyze this Pokemon game screenshot and tell me:
    1. What is the current game state (battle, menu, dialog, overworld)?
    2. What specific elements are visible on screen?
    3. Are there any Pokemon visible?
    4. Is there any text visible?
    """
    return analyze_screenshot(image_path, prompt)

def analyze_battle_state(image_path):
    """Analyze the battle state from a screenshot.
    
    Args:
        image_path (str): Path to the screenshot image.
        
    Returns:
        dict: Battle state information.
    """
    prompt = """Analyze this Pokemon battle screenshot and tell me:
    1. Which Pokemon are battling?
    2. What are their HP levels?
    3. What moves are available?
    4. Are there any status conditions?
    """
    return analyze_screenshot(image_path, prompt)

def read_dialog_text(image_path):
    """Extract dialog text from a screenshot.
    
    Args:
        image_path (str): Path to the screenshot image.
        
    Returns:
        str: Extracted dialog text.
    """
    prompt = "Read and transcribe any dialog text visible in this Pokemon game screenshot."
    return analyze_screenshot(image_path, prompt)

def analyze_menu_state(image_path):
    """Analyze the menu state from a screenshot.
    
    Args:
        image_path (str): Path to the screenshot image.
        
    Returns:
        dict: Menu state information.
    """
    prompt = """Analyze this Pokemon menu screenshot and tell me:
    1. Which menu is currently open?
    2. What options are available?
    3. Which option is currently selected?
    """
    return analyze_screenshot(image_path, prompt) 