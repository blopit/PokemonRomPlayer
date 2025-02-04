#!/usr/bin/env python3
"""
Keyboard Automation Script

This script automates keyboard input for the Pokemon ROM Player.
"""

import sys
import time
import argparse
from pathlib import Path

# Add the src directory to the Python path
src_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(src_dir))

from utils.keyboard_input import KeyboardAutomator

def main():
    parser = argparse.ArgumentParser(description='Keyboard automation for Pokemon ROM Player')
    parser.add_argument('--app', default='mGBA', help='Target application name')
    parser.add_argument('--cmd-enter-interval', type=float, default=11,
                       help='Interval between CMD+ENTER commands in seconds')
    parser.add_argument('--continue-interval', type=float, default=2,
                       help='Interval between continue messages in minutes')
    parser.add_argument('--message', default='continue',
                       help='Message to send periodically')
    args = parser.parse_args()

    automator = KeyboardAutomator(args.app)
    if not automator.start():
        sys.exit(1)

    try:
        automator.start_cmd_enter_task(args.cmd_enter_interval)
        automator.start_continue_task(args.continue_interval, args.message)
        
        print(f"Running automation for {args.app}:")
        print(f"- CMD+ENTER every {args.cmd_enter_interval} seconds")
        print(f"- Sending '{args.message}' every {args.continue_interval} minutes")
        print("Press Ctrl+C to stop")
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping automation...")
        automator.stop()
        print("Done.")

if __name__ == '__main__':
    main() 