import os
import base64
from openai import OpenAI
from utils.screenshot import take_screenshot, get_latest_screenshot

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def encode_image_to_base64(image_path):
    """Convert an image to base64 string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_game_state():
    """Take a screenshot and analyze the game state using GPT-4 Vision."""
    # Take screenshot
    screenshot_path = take_screenshot()
    if not screenshot_path:
        print("Failed to capture screenshot")
        return
    
    print(f"Screenshot captured: {screenshot_path}")
    
    # Convert to base64
    try:
        base64_image = encode_image_to_base64(screenshot_path)
    except Exception as e:
        print(f"Error encoding image: {str(e)}")
        return
    
    # Create message with image
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Please analyze this Pokemon game screenshot and tell me what's happening in the game. Is there a battle? What Pokemon are visible? What options are available?"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64_image}"
                    }
                }
            ]
        }
    ]
    
    # Get response from GPT-4 Vision
    try:
        response = client.chat.completions.create(
            model="gpt-4-vision-preview",  # Model with vision capabilities
            messages=messages,
            max_tokens=1024
        )
        print("\nGPT-4 Vision Analysis:")
        print(response.choices[0].message.content)
        
    except Exception as e:
        print(f"Error getting analysis: {str(e)}")
        print("Response details:")
        if hasattr(e, 'response'):
            print(e.response.json())

if __name__ == "__main__":
    analyze_game_state() 