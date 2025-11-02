"""
Utility functions for the HiPlot GUI application.
"""
import os
import sys
import tkinter as tk


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class ToolTipHelper:
    """Helper class for creating tooltips on widgets"""
    
    @staticmethod
    def create_tooltip(widget, text):
        """Create a tooltip for a widget to show full text on hover"""
        
        def enter(event):
            try:
                x, y, _, _ = widget.bbox("insert")
            except tk.TclError:
                # If bbox fails, use widget position
                x, y = 25, 25
            
            x += widget.winfo_rootx() + 25
            y += widget.winfo_rooty() + 25
            
            # Create a toplevel window
            tooltip = tk.Toplevel(widget)
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{x}+{y}")
            
            # Create tooltip content
            label = tk.Label(tooltip, text=text, justify='left',
                            background="#ffffe0", relief="solid", borderwidth=1,
                            font=("TkDefaultFont", "8", "normal"))
            label.pack(ipadx=3, ipady=1)
            
            # Store tooltip reference to destroy it later
            widget._tooltip = tooltip
        
        def leave(event):
            if hasattr(widget, '_tooltip'):
                widget._tooltip.destroy()
                delattr(widget, '_tooltip')
        
        # Bind events to widget
        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)


def get_text_width_estimate(text, font_size=8):
    """Estimate the width needed for text display"""
    return max(6, min(25, int(len(str(text)) * 0.6) + 1))


def configure_window_size(root, num_columns, base_width=750, base_height=650):
    """Configure window size based on number of columns"""
    if num_columns > 15:
        new_width = min(900, base_width + (num_columns - 15) * 5)
        new_height = min(800, base_height + (num_columns // 8) * 25)
        root.geometry(f"{new_width}x{new_height}")

