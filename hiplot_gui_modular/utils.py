"""
Utility functions for the HiPlot GUI application.
"""
import os
import sys
import time
import tkinter as tk


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
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


def is_text_input(widget):
    """True for widgets where typed keys are text (so they must not trigger searching)"""
    try:
        return widget.winfo_class() in ('Entry', 'TEntry', 'Text', 'Spinbox', 'TSpinbox', 'TCombobox')
    except (AttributeError, tk.TclError):
        return False


def is_search_key(event):
    """A printable key without Ctrl/Alt (Ctrl+C etc. keep working)"""
    CONTROL, ALT = 0x0004, 0x20000  # Windows modifier bits in event.state
    return (len(event.char) == 1 and event.char.isprintable()
            and not (event.state & (CONTROL | ALT)))


def find_name_match(names, typed, current_index=None):
    """Index of the item to jump to for typed text, or None.

    Repeating one letter ('c', 'cc', 'ccc') cycles through names starting with
    it, after the current item. Otherwise: first name starting with the text,
    else first name containing it. Case is ignored.
    """
    if not typed:
        return None
    lowered = [str(n).lower() for n in names]
    typed = typed.lower()

    if len(typed) > 1 and len(set(typed)) == 1:
        letter = typed[0]
        start = -1 if current_index is None else current_index
        order = list(range(start + 1, len(lowered))) + list(range(0, start + 1))
        for i in order:
            if lowered[i].startswith(letter):
                return i
        return None

    for i, name in enumerate(lowered):
        if name.startswith(typed):
            return i
    for i, name in enumerate(lowered):
        if typed in name:
            return i
    return None


class TypeAhead:
    """Type a name in a list or dropdown to jump to the first match.

    Keys typed within RESET_MS of each other build up one search ('c', 'co',
    'con'...); after a pause the next key starts a new search.
    """
    RESET_MS = 1000

    def __init__(self, widget):
        self.widget = widget
        self.typed = ""
        self.last_key_time = 0
        widget.bind("<Key>", self._on_key, add="+")
        if isinstance(widget, tk.Listbox):
            # A Listbox only receives keys when focused; clicking it should focus it
            widget.bind("<Button-1>", lambda e: widget.focus_set(), add="+")
        else:
            self._bind_combobox_popdown()

    def _bind_combobox_popdown(self):
        """While a dropdown is open its list is a separate widget - search there too"""
        try:
            popdown = self.widget.tk.eval(f"ttk::combobox::PopdownWindow {self.widget}")
            self.widget.tk.call("bind", f"{popdown}.f.l", "<Key>",
                                "+" + self.widget.register(self._on_popdown_key) + " %A %s")
        except tk.TclError:
            pass  # unknown Tk version: searching still works while the dropdown is closed

    def _on_popdown_key(self, char, state):
        class KeyEvent:
            pass
        event = KeyEvent()
        event.char, event.state = char, int(state)
        index = self._search(event)
        if index is not None:
            popdown_list = self.widget.tk.eval(f"ttk::combobox::PopdownWindow {self.widget}") + ".f.l"
            self.widget.tk.call(popdown_list, "selection", "clear", 0, "end")
            self.widget.tk.call(popdown_list, "selection", "set", index)
            self.widget.tk.call(popdown_list, "activate", index)
            self.widget.tk.call(popdown_list, "see", index)

    def _items(self):
        if isinstance(self.widget, tk.Listbox):
            return list(self.widget.get(0, tk.END))
        return list(self.widget.cget("values") or ())

    def _current_index(self):
        if isinstance(self.widget, tk.Listbox):
            selection = self.widget.curselection()
            return selection[0] if selection else None
        current = self.widget.current()
        return current if current >= 0 else None

    def _search(self, event):
        """Update the typed text and return the matching index (or None)"""
        if not is_search_key(event):
            return None
        now = time.monotonic() * 1000
        if now - self.last_key_time > self.RESET_MS:
            self.typed = ""
        self.last_key_time = now
        self.typed += event.char
        return find_name_match(self._items(), self.typed, self._current_index())

    def _on_key(self, event):
        index = self._search(event)
        if index is None:
            return None
        if isinstance(self.widget, tk.Listbox):
            self.widget.selection_clear(0, tk.END)
            self.widget.selection_set(index)
            self.widget.activate(index)
            self.widget.see(index)
            self.widget.event_generate("<<ListboxSelect>>")
        else:
            self.widget.current(index)
            self.widget.event_generate("<<ComboboxSelected>>")
        return "break"


def add_type_ahead(*widgets):
    """Attach type-to-jump searching to Listboxes and Comboboxes"""
    for widget in widgets:
        if widget is not None:
            widget._type_ahead = TypeAhead(widget)


def grab_when_visible(window):
    """Make a dialog modal once it is on screen.

    grab_set() fails with "window not viewable" if called before the window
    manager has mapped the window (e.g. when opened from a double-click).
    """
    try:
        window.wait_visibility()
        window.grab_set()
    except tk.TclError:
        pass


def get_text_width_estimate(text, font_size=8):
    """Estimate the width needed for text display"""
    return max(6, min(25, int(len(str(text)) * 0.6) + 1))


def configure_window_size(root, num_columns, base_width=750, base_height=650):
    """Configure window size based on number of columns"""
    if num_columns > 15:
        new_width = min(900, base_width + (num_columns - 15) * 5)
        new_height = min(800, base_height + (num_columns // 8) * 25)
        root.geometry(f"{new_width}x{new_height}")

