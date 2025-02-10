"""
Image Processor Tool

This module provides a CrewAI tool interface for processing game screenshots,
performing OCR, and extracting game state information.
"""

import os
import cv2
import numpy as np
import pytesseract
from PIL import Image
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from utils.logger import get_logger
from utils.llm_api import get_provider

logger = get_logger("crew")

@dataclass
class ImageProcessorConfig:
    """Configuration for image processing."""
    ocr_lang: str = "eng"  # Language for OCR
    min_confidence: float = 0.6  # Minimum confidence for OCR results
    max_retries: int = 3
    retry_delay: float = 0.5
    # Regions of interest for different UI elements (x, y, width, height)
    roi_map: Dict[str, Tuple[int, int, int, int]] = field(default_factory=lambda: {
        "battle_menu": (160, 120, 80, 40),  # Battle menu region
        "dialog_box": (0, 120, 240, 40),    # Dialog box region
        "hp_bars": (0, 0, 240, 40),         # HP bars region
        "move_list": (120, 120, 120, 40)    # Move list region
    })

class ImageProcessorTool:
    """Tool for processing game screenshots and extracting information."""
    
    def __init__(self, config: Optional[ImageProcessorConfig] = None):
        """Initialize the image processor tool.
        
        Args:
            config: Tool configuration
        """
        self.config = config or ImageProcessorConfig()
        self.llm = get_provider("openai")  # Use OpenAI for image analysis
        logger.info("Initialized image processor tool")
        
    def load_image(self, image_path: str) -> Optional[np.ndarray]:
        """Load an image from file.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Loaded image as numpy array if successful, None otherwise
        """
        try:
            if not os.path.exists(image_path):
                logger.error(f"Image file not found: {image_path}")
                return None
                
            img = cv2.imread(image_path)
            if img is None:
                logger.error(f"Failed to load image: {image_path}")
                return None
                
            return img
            
        except Exception as e:
            logger.error(f"Error loading image: {e}")
            return None
            
    def extract_text(self, img: np.ndarray, region: Optional[Tuple[int, int, int, int]] = None) -> str:
        """Extract text from an image region using OCR.
        
        Args:
            img: Input image
            region: Optional region of interest (x, y, width, height)
            
        Returns:
            Extracted text string
        """
        try:
            # Crop to region if specified
            if region:
                x, y, w, h = region
                img = img[y:y+h, x:x+w]
                
            # Convert to PIL Image for Tesseract
            pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
            
            # Extract text with confidence check
            result = pytesseract.image_to_data(
                pil_img,
                lang=self.config.ocr_lang,
                output_type=pytesseract.Output.DICT
            )
            
            # Filter by confidence
            text_parts = []
            for i, conf in enumerate(result["conf"]):
                if conf > self.config.min_confidence * 100:  # Confidence is 0-100
                    text_parts.append(result["text"][i])
                    
            return " ".join(text_parts)
            
        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            return ""
            
    def detect_battle_state(self, img: np.ndarray) -> Dict[str, Any]:
        """Detect battle-related information from the game screen.
        
        Args:
            img: Input image
            
        Returns:
            Dictionary containing battle state information
        """
        try:
            battle_info = {}
            
            # Extract text from battle menu
            menu_text = self.extract_text(img, self.config.roi_map["battle_menu"])
            battle_info["menu_text"] = menu_text
            
            # Extract text from move list
            moves_text = self.extract_text(img, self.config.roi_map["move_list"])
            battle_info["moves"] = [m.strip() for m in moves_text.split() if m.strip()]
            
            # TODO: Add HP bar detection
            # TODO: Add Pokemon sprite detection
            
            return battle_info
            
        except Exception as e:
            logger.error(f"Error detecting battle state: {e}")
            return {}
            
    def detect_dialog(self, img: np.ndarray) -> Optional[str]:
        """Detect and extract dialog text from the game screen.
        
        Args:
            img: Input image
            
        Returns:
            Extracted dialog text if found, None otherwise
        """
        try:
            dialog_text = self.extract_text(img, self.config.roi_map["dialog_box"])
            return dialog_text if dialog_text.strip() else None
            
        except Exception as e:
            logger.error(f"Error detecting dialog: {e}")
            return None
            
    def analyze_game_state(self, image_path: str) -> Dict[str, Any]:
        """Analyze the game state from a screenshot.
        
        Args:
            image_path: Path to the screenshot
            
        Returns:
            Dictionary containing analyzed game state information
        """
        try:
            # Load image
            img = self.load_image(image_path)
            if img is None:
                return {}
                
            # Analyze different aspects of the game state
            state_info = {
                "battle_state": self.detect_battle_state(img),
                "dialog": self.detect_dialog(img),
                "timestamp": os.path.getctime(image_path)
            }
            
            # Use LLM to analyze the overall state
            prompt = """Analyze this Pokemon game screenshot and identify:
            1. Current game mode (battle, overworld, menu)
            2. Important UI elements visible
            3. Any text or numbers visible
            4. Current situation or context
            
            Return your analysis in a structured format."""
            
            try:
                llm_analysis = self.llm.query(prompt, image=image_path)
                state_info["llm_analysis"] = llm_analysis
            except Exception as e:
                logger.warning(f"LLM analysis failed: {e}")
                
            return state_info
            
        except Exception as e:
            logger.error(f"Error analyzing game state: {e}")
            return {}
            
    def __str__(self) -> str:
        """Get string representation of the tool.
        
        Returns:
            Tool description string
        """
        return "Image Processor Tool - Analyzes game screenshots and extracts information" 