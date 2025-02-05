"""
Test script for webhook handler functionality
"""

import os
from utils.webhook_handler import WebhookHandler
from utils.command_queue import CommandQueue
from utils.input_handler import InputHandler

def main():
    # Initialize handlers
    webhook = WebhookHandler()
    command_queue = CommandQueue()
    input_handler = InputHandler()
    
    # Get latest screenshot from screenshots directory
    screenshot_dir = "screenshots"
    screenshots = [f for f in os.listdir(screenshot_dir) if f.endswith('.png')]
    if not screenshots:
        print("No screenshots found")
        return
        
    # Sort by timestamp and get latest
    latest = sorted(screenshots, reverse=True)[0]
    screenshot_path = os.path.join(screenshot_dir, latest)
    print(f"Processing latest screenshot: {latest}")
    
    # Process screenshot and get commands
    success = webhook.process_screenshot_to_queue(screenshot_path, command_queue)
    if not success:
        print("Failed to process screenshot")
        return
        
    # Print commands that will be executed
    print("\nCommands to execute:")
    for cmd in command_queue.commands:
        print(f"- {cmd.command_type}: {cmd.args} (delay: {cmd.delay}s)")
        
    # Focus emulator window
    if not input_handler.focus_window("mGBA"):
        print("Failed to focus emulator window")
        return
        
    # Process commands
    print("\nExecuting commands...")
    command_queue.process_commands(input_handler)
    print("Done!")

if __name__ == "__main__":
    main() 