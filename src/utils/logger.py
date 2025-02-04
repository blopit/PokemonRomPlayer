"""
Enhanced logging utility for the Pokemon ROM Player.
"""

import logging
import logging.handlers
import os
from typing import Dict, Optional
import colorlog
from pathlib import Path
import sys

# Default logging configuration
DEFAULT_CONFIG = {
    "level": "INFO",
    "file": "logs/pokemon_player.log",
    "console": True,
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "date_format": "%Y-%m-%d %H:%M:%S",
    "components": {
        "emulator": "INFO",
        "ai": "INFO",
        "battle": "INFO",
        "navigation": "INFO",
        "memory": "INFO",
        "input": "INFO",
        "screen": "INFO"
    }
}

class PokemonLogger:
    """Enhanced logger with support for multiple outputs and colored console logging."""
    
    # ANSI color codes for different log levels
    COLORS = {
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red,bg_white',
    }
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the logger with configuration.
        
        Args:
            config: Optional logging configuration dictionary
        """
        self.config = config or DEFAULT_CONFIG
        self.loggers: Dict[str, logging.Logger] = {}
        
        # Create logs directory if it doesn't exist
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Set up main logger
        self.setup_main_logger()
        
        # Set up component loggers
        if "separate_files" in self.config:
            for component, log_file in self.config["separate_files"].items():
                self.setup_component_logger(component, log_file)
    
    def setup_main_logger(self) -> None:
        """Set up the main logger with console and file output."""
        logger = logging.getLogger("pokemon_player")
        logger.setLevel(self.config.get("level", "INFO"))
        
        # Remove any existing handlers
        logger.handlers = []
        
        # Console handler with colors
        if self.config.get("console", True):
            console_handler = colorlog.StreamHandler()
            console_handler.setFormatter(colorlog.ColoredFormatter(
                "%(log_color)s" + self.config.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
                datefmt=self.config.get("date_format", "%Y-%m-%d %H:%M:%S"),
                log_colors=self.COLORS
            ))
            logger.addHandler(console_handler)
        
        # File handler with rotation
        if "file" in self.config:
            file_handler = logging.handlers.RotatingFileHandler(
                self.config["file"],
                maxBytes=self.config.get("file_rotation", {}).get("max_bytes", 10485760),
                backupCount=self.config.get("file_rotation", {}).get("backup_count", 5)
            )
            file_handler.setFormatter(logging.Formatter(
                self.config.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
                datefmt=self.config.get("date_format", "%Y-%m-%d %H:%M:%S")
            ))
            logger.addHandler(file_handler)
        
        self.loggers["main"] = logger
    
    def setup_component_logger(self, component: str, log_file: str) -> None:
        """Set up a logger for a specific component.
        
        Args:
            component: Name of the component
            log_file: Path to the log file
        """
        logger = logging.getLogger(f"pokemon_player.{component}")
        level = self.config.get("components", {}).get(component, "INFO")
        logger.setLevel(level)
        
        # Remove any existing handlers
        logger.handlers = []
        
        # Create directory if needed
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=self.config.get("file_rotation", {}).get("max_bytes", 10485760),
            backupCount=self.config.get("file_rotation", {}).get("backup_count", 5)
        )
        file_handler.setFormatter(logging.Formatter(
            self.config.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
            datefmt=self.config.get("date_format", "%Y-%m-%d %H:%M:%S")
        ))
        logger.addHandler(file_handler)
        
        self.loggers[component] = logger
    
    def get_logger(self, component: Optional[str] = None) -> logging.Logger:
        """Get a logger for a specific component.
        
        Args:
            component: Optional component name
            
        Returns:
            Logger instance
        """
        if component is None:
            return self.loggers["main"]
        return self.loggers.get(component, self.loggers["main"])

# Global logger instance
_logger_instance: Optional[PokemonLogger] = None

def init_logger(config: Optional[Dict] = None) -> None:
    """Initialize the global logger instance.
    
    Args:
        config: Optional logging configuration dictionary
    """
    global _logger_instance
    _logger_instance = PokemonLogger(config)

def get_logger(component: Optional[str] = None) -> logging.Logger:
    """Get a logger instance.
    
    Args:
        component: Optional component name
        
    Returns:
        Logger instance
    """
    global _logger_instance
    if _logger_instance is None:
        init_logger()
    return _logger_instance.get_logger(component)

def setup_logger(debug: bool = False) -> None:
    """Set up logging configuration.
    
    Args:
        debug: Whether to enable debug logging
    """
    config = DEFAULT_CONFIG.copy()
    if debug:
        config["level"] = "DEBUG"
        for component in config["components"]:
            config["components"][component] = "DEBUG"
    init_logger(config)

# Initialize default logger
init_logger()

def setup_logging(level=logging.INFO):
    """Set up logging configuration.
    
    Args:
        level: Logging level (default: INFO)
    """
    # Create logs directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(logs_dir / "pokemon_player.log")
        ]
    )

# Create logger for this module
logger = logging.getLogger(__name__) 