"""
Launch the ISO Piping Automation GUI.
Usage:  python run_gui.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from gui.app import launch

if __name__ == "__main__":
    launch()
