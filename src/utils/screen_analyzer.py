import cv2
import numpy as np
from typing import Optional, Tuple, List
import pytesseract
from PIL import Image

class ScreenAnalyzer:
    """Analyzes screenshots from the emulator for game state information."""
    
    # Screen regions of interest (ROIs) for different game elements
    BATTLE_TEXT_ROI = (136, 384, 368, 416)  # Region for battle text
    MENU_ROI = (0, 320, 240, 416)          # Region for menu options
    HP_BAR_ROI = (128, 64, 240, 80)        # Region for HP bar in battle
    
    def __init__(self):
        """Initialize the screen analyzer."""
        self.previous_frame = None
        self.frame_diff_threshold = 30  # Threshold for detecting screen changes
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for better text recognition.
        
        Args:
            image: Input image in BGR format
            
        Returns:
            Preprocessed image
        """
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply thresholding to get black text on white background
        _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
        
        return thresh
    
    def extract_text(self, image: np.ndarray, roi: Optional[Tuple[int, int, int, int]] = None) -> str:
        """Extract text from a specific region of the screen.
        
        Args:
            image: Screenshot image
            roi: Optional region of interest (x1, y1, x2, y2)
            
        Returns:
            Extracted text
        """
        if roi:
            x1, y1, x2, y2 = roi
            image = image[y1:y2, x1:x2]
        
        # Preprocess image
        processed = self.preprocess_image(image)
        
        # Convert to PIL Image for Tesseract
        pil_image = Image.fromarray(processed)
        
        # Extract text
        text = pytesseract.image_to_string(pil_image, config='--psm 6')
        return text.strip()
    
    def detect_screen_change(self, current_frame: np.ndarray) -> bool:
        """Detect if the screen has changed significantly.
        
        Args:
            current_frame: Current screenshot
            
        Returns:
            True if significant change detected
        """
        if self.previous_frame is None:
            self.previous_frame = current_frame
            return True
        
        # Calculate frame difference
        diff = cv2.absdiff(current_frame, self.previous_frame)
        mean_diff = np.mean(diff)
        
        # Update previous frame
        self.previous_frame = current_frame
        
        return mean_diff > self.frame_diff_threshold
    
    def detect_battle_state(self, image: np.ndarray) -> bool:
        """Detect if the game is in a battle state.
        
        Args:
            image: Screenshot image
            
        Returns:
            True if in battle state
        """
        # Extract battle text region
        battle_text = self.extract_text(image, self.BATTLE_TEXT_ROI)
        
        # Check for common battle text patterns
        battle_indicators = [
            "wild", "appeared", "wants to fight", "sent out",
            "used", "foe", "trainer"
        ]
        
        return any(indicator.lower() in battle_text.lower() 
                  for indicator in battle_indicators)
    
    def get_hp_percentage(self, image: np.ndarray) -> float:
        """Calculate the HP percentage from the HP bar.
        
        Args:
            image: Screenshot image
            
        Returns:
            HP percentage (0-100)
        """
        # Extract HP bar region
        hp_region = image[self.HP_BAR_ROI[1]:self.HP_BAR_ROI[3],
                         self.HP_BAR_ROI[0]:self.HP_BAR_ROI[2]]
        
        # Convert to HSV and isolate green/yellow/red components
        hsv = cv2.cvtColor(hp_region, cv2.COLOR_BGR2HSV)
        
        # Create mask for HP bar colors
        lower_green = np.array([40, 40, 40])
        upper_red = np.array([180, 255, 255])
        mask = cv2.inRange(hsv, lower_green, upper_red)
        
        # Calculate percentage of filled HP bar
        total_pixels = mask.size
        filled_pixels = np.count_nonzero(mask)
        
        return (filled_pixels / total_pixels) * 100 if total_pixels > 0 else 0
    
    def get_menu_options(self, image: np.ndarray) -> List[str]:
        """Extract menu options from the screen.
        
        Args:
            image: Screenshot image
            
        Returns:
            List of menu option texts
        """
        # Extract menu region
        menu_text = self.extract_text(image, self.MENU_ROI)
        
        # Split into lines and clean up
        options = [line.strip() for line in menu_text.split('\n') if line.strip()]
        return options 