"""
Main entry point for the HiPlot GUI application.

This script initializes and runs the modular HiPlot GUI application.
Run this file to start the application.
"""
import tkinter as tk
import sys
import os

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main_gui import HiPlotGUI


def main():
    """Main entry point for the application"""
    root = tk.Tk()
    app = HiPlotGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
