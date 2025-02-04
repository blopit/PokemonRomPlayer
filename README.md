# Pokemon ROM Player

An AI-powered automation system for playing Pokemon games using computer vision and LLM-based decision making.

## Setup

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Install mGBA emulator:
- Download from: https://mgba.io/downloads.html
- Install and make sure it's working

3. Prepare your Pokemon ROM:
- Load your Pokemon ROM in mGBA
- Make sure the game is running and visible

## Usage

Run the automation:
```bash
python run_game.py
```

Optional arguments:
- `--window`: Emulator window name (default: "mGBA")
- `--debug`: Enable debug logging

Example with options:
```bash
python run_game.py --window "mGBA" --debug
```

## How it Works

The system uses a sense-process-actuate loop:

1. **Sense**: Captures screenshots of the game window
2. **Process**: Uses AI to analyze the game state and decide actions
3. **Actuate**: Executes actions via keyboard inputs

The AI will:
- Complete the main story campaign
- Catch Pokemon to complete the Pokedex
- Level up caught Pokemon

## Controls

- Press Ctrl+C to stop the automation

## Project Structure

```
.
├── run_game.py          # Main entry point
├── src/
│   ├── automation/      # Core automation logic
│   ├── utils/          # Utility functions
│   └── ai/             # AI/ML components
├── data/
│   └── screenshots/    # Captured screenshots
└── requirements.txt    # Python dependencies
```

## Requirements

- Python 3.8+
- mGBA emulator
- Pokemon ROM (not provided)
- macOS (for keyboard control)

## Debugging

Screenshots are saved in `data/screenshots/` for debugging.
Enable debug logging with `--debug` for more detailed output.
