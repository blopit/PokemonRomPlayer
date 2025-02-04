"""
Screenshot utilities for capturing game state
"""

import cv2
import numpy as np
import pyautogui
from PIL import Image
import platform
import subprocess
import tempfile
import os
import time
from utils.logger import get_logger

logger = get_logger("pokemon_player")

def capture_window(pid: int = None, max_retries: int = 3) -> np.ndarray:
    """Capture screenshot of a specific window.
    
    Args:
        pid: Process ID of window to capture (optional)
        max_retries: Maximum number of retry attempts for screenshot capture
        
    Returns:
        Numpy array containing the screenshot
    """
    last_error = None
    for attempt in range(max_retries):
        try:
            # Create temp file for screenshot
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                temp_path = tmp.name
                
            if platform.system() == "Darwin":
                if pid:
                    # Focus window using AppleScript with error handling
                    script = """
                    tell application "System Events"
                        try
                            # Get all processes
                            set allProcesses to every process whose unix id is %d
                            
                            # If process found, focus its window
                            if (count of allProcesses) > 0 then
                                set mgbaProcess to item 1 of allProcesses
                                set frontmost of mgbaProcess to true
                                delay 0.5
                                
                                # Get all windows
                                set allWindows to every window of mgbaProcess
                                
                                # If window found, get its properties
                                if (count of allWindows) > 0 then
                                    set mgbaWindow to item 1 of allWindows
                                    
                                    # Get window properties
                                    set windowBounds to get size of mgbaWindow
                                    set windowPosition to get position of mgbaWindow
                                    
                                    # Log window info for debugging
                                    log "Window Title: " & name of mgbaWindow
                                    log "Position: " & (item 1 of windowPosition as string) & ", " & (item 2 of windowPosition as string)
                                    log "Size: " & (item 1 of windowBounds as string) & ", " & (item 2 of windowBounds as string)
                                    
                                    return {item 1 of windowPosition, item 2 of windowPosition, item 1 of windowBounds, item 2 of windowBounds}
                                else
                                    error "No windows found for process"
                                end if
                            else
                                error "Process not found"
                            end if
                        on error errMsg
                            return "error:" & errMsg
                        end try
                    end tell
                    """ % pid
                    
                    # Get window bounds
                    result = subprocess.check_output(['osascript', '-e', script]).decode().strip()
                    
                    if result.startswith("error:"):
                        raise Exception(f"AppleScript error: {result[6:]}")
                    
                    # Parse the last line which contains the coordinates
                    lines = result.splitlines()
                    coords = lines[-1]
                    x, y, width, height = map(int, coords.split(', '))
                    
                    logger.info(f"Capturing window at x={x}, y={y}, width={width}, height={height}")
                    
                    # Take screenshot of the specific region
                    subprocess.run(['screencapture', '-R%d,%d,%d,%d' % (x, y, width, height), temp_path], check=True)
                else:
                    # Take screenshot of focused window
                    subprocess.run(['screencapture', '-w', temp_path], check=True)
                
            else:
                # For other platforms, use pyautogui
                screenshot = pyautogui.screenshot()
                screenshot.save(temp_path)
                
            # Read and process the image
            img = cv2.imread(temp_path)
            if img is None:
                raise Exception("Failed to read screenshot")
                
            # Remove temp file
            os.unlink(temp_path)
            
            return img
            
        except Exception as e:
            last_error = e
            logger.warning(f"Screenshot attempt {attempt + 1} failed: {e}")
            time.sleep(0.5)  # Wait before retry
            
    logger.error(f"All screenshot attempts failed. Last error: {last_error}")
    raise last_error

def crop_to_ratio(img: np.ndarray, target_width: int, target_height: int) -> np.ndarray:
    """Crop image to match target aspect ratio.
    
    Args:
        img: Input image array
        target_width: Target width
        target_height: Target height
        
    Returns:
        Cropped and resized image array
    """
    try:
        # Get image dimensions
        height, width = img.shape[:2]
        logger.debug(f"Input dimensions: {width}x{height}")
        
        # Calculate target ratio
        target_ratio = target_width / target_height
        current_ratio = width / height
        
        if current_ratio > target_ratio:
            # Image is too wide
            new_width = int(height * target_ratio)
            x = (width - new_width) // 2
            y = 0
            w = new_width
            h = height
        else:
            # Image is too tall
            new_height = int(width / target_ratio)
            x = 0
            y = (height - new_height) // 2
            w = width
            h = new_height
            
        # Crop image
        cropped = img[y:y+h, x:x+w]
        
        # Resize to target dimensions
        resized = cv2.resize(cropped, (target_width, target_height))
        
        logger.debug(f"Output dimensions: {target_width}x{target_height}")
        return resized
        
    except Exception as e:
        logger.error(f"Error cropping image: {e}")
        raise

def take_screenshot(output_dir="screenshots"):
    """
    Take a screenshot of the mGBA emulator window.
    If the emulator window is not found, take a screenshot of the active window.
    
    Args:
        output_dir (str): Directory to save screenshots
        
    Returns:
        str: Path to the saved screenshot, or None if failed
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Take screenshot using pyautogui with retry
        for attempt in range(3):
            try:
                # Take screenshot of the entire screen
                screenshot = pyautogui.screenshot()
                
                # Save screenshot with timestamp
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                output_path = os.path.join(output_dir, f"screenshot_{timestamp}.png")
                screenshot.save(output_path)
                
                logger.info(f"Screenshot saved to {output_path}")
                return output_path
                
            except Exception as e:
                logger.warning(f"Screenshot attempt {attempt + 1} failed: {e}")
                if attempt < 2:  # Don't sleep on last attempt
                    time.sleep(0.5)
                    
        logger.error("All screenshot attempts failed")
        return None
            
    except Exception as e:
        logger.error(f"Error taking screenshot: {str(e)}")
        return None

def get_latest_screenshot(output_dir="screenshots"):
    """
    Get the path to the most recent screenshot.
    
    Args:
        output_dir (str): Directory containing screenshots
        
    Returns:
        str: Path to the latest screenshot, or None if no screenshots exist
    """
    try:
        if not os.path.exists(output_dir):
            logger.error(f"Screenshot directory {output_dir} does not exist")
            return None
            
        screenshots = [f for f in os.listdir(output_dir) if f.startswith("screenshot_") and f.endswith(".png")]
        if not screenshots:
            logger.error("No screenshots found")
            return None
            
        latest = max(screenshots, key=lambda x: os.path.getctime(os.path.join(output_dir, x)))
        return os.path.join(output_dir, latest)
        
    except Exception as e:
        logger.error(f"Error getting latest screenshot: {str(e)}")
        return None 