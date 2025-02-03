import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

class PokemonROMLogger:
    """Custom logger for the Pokemon ROM player."""
    
    # Log format with timestamps, level, and module information
    LOG_FORMAT = '%(asctime)s - %(levelname)s - %(module)s - %(message)s'
    
    # Default log levels for different outputs
    CONSOLE_LEVEL = logging.INFO
    FILE_LEVEL = logging.DEBUG
    
    def __init__(self, name: str = "PokemonROM", log_dir: Optional[str] = None):
        """Initialize the logger.
        
        Args:
            name: Logger name
            log_dir: Optional directory for log files
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Create log directory if specified
        self.log_dir = Path(log_dir) if log_dir else Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        
        # Clear any existing handlers
        self.logger.handlers.clear()
        
        # Set up handlers
        self._setup_console_handler()
        self._setup_file_handler()
        
        self.logger.info("Logger initialized")
    
    def _setup_console_handler(self) -> None:
        """Set up console output handler."""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.CONSOLE_LEVEL)
        console_formatter = logging.Formatter(self.LOG_FORMAT)
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
    
    def _setup_file_handler(self) -> None:
        """Set up file output handler."""
        # Create log file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.log_dir / f"pokemon_rom_{timestamp}.log"
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(self.FILE_LEVEL)
        file_formatter = logging.Formatter(self.LOG_FORMAT)
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
    
    def debug(self, message: str) -> None:
        """Log debug message.
        
        Args:
            message: Debug message to log
        """
        self.logger.debug(message)
    
    def info(self, message: str) -> None:
        """Log info message.
        
        Args:
            message: Info message to log
        """
        self.logger.info(message)
    
    def warning(self, message: str) -> None:
        """Log warning message.
        
        Args:
            message: Warning message to log
        """
        self.logger.warning(message)
    
    def error(self, message: str) -> None:
        """Log error message.
        
        Args:
            message: Error message to log
        """
        self.logger.error(message)
    
    def critical(self, message: str) -> None:
        """Log critical message.
        
        Args:
            message: Critical message to log
        """
        self.logger.critical(message)
    
    def exception(self, message: str) -> None:
        """Log exception message with traceback.
        
        Args:
            message: Exception message to log
        """
        self.logger.exception(message)

# Create global logger instance
logger = PokemonROMLogger() 