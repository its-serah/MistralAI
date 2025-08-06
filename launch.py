#!/usr/bin/env python3
"""
Simple launcher script for MistralAI Audio Analysis Tool

This script allows you to run the tool without installation:
python launch.py analyze audio.wav
python launch.py chat
"""

import sys
import os

# Add src directory to Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(script_dir, 'src')
sys.path.insert(0, src_dir)

# Import and run the CLI
if __name__ == "__main__":
    try:
        from src.cli.main import main
        main()
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you have installed the required dependencies:")
        print("pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
