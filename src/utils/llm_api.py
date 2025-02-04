"""
LLM API Module

This module provides a unified interface for interacting with various LLM providers.
"""

import os
import base64
from typing import Optional, Dict, Any, Tuple
from pathlib import Path
import requests
import json
from dotenv import load_dotenv
import cv2
import numpy as np

from utils.logger import get_logger

# Load environment variables
load_dotenv()

# Get logger for this module
logger = get_logger("llm")

def resize_image(image_path: str, max_size: Tuple[int, int] = (1024, 1024)) -> np.ndarray:
    """Resize an image while maintaining aspect ratio.
    
    Args:
        image_path: Path to the image file
        max_size: Maximum width and height
        
    Returns:
        Resized image as numpy array
    """
    # Read image
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Could not read image: {image_path}")
    
    # Calculate target size
    h, w = image.shape[:2]
    scale = min(max_size[0] / w, max_size[1] / h)
    
    # Only resize if image is too large
    if scale < 1:
        new_size = (int(w * scale), int(h * scale))
        image = cv2.resize(image, new_size, interpolation=cv2.INTER_AREA)
    
    return image

def encode_image(image: np.ndarray) -> str:
    """Encode image as base64 string.
    
    Args:
        image: Image as numpy array
        
    Returns:
        Base64 encoded image string
    """
    # Convert to PNG format
    success, buffer = cv2.imencode(".png", image)
    if not success:
        raise ValueError("Failed to encode image")
    
    # Convert to base64
    return base64.b64encode(buffer).decode("utf-8")

class LLMProvider:
    """Base class for LLM providers."""
    
    def __init__(self):
        """Initialize the LLM provider."""
        pass
    
    def query(self, prompt: str, system_prompt: Optional[str] = None, image_path: Optional[str] = None) -> str:
        """Query the LLM with a prompt and optional image.
        
        Args:
            prompt: The prompt to send to the LLM
            system_prompt: Optional system prompt to set context
            image_path: Optional path to an image file
            
        Returns:
            LLM response text
        """
        raise NotImplementedError

class OpenAIProvider(LLMProvider):
    """OpenAI API provider."""
    
    def __init__(self):
        """Initialize the OpenAI provider."""
        super().__init__()
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        # Use GPT-4 with vision capabilities
        self.model = "gpt-4o"  # Updated to use the latest GPT-4 model
        self.api_url = "https://api.openai.com/v1/chat/completions"
    
    def query(self, prompt: str, system_prompt: Optional[str] = None, image_path: Optional[str] = None) -> str:
        """Query OpenAI's API.
        
        Args:
            prompt: The prompt to send
            system_prompt: Optional system prompt to set context
            image_path: Optional path to an image file
            
        Returns:
            Response text
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Start with system message if provided
        messages = []
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        # Add user message
        if image_path:
            # Resize and encode image
            try:
                image = resize_image(image_path)
                image_data = encode_image(image)
                messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_data}"
                            }
                        }
                    ]
                })
            except Exception as e:
                logger.error(f"Failed to process image: {e}")
                raise
        else:
            messages.append({
                "role": "user",
                "content": prompt
            })
        
        data = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 1000
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenAI API error: {e}")
            raise

class AnthropicProvider(LLMProvider):
    """Anthropic API provider."""
    
    def __init__(self):
        """Initialize the Anthropic provider."""
        super().__init__()
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        
        self.model = "claude-3-sonnet-20240229"
        self.api_url = "https://api.anthropic.com/v1/messages"
    
    def query(self, prompt: str, image_path: Optional[str] = None) -> str:
        """Query Anthropic's API.
        
        Args:
            prompt: The prompt to send
            image_path: Optional path to an image file
            
        Returns:
            Response text
        """
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        # Construct the message content
        content = []
        
        # Add text prompt
        content.append({
            "type": "text",
            "text": prompt
        })
        
        # Add image if provided
        if image_path:
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
                content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": image_data
                    }
                })
        
        data = {
            "model": self.model,
            "messages": [{
                "role": "user",
                "content": content
            }],
            "max_tokens": 1000
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=data)
            response.raise_for_status()
            return response.json()["content"][0]["text"]
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise

def get_provider(provider_name: str) -> LLMProvider:
    """Get an LLM provider instance.
    
    Args:
        provider_name: Name of the provider ("openai" or "anthropic")
        
    Returns:
        LLM provider instance
    """
    providers = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider
    }
    
    if provider_name not in providers:
        raise ValueError(f"Unknown provider: {provider_name}")
    
    return providers[provider_name]()

def query_llm(prompt: str, provider: str = "openai", image_path: Optional[str] = None) -> str:
    """Query an LLM provider.
    
    Args:
        prompt: The prompt to send
        provider: Provider name ("openai" or "anthropic")
        image_path: Optional path to an image file
        
    Returns:
        Response text
    """
    try:
        llm = get_provider(provider)
        return llm.query(prompt, image_path)
    except Exception as e:
        logger.error(f"Error querying LLM: {e}")
        raise 
