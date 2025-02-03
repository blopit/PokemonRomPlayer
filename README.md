# Pokemon ROM Player

An advanced Pokemon ROM player system with AI capabilities that can autonomously play through Pokemon games, complete the Pokedex, and train Pokemon.

## Features

- Automated gameplay through Pokemon games
- Battle AI with strategic decision making
- Automatic Pokemon catching and Pokedex completion
- Pokemon training and leveling system
- Save state management
- Configurable AI behaviors
- Detailed logging and progress tracking

## Requirements

- Python 3.10 or higher
- mGBA emulator
- Pokemon ROM file (not included)
- Required Python packages (see `requirements.txt`)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/PokemonRomPlayer.git
cd PokemonRomPlayer
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

4. Install mGBA:
```bash
# On macOS with Homebrew:
brew install mgba

# On Ubuntu/Debian:
sudo apt-get install mgba

# On Windows:
# Download from https://mgba.io/downloads.html
```

## Configuration

1. Create a configuration file (or modify the default `config.json`):
```json
{
    "emulator": {
        "executable_path": "mgba",
        "window_title": "mGBA",
        "save_state_dir": "saves"
    },
    "game": {
        "rom_path": "path/to/your/pokemon.gba",
        "game_version": "emerald",
        "save_file_path": null
    },
    "ai": {
        "battle_strategy": "aggressive",
        "catch_strategy": "all",
        "training_strategy": "efficient"
    }
}
```

2. Ensure your ROM file is in the correct location and update the configuration accordingly.

## Usage

Run the program with default configuration:
```bash
python src/main.py
```

Run with specific ROM file and save directory:
```bash
python src/main.py --rom path/to/rom.gba --save-dir path/to/saves
```

Additional options:
```bash
python src/main.py --help
```

## Project Structure

```
PokemonRomPlayer/
├── src/
│   ├── ai/            # AI decision making and strategies
│   ├── emulator/      # Emulator interface and game state
│   ├── utils/         # Utility functions and helpers
│   └── tests/         # Test files
├── logs/              # Log files
├── saves/             # Save states
├── config.json        # Configuration file
└── requirements.txt   # Python dependencies
```

## Development

### Running Tests
```bash
pytest src/tests/
```

### Code Style
The project uses:
- Black for code formatting
- Flake8 for linting
- MyPy for type checking

Run style checks:
```bash
black src/
flake8 src/
mypy src/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This project is for educational purposes only. Pokemon is a registered trademark of Nintendo/Creatures Inc./GAME FREAK inc. This project is not affiliated with or endorsed by Nintendo, Creatures Inc., or GAME FREAK inc.
