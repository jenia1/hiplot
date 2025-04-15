import hiplot as hip
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, simpledialog
from pathlib import Path
import os
import webbrowser
import math
import numpy as np
import re
import sys

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class HiPlotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Mr.Spaghetti 🤌")
        
        # Set the window icon for title bar and taskbar
        try:
            # For Windows and most systems
            icon_path = resource_path('spaghetti.ico')
            self.root.iconbitmap(icon_path)
        except tk.TclError:
            try:
                # Alternative method that works on more platforms
                icon_path = resource_path('spaghetti.png')
                icon_img = tk.PhotoImage(file=icon_path)
                self.root.tk.call('wm', 'iconphoto', self.root._w, icon_img)
            except Exception as e:
                print(f"Failed to set icon: {e}")
        
        self.root.geometry("750x650")
        self.csv_file_path = None
        self.output_directory = os.getcwd()  # Default to current directory
        self.html_filename = "hiplot_visualization.html"
        self.df_columns = []
        self.active_columns = {}  # Dictionary to track which columns are active
        self.column_buttons = {}  # Dictionary to track column buttons by column name
        self.column_mapping = {}  # To track original column names to renamed ones
        self.df = None  # DataFrame to store the CSV data
        
        # Pagination settings
        self.rows_per_page = 100
        self.current_page = 0
        self.total_pages = 1
        
        # Create GUI elements
        self.setup_ui()
    
    def setup_ui(self):
        # Create a main frame inside the root window with scrolling capability
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Add a canvas inside the main frame
        self.canvas = tk.Canvas(self.main_frame)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Add a scrollbar to the canvas
        self.scrollbar = ttk.Scrollbar(self.main_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Add mouse wheel scroll event
        self.canvas.bind_all("<MouseWheel>", lambda event: self.canvas.yview_scroll(int(-1*(event.delta/120)), "units"))
        
        # Create a frame inside the canvas for all content
        self.content_frame = tk.Frame(self.canvas)
        self.canvas_frame = self.canvas.create_window((0, 0), window=self.content_frame, anchor="nw")
        
        # Configure canvas to resize with window and update scrollregion when content changes
        self.content_frame.bind("<Configure>", self.on_frame_configure)
        self.canvas.bind("<Configure>", self.on_canvas_configure)
        
        # Frame for file selection
        file_frame = tk.LabelFrame(self.content_frame, text="Input File", padx=15, pady=15)
        file_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Load CSV button
        self.load_btn = tk.Button(file_frame, text="Load CSV File", command=self.load_csv, width=20, height=2)
        self.load_btn.pack(pady=5)
        
        # Label to show selected file
        self.file_label = tk.Label(file_frame, text="No file selected", wraplength=550)
        self.file_label.pack(pady=5)
        
        # Column selection frame
        self.columns_frame = tk.LabelFrame(
            self.content_frame, 
            text="Column Selection (green = visible, gray = hidden, right-click for options)", 
            padx=15, pady=15
        )
        self.columns_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # This will be populated after a CSV is loaded
        self.columns_grid_frame = tk.Frame(self.columns_frame)
        self.columns_grid_frame.pack(fill=tk.BOTH, expand=True)
        
        # Add Column Expression Button Frame
        add_column_frame = tk.Frame(self.content_frame)
        add_column_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Add Column Button
        self.add_column_btn = tk.Button(
            add_column_frame, 
            text="Add Column with Expression", 
            command=self.show_add_column_dialog,
            width=25,
            state=tk.DISABLED
        )
        self.add_column_btn.pack(side=tk.LEFT, padx=10)
        
        # Add tooltip-like info button or text
        tk.Label(
            add_column_frame, 
            text="(e.g., 'col1 + col2', 'col1 * 2', 'np.log(col1)')", 
            fg="gray"
        ).pack(side=tk.LEFT, padx=5)
        
        # Output settings frame
        output_frame = tk.LabelFrame(self.content_frame, text="Output Settings", padx=15, pady=15)
        output_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Output directory selection
        tk.Label(output_frame, text="Save Directory:").grid(row=0, column=0, sticky="w", pady=5)
        
        output_dir_frame = tk.Frame(output_frame)
        output_dir_frame.grid(row=0, column=1, sticky="w", pady=5)
        
        self.output_dir_var = tk.StringVar(value=self.output_directory)
        self.output_dir_entry = tk.Entry(output_dir_frame, textvariable=self.output_dir_var, width=40)
        self.output_dir_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        self.browse_dir_btn = tk.Button(output_dir_frame, text="Browse...", command=self.browse_output_dir)
        self.browse_dir_btn.pack(side=tk.LEFT)
        
        # HTML filename
        tk.Label(output_frame, text="HTML Filename:").grid(row=1, column=0, sticky="w", pady=5)
        self.filename_var = tk.StringVar(value=self.html_filename)
        self.filename_entry = tk.Entry(output_frame, textvariable=self.filename_var, width=40)
        self.filename_entry.grid(row=1, column=1, sticky="w", pady=5)
        
        # Configuration frame for visualization options
        config_frame = tk.LabelFrame(self.content_frame, text="Visualization Options", padx=15, pady=15)
        config_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Color by selection dropdown
        tk.Label(config_frame, text="Color by:").grid(row=0, column=0, sticky="w", pady=5)
        self.color_by_var = tk.StringVar()
        self.color_by_dropdown = ttk.Combobox(config_frame, textvariable=self.color_by_var, width=30, state="readonly")
        self.color_by_dropdown.grid(row=0, column=1, sticky="w", pady=5)
        
        # X-axis selection dropdown
        tk.Label(config_frame, text="X-axis:").grid(row=1, column=0, sticky="w", pady=5)
        self.x_axis_var = tk.StringVar()
        self.x_axis_dropdown = ttk.Combobox(config_frame, textvariable=self.x_axis_var, width=30, state="readonly")
        self.x_axis_dropdown.grid(row=1, column=1, sticky="w", pady=5)
        
        # Y-axis selection dropdown
        tk.Label(config_frame, text="Y-axis:").grid(row=2, column=0, sticky="w", pady=5)
        self.y_axis_var = tk.StringVar()
        self.y_axis_dropdown = ttk.Combobox(config_frame, textvariable=self.y_axis_var, width=30, state="readonly")
        self.y_axis_dropdown.grid(row=2, column=1, sticky="w", pady=5)
        
        # Buttons frame
        button_frame = tk.Frame(self.content_frame, padx=20, pady=20)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Generate and view buttons
        self.generate_btn = tk.Button(button_frame, text="Generate HTML", command=self.generate_html, width=15, height=2)
        self.generate_btn.pack(side=tk.LEFT, padx=10)
        
        self.view_btn = tk.Button(button_frame, text="View in Browser", command=self.view_html, width=15, height=2, state=tk.DISABLED)
        self.view_btn.pack(side=tk.LEFT, padx=10)
        
        # Create context menu (not assigned to anything yet - will be created per column)
        self.context_menu = tk.Menu(self.root, tearoff=0)
    
    def create_tooltip(self, widget, text):
        """Create a tooltip for a widget to show full text on hover"""
        # Function to show tooltip
        def enter(event):
            x, y, _, _ = widget.bbox("insert")
            x += widget.winfo_rootx() + 25
            y += widget.winfo_rooty() + 25
            
            # Create a toplevel window
            self.tooltip = tk.Toplevel(widget)
            self.tooltip.wm_overrideredirect(True)
            self.tooltip.wm_geometry(f"+{x}+{y}")
            
            # Create tooltip content
            label = tk.Label(self.tooltip, text=text, justify='left',
                            background="#ffffe0", relief="solid", borderwidth=1,
                            font=("TkDefaultFont", "8", "normal"))
            label.pack(ipadx=3, ipady=1)
        
        # Function to hide tooltip
        def leave(event):
            if hasattr(self, 'tooltip'):
                self.tooltip.destroy()
        
        # Bind events to widget
        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)
    
    def show_add_column_dialog(self):
        """Show a dialog to add a new column using a mathematical expression"""
        if self.df is None:
            messagebox.showwarning("Warning", "Please load a CSV file first")
            return
        
        # Create a new top-level window
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Column with Expression")
        dialog.geometry("800x500")
        dialog.transient(self.root)  # Make the window transient (always on top of the main window)
        dialog.grab_set()  # Make the window modal
        
        # Create and configure the main frame
        main_frame = tk.Frame(dialog, padx=15, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Column name entry
        name_frame = tk.Frame(main_frame)
        name_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(name_frame, text="New Column Name:", width=15, anchor="w").pack(side=tk.LEFT)
        name_var = tk.StringVar()
        name_entry = tk.Entry(name_frame, textvariable=name_var, width=30)
        name_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Create a frame for the main content area with columns list, expression, and reference
        content_frame = tk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Left panel: Available Columns
        columns_frame = tk.LabelFrame(content_frame, text="Available Columns (click to copy)", padx=10, pady=10)
        columns_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Create a listbox with scrollbar for columns
        columns_listbox_frame = tk.Frame(columns_frame)
        columns_listbox_frame.pack(fill=tk.BOTH, expand=True)
        
        columns_scrollbar = ttk.Scrollbar(columns_listbox_frame)
        columns_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        columns_listbox = tk.Listbox(
            columns_listbox_frame,
            width=25,
            selectmode=tk.SINGLE,
            yscrollcommand=columns_scrollbar.set
        )
        columns_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        columns_scrollbar.config(command=columns_listbox.yview)
        
        # Populate the columns listbox
        for col in self.df_columns:
            columns_listbox.insert(tk.END, col)
        
        # Add function to copy column name to clipboard when clicked
        def copy_column_to_expression():
            selection = columns_listbox.curselection()
            if selection:
                selected_col = columns_listbox.get(selection[0])
                current_pos = expr_text.index(tk.INSERT)
                expr_text.insert(current_pos, selected_col)
                expr_text.focus_set()  # Return focus to expression text area
                
        columns_listbox.bind("<Double-1>", lambda e: copy_column_to_expression())
        
        # Add a "Copy to Expression" button under the listbox
        copy_btn = tk.Button(
            columns_frame,
            text="Copy Selected to Expression",
            command=copy_column_to_expression
        )
        copy_btn.pack(pady=5)
        
        # Middle panel: Expression entry
        expr_frame = tk.LabelFrame(content_frame, text="Enter Expression", padx=10, pady=10)
        expr_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Create a scrollable text widget for the expression
        expr_text = tk.Text(expr_frame, width=30, height=10, wrap=tk.WORD)
        expr_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        expr_scrollbar = ttk.Scrollbar(expr_frame, orient="vertical", command=expr_text.yview)
        expr_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        expr_text.configure(yscrollcommand=expr_scrollbar.set)
        
        # Add an empty line to start
        expr_text.insert("1.0", "")
        expr_text.focus_set()  # Set focus to the expression text area
        
        # Right panel: Operations and Examples
        ref_frame = tk.LabelFrame(content_frame, text="Operations & Examples", padx=10, pady=10)
        ref_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Create a scrollable text widget for the reference
        ref_text = tk.Text(ref_frame, width=30, height=10, wrap=tk.WORD)
        ref_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        ref_scrollbar = ttk.Scrollbar(ref_frame, orient="vertical", command=ref_text.yview)
        ref_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        ref_text.configure(yscrollcommand=ref_scrollbar.set)
        
        # Populate reference text with operations and examples
        reference_content = """BASIC OPERATIONS:
• Addition: col1 + col2
• Subtraction: col1 - col2
• Multiplication: col1 * col2
• Division: col1 / col2
• Power: col1 ** 2

FUNCTIONS:
• Round: np.round(col1, 2)
• Absolute: np.abs(col1)
• Log: np.log(col1)
• Exp: np.exp(col1)
• Square root: np.sqrt(col1)
• Sin/Cos: np.sin(col1)

CONDITIONALS:
• IF-ELSE: np.where(col1 > 0, col1, 0)
• Multiple: np.select(
    [col1<0, col1>100], 
    ['low', 'high'], 
    default='normal')

TEXT OPERATIONS:
• Uppercase: col1.str.upper()
• Replace: col1.str.replace('old', 'new')
• Extract: col1.str.extract('(\\\\d+)')
• Length: col1.str.len()

AGGREGATIONS:
• Combine text: col1 + '-' + col2
• Column max: np.maximum(col1, col2)
• Column min: np.minimum(col1, col2)

COMPLEX EXAMPLES:
• BMI: col_weight / (col_height**2)
• Z-score: (col1 - col1.mean()) / col1.std()
• Categorize: 
  np.where(col1 < 10, 'Low',
    np.where(col1 < 50, 'Medium', 'High'))
"""
        
        ref_text.insert("1.0", reference_content)
        ref_text.config(state=tk.DISABLED)  # Make it read-only
        
        # Buttons frame
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        # Cancel button
        cancel_btn = tk.Button(
            button_frame, 
            text="Cancel", 
            command=dialog.destroy, 
            width=10
        )
        cancel_btn.pack(side=tk.RIGHT, padx=5)
        
        # Add Column button
        add_btn = tk.Button(
            button_frame, 
            text="Add Column", 
            command=lambda: self.create_column_from_expression(
                name_var.get(), 
                expr_text.get("1.0", tk.END).strip(),
                dialog
            ), 
            width=15
        )
        add_btn.pack(side=tk.RIGHT, padx=5)
    
    def create_column_from_expression(self, column_name, expression, dialog):
        """Create a new column using the provided mathematical expression"""
        if not column_name or not column_name.strip():
            messagebox.showwarning("Warning", "Please enter a column name", parent=dialog)
            return
        
        if not expression or not expression.strip():
            messagebox.showwarning("Warning", "Please enter an expression", parent=dialog)
            return
        
        column_name = column_name.strip()
        expression = expression.strip()
        
        # Check if column name already exists
        if column_name in self.df.columns:
            overwrite = messagebox.askyesno(
                "Column Exists", 
                f"Column '{column_name}' already exists. Overwrite?",
                default=messagebox.NO,
                parent=dialog
            )
            if not overwrite:
                return
        
        try:
            # Create a local environment with column references
            local_env = {'np': np, 'pd': pd}
            
            # Add each column as a variable in the environment
            for col in self.df.columns:
                # Replace spaces and special characters in column names for variable names
                safe_col_name = re.sub(r'\W|^(?=\d)', '_', col)
                local_env[safe_col_name] = self.df[col]
                
                # Also add the original column name if it's a valid Python identifier
                if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', col):
                    local_env[col] = self.df[col]
            
            # Replace column names with safe variable names in the expression
            mod_expression = expression
            for col in sorted(self.df.columns, key=len, reverse=True):  # Sort by length for proper replacement
                if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', col):
                    safe_name = re.sub(r'\W|^(?=\d)', '_', col)
                    # Only replace full column names (not substrings)
                    mod_expression = re.sub(r'\b' + re.escape(col) + r'\b', safe_name, mod_expression)
            
            # Execute the expression and assign the result to the new column
            result = eval(mod_expression, {"__builtins__": {}}, local_env)
            
            # Check if the result has the correct length
            if isinstance(result, (pd.Series, np.ndarray)) and len(result) == len(self.df):
                self.df[column_name] = result
            else:
                # Try to broadcast scalar values
                self.df[column_name] = result
            
            # Update the column list
            if column_name not in self.df_columns:
                self.df_columns.append(column_name)
                self.update_column_grid_and_dropdowns()
            else:
                # If we're overwriting an existing column, no need to update the grid
                # But let's update the dropdowns in case column was inactive
                self.active_columns[column_name] = True
                self.update_dropdown_lists()
                
                # If the column button exists, make sure it's active (green)
                if column_name in self.column_buttons:
                    self.column_buttons[column_name].config(bg="light green", activebackground="light green")
            
            # Close the dialog without showing a success message
            dialog.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create column: {str(e)}", parent=dialog)
    
    def change_page(self, column_name, scrollable_frame, delta):
        """Change the current page in pagination"""
        new_page = self.current_page + delta
        if 0 <= new_page < self.total_pages:
            self.current_page = new_page
            self.page_var.set(f"{self.current_page + 1} / {self.total_pages}")
            self.refresh_data_view(column_name, scrollable_frame)
    
    def go_to_page(self, column_name, scrollable_frame, page_entry):
        """Jump to a specific page"""
        try:
            page = int(page_entry.get()) - 1  # Convert to 0-based index
            if 0 <= page < self.total_pages:
                self.current_page = page
                self.page_var.set(f"{self.current_page + 1} / {self.total_pages}")
                self.refresh_data_view(column_name, scrollable_frame)
            else:
                messagebox.showwarning("Invalid Page", 
                                    f"Please enter a page number between 1 and {self.total_pages}")
        except ValueError:
            messagebox.showwarning("Invalid Input", "Please enter a valid page number")
    
    def on_view_mode_changed(self, column_name, scrollable_frame):
        """Handle changes to the view mode (all values or unique values)"""
        # Reset to first page when switching modes
        self.current_page = 0
        
        # Refresh the view with the new mode
        self.refresh_data_view(column_name, scrollable_frame)
    
    def update_column_grid_and_dropdowns(self):
        """Update both the column grid and dropdown options after adding a new column"""
        # Recreate the column grid
        self.create_column_grid()
        
        # Update the dropdown options
        self.update_dropdown_lists()
    
    def on_frame_configure(self, event=None):
        """Reset the scroll region to encompass the content frame"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def on_canvas_configure(self, event=None):
        """When canvas size changes, adjust the content frame width"""
        if event:
            # Set the width of content_frame to match the canvas width
            canvas_width = event.width
            self.canvas.itemconfig(self.canvas_frame, width=canvas_width)
    
    def toggle_column(self, column, button):
        """Toggle a column's active state and update button color"""
        if self.active_columns[column]:
            # Deactivate column
            self.active_columns[column] = False
            button.config(bg="light gray", activebackground="light gray")
        else:
            # Activate column
            self.active_columns[column] = True
            button.config(bg="light green", activebackground="light green")
        
        # Update dropdowns with only active columns
        self.update_dropdown_lists()
    
    def remove_constant_columns(self):
        """Identify and disable columns that have the exact same value in all rows"""
        if self.df is None or len(self.df) <= 1:  # Need at least 2 rows to compare
            messagebox.showinfo("Info", "No data available to analyze")
            return
        
        constant_columns = []
        
        # Check each column to see if all values are the same
        for col in self.df_columns:
            # Get unique values, ignoring NaN
            unique_values = self.df[col].dropna().unique()
            
            # If there's only one unique value, it's a constant column
            if len(unique_values) == 1 or (self.df[col].isna().all()):
                constant_columns.append(col)
                # Deactivate the column
                if col in self.active_columns:
                    self.active_columns[col] = False
                    # Update button appearance
                    if col in self.column_buttons:
                        self.column_buttons[col].config(bg="light gray", activebackground="light gray")
        
        # Update dropdowns
        self.update_dropdown_lists()
        
        # Show message with results
        if constant_columns:
            messagebox.showinfo("Constant Columns Removed", 
                              f"Removed {len(constant_columns)} constant column(s):\n" + 
                              "\n".join(constant_columns[:10]) + 
                              ("\n..." if len(constant_columns) > 10 else ""))
        else:
            messagebox.showinfo("No Constant Columns", "No constant columns found in the data")
    
    def show_column_context_menu(self, event, original_column, button):
        """Show the context menu for a column button"""
        # Create a new context menu for this specific button
        context_menu = tk.Menu(self.root, tearoff=0)
        
        # Add rename option
        context_menu.add_command(
            label="Rename Column", 
            command=lambda: self.rename_column(original_column, button)
        )
        
        # Add view/edit data option
        context_menu.add_command(
            label="View/Edit Column Data", 
            command=lambda: self.show_column_data(original_column)
        )
        
        # Add separator
        context_menu.add_separator()
        
        # Add option to remove constant columns
        context_menu.add_command(
            label="Remove Constant Columns",
            command=self.remove_constant_columns
        )
        
        # Show the menu at the click position
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            # Make sure to release the grab
            context_menu.grab_release()
    
    def rename_column(self, original_column, button):
        """Open a dialog to rename a column"""
        current_name = button['text']
        new_name = simpledialog.askstring("Rename Column", 
                                        f"Rename column '{current_name}' to:",
                                        initialvalue=current_name,
                                        parent=self.root)
        
        if new_name and new_name.strip() and new_name != current_name:
            # Update the button text
            button.config(text=new_name)
            
            # Update the column mapping
            self.column_mapping[original_column] = new_name
            
            # Update the dropdowns
            self.update_dropdown_lists()
    
    def refresh_data_view(self, column_name, scrollable_frame):
        """Refresh the data view based on toggle state (all values or unique values) with pagination"""
        # Clear existing widgets from the scrollable frame
        for widget in scrollable_frame.winfo_children():
            widget.destroy()
        
        # Get column data
        column_data = self.df[column_name].copy()
        
        # Determine if we're showing all values or unique values
        show_unique = self.show_unique_only.get()
        
        # Store the entries for later reference when saving
        self.value_entries = {}
        
        if show_unique:
            # Get unique values
            unique_values = column_data.dropna().unique()
            
            # Sort unique values for consistent display
            try:
                unique_values = sorted(unique_values)
            except TypeError:
                # If values can't be sorted (mixed types), convert to strings
                unique_values = sorted(unique_values, key=str)
            
            # Paginate unique values
            self.total_pages = math.ceil(len(unique_values) / self.rows_per_page)
            
            # Update page display
            self.page_var.set(f"{self.current_page + 1} / {self.total_pages}")
            
            # Calculate start and end indices for the current page
            start_idx = self.current_page * self.rows_per_page
            end_idx = min(start_idx + self.rows_per_page, len(unique_values))
            
            # Get current page's unique values
            page_unique_values = unique_values[start_idx:end_idx]
            
            # Add column headers
            tk.Label(scrollable_frame, text="Value", font=('bold'), width=20).grid(row=0, column=0, padx=5, pady=5)
            tk.Label(scrollable_frame, text="New Value", font=('bold'), width=20).grid(row=0, column=1, padx=5, pady=5)
            tk.Label(scrollable_frame, text="Occurrences", font=('bold'), width=10).grid(row=0, column=2, padx=5, pady=5)
            
            # Add data rows with editable fields for unique values
            for i, value in enumerate(page_unique_values, 1):
                # Count occurrences of this value
                occurrences = len(self.df[self.df[column_name] == value])
                
                # Original value label (non-editable)
                original_value_str = str(value)
                tk.Label(scrollable_frame, text=original_value_str, width=20).grid(row=i, column=0, padx=5, pady=2)
                
                # New value entry
                value_var = tk.StringVar(value=original_value_str)
                entry = tk.Entry(scrollable_frame, textvariable=value_var, width=20)
                entry.grid(row=i, column=1, padx=5, pady=2)
                
                # Occurrences count
                tk.Label(scrollable_frame, text=str(occurrences), width=10).grid(row=i, column=2, padx=5, pady=2)
                
                # Store the entry variable with a special prefix to identify as unique value
                self.value_entries[f"unique:{original_value_str}"] = value_var
                
        else:
            # Show all values with pagination
            self.total_pages = math.ceil(len(column_data) / self.rows_per_page)
            
            # Update page display
            self.page_var.set(f"{self.current_page + 1} / {self.total_pages}")
            
            # Calculate start and end indices for the current page
            start_idx = self.current_page * self.rows_per_page
            end_idx = min(start_idx + self.rows_per_page, len(column_data))
            
            # Get the page data - handle both regular index and RangeIndex
            try:
                page_data = column_data.iloc[start_idx:end_idx]
                page_indices = column_data.index[start_idx:end_idx]
            except:
                # Fallback for any unexpected index issues
                page_data = column_data.iloc[start_idx:end_idx]
                page_indices = list(range(start_idx, end_idx))
            
            # Add column headers
            tk.Label(scrollable_frame, text="Index", font=('bold'), width=10).grid(row=0, column=0, padx=5, pady=5)
            tk.Label(scrollable_frame, text="Value", font=('bold'), width=30).grid(row=0, column=1, padx=5, pady=5)
            
            # Add data rows with editable fields for the current page
            for i, (idx, value) in enumerate(zip(page_indices, page_data), 1):
                # Index label
                tk.Label(scrollable_frame, text=str(idx), width=10).grid(row=i, column=0, padx=5, pady=2)
                
                # Value entry
                value_var = tk.StringVar(value=str(value))
                entry = tk.Entry(scrollable_frame, textvariable=value_var, width=30)
                entry.grid(row=i, column=1, padx=5, pady=2)
                
                # Store the entry variable with the row index
                self.value_entries[idx] = value_var
    
    def show_column_data(self, column_name):
        """Show the column data in a new window with pagination for large datasets"""
        if self.df is None or column_name not in self.df.columns:
            messagebox.showwarning("Warning", "No data available for this column")
            return
        
        # Create a new top-level window
        data_window = tk.Toplevel(self.root)
        data_window.title(f"Column Data: {column_name}")
        data_window.geometry("650x550")
        
        # Get the column data
        column_data = self.df[column_name].copy()
        
        # Reset pagination for a new view
        self.current_page = 0
        
        # Configure pagination for "all values" mode initially
        self.rows_per_page = 100
        self.total_pages = math.ceil(len(column_data) / self.rows_per_page)
        
        # Create a frame for the data display
        frame = tk.Frame(data_window, padx=15, pady=15)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Add column statistics at the top
        stats_frame = tk.LabelFrame(frame, text="Column Statistics", padx=10, pady=10)
        stats_frame.pack(fill=tk.X, pady=10)
        
        # Calculate number of unique values for display
        unique_count = len(column_data.dropna().unique())
        
        # Determine data type and show appropriate statistics
        data_type = column_data.dtype
        
        if np.issubdtype(data_type, np.number):
            # Numeric data - show statistics
            stats_text = (
                f"Type: {data_type}\n"
                f"Min: {column_data.min()}\n"
                f"Max: {column_data.max()}\n"
                f"Mean: {column_data.mean():.4f}\n"
                f"Median: {column_data.median()}\n"
                f"Standard Deviation: {column_data.std():.4f}\n"
                f"Count: {len(column_data)}\n"
                f"Unique Values: {unique_count}"
            )
        else:
            # Text or other data - show basic info
            stats_text = (
                f"Type: {data_type}\n"
                f"Count: {len(column_data)}\n"
                f"Unique Values: {unique_count}"
            )
        
        tk.Label(stats_frame, text=stats_text, justify='left').pack(anchor='w')
        
        # Create toggle frame for the view mode
        toggle_frame = tk.Frame(frame)
        toggle_frame.pack(fill=tk.X, pady=5)
        
        # Create a variable for the toggle state
        self.show_unique_only = tk.BooleanVar(value=False)
        
        # Create radio buttons for toggle
        tk.Radiobutton(
            toggle_frame, 
            text="Show All Values", 
            variable=self.show_unique_only, 
            value=False,
            command=lambda: self.on_view_mode_changed(column_name, scrollable_frame)
        ).pack(side=tk.LEFT, padx=20)
        
        tk.Radiobutton(
            toggle_frame, 
            text="Show Unique Values Only", 
            variable=self.show_unique_only, 
            value=True,
            command=lambda: self.on_view_mode_changed(column_name, scrollable_frame)
        ).pack(side=tk.LEFT, padx=20)
        
        # Create pagination controls
        page_control_frame = tk.Frame(frame)
        page_control_frame.pack(fill=tk.X, pady=5)
        
        # Page indicator
        self.page_var = tk.StringVar(value=f"1 / {self.total_pages}")
        
        # Navigation buttons and page indicator
        tk.Label(page_control_frame, text="Page:").pack(side=tk.LEFT, padx=5)
        tk.Label(page_control_frame, textvariable=self.page_var, width=10).pack(side=tk.LEFT, padx=5)
        
        # Previous page button
        prev_btn = tk.Button(
            page_control_frame, 
            text="Previous", 
            command=lambda: self.change_page(column_name, scrollable_frame, -1)
        )
        prev_btn.pack(side=tk.LEFT, padx=5)
        
        # Next page button
        next_btn = tk.Button(
            page_control_frame, 
            text="Next", 
            command=lambda: self.change_page(column_name, scrollable_frame, 1)
        )
        next_btn.pack(side=tk.LEFT, padx=5)
        
        # Jump to page entry and button
        tk.Label(page_control_frame, text="Go to:").pack(side=tk.LEFT, padx=(20, 5))
        page_entry = tk.Entry(page_control_frame, width=8)
        page_entry.pack(side=tk.LEFT, padx=5)
        
        go_btn = tk.Button(
            page_control_frame, 
            text="Go", 
            command=lambda: self.go_to_page(column_name, scrollable_frame, page_entry)
        )
        go_btn.pack(side=tk.LEFT, padx=5)
        
        # Create a data editing frame
        edit_frame = tk.LabelFrame(frame, text="View/Edit Data", padx=10, pady=10)
        edit_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Create a scrollable frame for the data
        data_canvas = tk.Canvas(edit_frame)
        scrollbar = ttk.Scrollbar(edit_frame, orient="vertical", command=data_canvas.yview)
        scrollable_frame = tk.Frame(data_canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: data_canvas.configure(scrollregion=data_canvas.bbox("all"))
        )
        
        data_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        data_canvas.configure(yscrollcommand=scrollbar.set)
        
        data_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Initialize the view with all values (will be populated by refresh_data_view)
        self.refresh_data_view(column_name, scrollable_frame)
        
        # Add buttons at the bottom
        button_frame = tk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        # Save button to apply changes
        save_btn = tk.Button(
            button_frame, 
            text="Save Changes", 
            command=lambda: self.save_column_or_unique_changes(column_name)
        )
        save_btn.pack(side=tk.LEFT, padx=10)
        
        # Cancel button to close without saving
        cancel_btn = tk.Button(button_frame, text="Cancel", command=data_window.destroy)
        cancel_btn.pack(side=tk.LEFT, padx=10)
    
    def save_column_or_unique_changes(self, column_name):
        """Save changes based on view mode (all values or unique values)"""
        if self.df is None:
            return
        
        try:
            # Get the original data type of the column
            original_dtype = self.df[column_name].dtype
            
            # Check if we're in unique values mode
            if self.show_unique_only.get():
                # Process unique value changes
                value_mapping = {}
                changes_made = 0
                
                for key, value_var in self.value_entries.items():
                    if key.startswith("unique:"):
                        original_val_str = key.split(":", 1)[1]
                        new_val_str = value_var.get()
                        
                        # Only include in mapping if the value changed
                        if original_val_str != new_val_str:
                            changes_made += 1
                            # For numeric types, convert strings back to numbers
                            if np.issubdtype(original_dtype, np.number):
                                try:
                                    # Try parsing the original value
                                    try:
                                        original_val = float(original_val_str)
                                        if original_val.is_integer():
                                            original_val = int(original_val)
                                    except:
                                        original_val = original_val_str
                                        
                                    # Try parsing the new value
                                    try:
                                        new_val = float(new_val_str)
                                        if new_val.is_integer():
                                            new_val = int(new_val)
                                    except:
                                        new_val = new_val_str
                                    
                                    value_mapping[original_val] = new_val
                                except ValueError:
                                    # If conversion fails, use string values
                                    value_mapping[original_val_str] = new_val_str
                            else:
                                # For non-numeric types, use string values
                                value_mapping[original_val_str] = new_val_str
                
                # Apply the mapping to the DataFrame column
                for old_val, new_val in value_mapping.items():
                    self.df.loc[self.df[column_name] == old_val, column_name] = new_val
                
                if changes_made > 0:
                    messagebox.showinfo("Success", f"Changes to {changes_made} unique value(s) have been applied throughout the dataset")
                else:
                    messagebox.showinfo("No Changes", "No changes were made to any values")
                
            else:
                # Process individual value changes (only for displayed rows)
                changes_made = 0
                
                for idx, value_var in self.value_entries.items():
                    # Only update if the index exists in the DataFrame
                    if isinstance(idx, (int, np.integer)) or (isinstance(idx, str) and idx.isdigit()):
                        if isinstance(idx, str) and idx.isdigit():
                            idx = int(idx)
                            
                        # Handle RangeIndex vs regular index
                        if idx in self.df.index:
                            new_value = value_var.get()
                            old_value = str(self.df.at[idx, column_name])
                            
                            # Only count as a change if value actually changed
                            if new_value != old_value:
                                changes_made += 1
                                
                                # Try to convert to the original data type
                                try:
                                    if np.issubdtype(original_dtype, np.number):
                                        # For numeric types
                                        if pd.isna(new_value) or new_value == '':
                                            self.df.at[idx, column_name] = np.nan
                                        else:
                                            self.df.at[idx, column_name] = original_dtype.type(float(new_value))
                                    else:
                                        # For string or other types
                                        self.df.at[idx, column_name] = new_value
                                except ValueError:
                                    # If conversion fails, keep as string
                                    self.df.at[idx, column_name] = new_value
                
                if changes_made > 0:
                    messagebox.showinfo("Success", f"Changes to {changes_made} value(s) have been saved")
                else:
                    messagebox.showinfo("No Changes", "No changes were made to any values")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save changes: {str(e)}")
    
    def create_column_grid(self):
        """Create grid of column toggle buttons with dynamic width based on column names"""
        # Clear any existing buttons
        for widget in self.columns_grid_frame.winfo_children():
            widget.destroy()
        
        self.column_buttons = {}
        
        if not self.df_columns:
            empty_label = tk.Label(self.columns_grid_frame, text="Load a CSV file to see columns")
            empty_label.pack(padx=10, pady=10)
            return
        
        # Reset column mapping when creating a new grid
        self.column_mapping = {}
        
        # Calculate the maximum column name length for button sizing
        max_name_length = max([len(str(col)) for col in self.df_columns])
        
        # Calculate button width based on max column name length
        # Each character is approximately 0.8 characters in button width units
        # Add padding to ensure text fits
        base_width = max(8, min(20, int(max_name_length * 0.8) + 1))
        
        # Calculate grid dimensions - adjusting columns per row based on button width
        button_width_factor = base_width / 8  # Relative to the original 8 width
        cols_per_row = max(3, int(8 / button_width_factor))  # Ensure at least 3 columns
        
        # Create buttons for each column
        for i, column in enumerate(self.df_columns):
            row_idx = i // cols_per_row
            col_idx = i % cols_per_row
            
            # Determine font size based on column name length
            col_name = str(column)
            if len(col_name) > 15:
                font_size = 7  # Smaller font for long names
            else:
                font_size = 8  # Default font size
            
            # Create button for the column with adaptive width
            button = tk.Button(
                self.columns_grid_frame, 
                text=col_name, 
                bg="light green",
                activebackground="light green",
                width=base_width,  # Dynamic width based on max column length
                pady=2,
                font=('TkDefaultFont', font_size),  # Dynamic font size
                command=lambda col=column, btn=None: self.toggle_column(col, btn)
            )
            button.grid(row=row_idx, column=col_idx, padx=2, pady=2, sticky="nsew")
            
            # Add tooltip for long column names
            if len(col_name) > base_width:
                self.create_tooltip(button, col_name)
            
            # Store reference to the button in the dictionary
            self.column_buttons[column] = button
            button.config(command=lambda col=column, btn=button: self.toggle_column(col, btn))
            
            # Add right-click event for context menu
            button.bind("<Button-3>", 
                        lambda event, col=column, btn=button: 
                        self.show_column_context_menu(event, col, btn))
            
            # Initialize as active
            self.active_columns[column] = True
            
        # Configure grid weights
        for i in range(math.ceil(len(self.df_columns) / cols_per_row)):
            self.columns_grid_frame.grid_rowconfigure(i, weight=1)
        for i in range(cols_per_row):
            self.columns_grid_frame.grid_columnconfigure(i, weight=1)
            
        # Update scroll region after creating the grid
        self.root.update_idletasks()
        self.on_frame_configure()
    
    def update_dropdown_lists(self):
        """Update dropdown lists with only active columns"""
        # Get active columns with their display names (renamed if applicable)
        active_cols = []
        for col in self.df_columns:
            if self.active_columns.get(col, True):
                display_name = self.column_mapping.get(col, col)
                active_cols.append(display_name)
        
        for dropdown in [self.color_by_dropdown, self.x_axis_dropdown, self.y_axis_dropdown]:
            current_value = dropdown.get()
            dropdown['values'] = active_cols
            
            # Try to preserve the current selection if possible
            if current_value in active_cols:
                dropdown.set(current_value)
            elif active_cols:
                dropdown.set(active_cols[0])
            else:
                dropdown.set('')
    
    def browse_output_dir(self):
        """Open directory browser to select output location"""
        dir_path = filedialog.askdirectory(
            title="Select Directory to Save HTML",
            initialdir=self.output_directory
        )
        
        if dir_path:
            self.output_directory = dir_path
            self.output_dir_var.set(dir_path)
    
    def update_dropdown_options(self, columns):
        """Update dropdown menus with columns from the loaded CSV"""
        self.df_columns = columns
        
        # Initialize all columns as active
        self.active_columns = {col: True for col in columns}
        
        # Create the column selection grid
        self.create_column_grid()
        
        # Update dropdown values
        for dropdown in [self.color_by_dropdown, self.x_axis_dropdown, self.y_axis_dropdown]:
            dropdown['values'] = columns
        
        # Set default values if columns are available
        if columns:
            # Try to find numeric columns for better defaults
            try:
                numeric_cols = self.df.select_dtypes(include=['number']).columns.tolist()
                
                if numeric_cols:
                    self.color_by_var.set(numeric_cols[-1])  # Last numeric column
                    self.x_axis_var.set(numeric_cols[0])     # First numeric column
                    
                    if len(numeric_cols) > 1:
                        self.y_axis_var.set(numeric_cols[-1])  # Last numeric column
                    else:
                        self.y_axis_var.set(columns[min(1, len(columns)-1)])
                else:
                    # If no numeric columns, use first few columns
                    self.color_by_var.set(columns[0])
                    self.x_axis_var.set(columns[0])
                    self.y_axis_var.set(columns[min(1, len(columns)-1)])
            except:
                # Fallback to first columns
                self.color_by_var.set(columns[0])
                self.x_axis_var.set(columns[0])
                self.y_axis_var.set(columns[min(1, len(columns)-1)])
        
        # Update scroll region after updating dropdowns
        self.root.update_idletasks()
        self.on_frame_configure()
    
    def load_csv(self):
        """Open file dialog to select a CSV file"""
        file_path = filedialog.askopenfilename(
            title="Select CSV File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if file_path:
            self.csv_file_path = file_path
            self.file_label.config(text=f"Selected: {os.path.basename(file_path)}")
            
            # Update default HTML filename based on CSV filename
            csv_basename = os.path.splitext(os.path.basename(file_path))[0]
            self.filename_var.set(f"{csv_basename}_hiplot.html")
            
            # Try to read the CSV to get column names
            try:
                # Show a loading message for large files
                self.file_label.config(text=f"Loading {os.path.basename(file_path)}... This may take a moment.")
                self.root.update()  # Force UI update to show loading message
                
                self.df = pd.read_csv(file_path)
                columns = self.df.columns.tolist()
                
                # Update file label with row count information
                self.file_label.config(text=f"Selected: {os.path.basename(file_path)} ({len(self.df)} rows, {len(columns)} columns)")
                
                self.update_dropdown_options(columns)
                
                # Adjust window size based on number of columns
                num_columns = len(columns)
                if num_columns > 15:  # If there are many columns, make window larger
                    new_width = min(900, 750 + (num_columns - 15) * 5)  # Less increase needed with smaller buttons
                    new_height = min(800, 650 + (num_columns // 8) * 25)  # Adjusted for more columns per row
                    self.root.geometry(f"{new_width}x{new_height}")
                
                # Enable the add column button now that we have data
                self.add_column_btn.config(state=tk.NORMAL)
            
            except Exception as e:
                self.file_label.config(text=f"Error: {os.path.basename(file_path)}")
                messagebox.showerror("Error", f"Could not read CSV file: {str(e)}")
    
    def get_full_output_path(self):
        """Get the full path for the HTML output file"""
        filename = self.filename_var.get().strip()
        
        # Make sure filename has .html extension
        if not filename.lower().endswith('.html'):
            filename += '.html'
        
        return os.path.join(self.output_directory, filename)
    
    def get_active_columns_df(self):
        """Return a DataFrame with only the active columns and renamed as needed"""
        if self.df is None:
            return None
            
        # Get active columns
        active_cols = [col for col in self.df_columns if self.active_columns.get(col, True)]
        
        if not active_cols:
            return None
            
        # Create a copy of the DataFrame with only active columns
        active_df = self.df[active_cols].copy()
        
        # Rename columns according to the mapping
        rename_dict = {col: self.column_mapping[col] 
                      for col in active_cols 
                      if col in self.column_mapping}
        
        if rename_dict:
            active_df.rename(columns=rename_dict, inplace=True)
            
        return active_df
    
    def generate_html(self):
        """Generate HiPlot HTML from the selected CSV file"""
        if not self.csv_file_path:
            messagebox.showwarning("Warning", "Please select a CSV file first")
            return
        
        # Get full output path
        output_path = self.get_full_output_path()
        
        # Make sure the output directory exists
        output_dir = os.path.dirname(output_path)
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create output directory: {str(e)}")
                return
        
        try:
            # Show a loading message for large datasets
            self.root.config(cursor="wait")  # Change cursor to hourglass
            self.generate_btn.config(state=tk.DISABLED)
            self.root.update()  # Force update to show cursor change
            
            # Get active columns DataFrame with renamed columns
            active_df = self.get_active_columns_df()
            
            if active_df is None or active_df.empty:
                messagebox.showwarning("Warning", "No active columns selected for visualization")
                return
                
            # Create a temporary CSV with only active columns and renamed columns
            temp_csv_path = os.path.join(os.path.dirname(output_path), "_temp_hiplot.csv")
            active_df.to_csv(temp_csv_path, index=False)
            
            # Load data from the temporary CSV with only active columns
            experiment = hip.Experiment.from_csv(temp_csv_path)
            
            # Configure experiment
            color_by = self.color_by_var.get()
            x_axis = self.x_axis_var.get()
            y_axis = self.y_axis_var.get()
            
            if color_by and color_by in active_df.columns:
                experiment.colorby = color_by
            
            # Configure parallel plot display with a responsive height
            experiment.display_data(hip.Displays.PARALLEL_PLOT).update({
                'height': 700,  # Reasonable default for most displays
            })
            
            # Configure XY plot display if both axes are specified and active
            if x_axis and y_axis and x_axis in active_df.columns and y_axis in active_df.columns:
                experiment.display_data(hip.Displays.XY).update({
                    'axis_x': x_axis,
                    'axis_y': y_axis,
                })
            
            # Save experiment as HTML
            experiment.to_html(output_path)
            
            # Clean up temp file
            try:
                os.remove(temp_csv_path)
            except Exception as e:
                print(f"Warning: Could not remove temp file: {e}")
            
            self.root.config(cursor="")  # Reset cursor
            self.generate_btn.config(state=tk.NORMAL)
            
            messagebox.showinfo("Success", f"HiPlot visualization saved to:\n{output_path}")
            self.view_btn.config(state=tk.NORMAL)
            
        except Exception as e:
            self.root.config(cursor="")  # Reset cursor
            self.generate_btn.config(state=tk.NORMAL)
            
            import traceback
            error_details = traceback.format_exc()
            print(f"Error generating HTML: {str(e)}\n{error_details}")
            messagebox.showerror("Error", f"Failed to generate HTML: {str(e)}")
    
    def view_html(self):
        """Open the generated HTML file in the default web browser"""
        output_path = self.get_full_output_path()
        
        if os.path.exists(output_path):
            webbrowser.open('file://' + os.path.realpath(output_path))
        else:
            messagebox.showwarning("Warning", "HTML file not found. Generate it first.")

if __name__ == "__main__":
    root = tk.Tk()
    app = HiPlotGUI(root)
    root.mainloop()