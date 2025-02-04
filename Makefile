# Makefile for Pokemon ROM Player Automation

# Usage:
#   make run [ROM=path/to/your_rom.gba] [EMULATOR_PATH=/path/to/mGBA] [DEBUG=--debug]

DEBUG_FLAG := $(DEBUG)
ROM_ARG ?= roms/moemon star em v1.1c.gba
EMULATOR_ARG := $(EMULATOR_PATH)

.PHONY: run
run:
	venv/bin/python run_game.py "$(ROM_ARG)" --emulator-path "$(EMULATOR_ARG)" $(DEBUG_FLAG)

# Example:
#   make run ROM='roms/moemon star em v1.1c.gba' EMULATOR_PATH=/Applications/mGBA.app/Contents/MacOS/mGBA DEBUG=--debug
