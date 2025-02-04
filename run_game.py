
#!/usr/bin/env python3
"""
Pokemon ROM Player Entry Point

This script provides a simple interface to run the Pokemon ROM automation.
"""

import os
import sys
import time
import argparse
import logging
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).resolve().parent / "src"
sys.path.append(str(src_dir))

from automation.game_loop import GameLoop
from utils.logger import setup_logging

def main():
    parser = argparse.ArgumentParser(description="Pokemon ROM Player Automation")
    parser.add_argument("rom_path", help="Path to Pokemon ROM file")
    parser.add_argument("--emulator-path", help="Path to mGBA executable", default=None)
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    setup_logging(level=log_level)
    logger = logging.getLogger(__name__)

    # Print welcome message
    print("\n=== Pokemon ROM Player Automation ===")
    print("\nMake sure:")
    print("1. mGBA emulator is running")
    print("2. Pokemon ROM is loaded")
    print("3. Game window is visible and not minimized")
    print("\nControls:")
    print("- Press Ctrl+C to stop the automation")
    print("\nStarting in 5 seconds...")
    time.sleep(5)

    try:
        # Create and run automation
        automation = GameLoop(args.rom_path, args.emulator_path)
        automation.start()

    except KeyboardInterrupt:
        print("\nStopping automation...")
    except Exception as e:
        logger.error(f"Error running automation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 