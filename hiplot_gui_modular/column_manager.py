"""
Column management module for handling column selection, display, and operations.
"""
import tkinter as tk
from tkinter import messagebox, simpledialog
import math
from utils import ToolTipHelper, get_text_width_estimate
from data_viewer import DataViewer


class ColumnManager:
    """Manages column display, selection, and operations"""
    
    def __init__(self, parent, df, df_columns):
        self.parent = parent
        self.df = df
        self.df_columns = df_columns
        self.active_columns = {}
        self.column_buttons = {}
        self.column_mapping = {}
        self.columns_grid_frame = None
        
        # Callbacks
        self.on_columns_updated_callback = None
    
    def set_columns_updated_callback(self, callback):
        """Set callback for when columns are updated"""
        self.on_columns_updated_callback = callback
    
    def create_column_grid(self, grid_frame):
        """Create grid of column toggle buttons"""
        self.columns_grid_frame = grid_frame
        
        # Clear existing widgets
        for widget in grid_frame.winfo_children():
            widget.destroy()
        
        self.column_buttons = {}
        
        if not self.df_columns:
            empty_label = tk.Label(grid_frame, text="Load a CSV file to see columns")
            empty_label.pack(padx=10, pady=10)
            return
        
        # Reset column mapping
        self.column_mapping = {}
        
        # Calculate button sizing
        max_name_length = max([len(str(col)) for col in self.df_columns])
        base_width = get_text_width_estimate(max_name_length)
        cols_per_row = 5
        
        # Adjust window size if needed
        self._adjust_window_size_if_needed(base_width)
        
        # Create buttons
        for i, column in enumerate(self.df_columns):
            self._create_column_button(column, i, cols_per_row, base_width)
        
        # Configure grid weights
        self._configure_grid_weights(cols_per_row)
        
        # Update scroll region
        self.parent.update_idletasks()
        if hasattr(self.parent, 'on_frame_configure'):
            self.parent.on_frame_configure()
    
    def _create_column_button(self, column, index, cols_per_row, base_width):
        """Create a single column button"""
        row_idx = index // cols_per_row
        col_idx = index % cols_per_row
        
        col_name = str(column)
        font_size = self._get_font_size(col_name)
        
        button = tk.Button(
            self.columns_grid_frame,
            text=col_name,
            bg="light green",
            activebackground="light green",
            width=base_width,
            padx=1,
            pady=1,
            font=('TkDefaultFont', font_size),
            command=lambda col=column, btn=None: self.toggle_column(col, btn)
        )
        
        button.grid(row=row_idx, column=col_idx, padx=1, pady=1, sticky="nsew")
        
        # Add tooltip
        ToolTipHelper.create_tooltip(button, col_name)
        
        # Store button reference and update command
        self.column_buttons[column] = button
        button.config(command=lambda col=column, btn=button: self.toggle_column(col, btn))
        
        # Add context menu
        button.bind("<Button-3>", 
                   lambda event, col=column, btn=button: 
                   self.show_column_context_menu(event, col, btn))
        
        # Initialize as active
        self.active_columns[column] = True
    
    def _get_font_size(self, col_name):
        """Determine appropriate font size based on column name length"""
        if len(col_name) > 20:
            return 6
        elif len(col_name) > 15:
            return 7
        else:
            return 8
    
    def _adjust_window_size_if_needed(self, base_width):
        """Adjust window size if buttons are very wide"""
        if base_width > 12:
            current_width = self.parent.winfo_width()
            needed_width = (base_width * 5 * 8) + 50
            if needed_width > current_width:
                new_width = min(1200, needed_width)
                current_height = self.parent.winfo_height()
                self.parent.geometry(f"{new_width}x{current_height}")
    
    def _configure_grid_weights(self, cols_per_row):
        """Configure grid weights for proper expansion"""
        for i in range(math.ceil(len(self.df_columns) / cols_per_row)):
            self.columns_grid_frame.grid_rowconfigure(i, weight=1)
        
        for i in range(cols_per_row):
            self.columns_grid_frame.grid_columnconfigure(i, weight=1)
    
    def toggle_column(self, column, button):
        """Toggle a column's active state"""
        if self.active_columns[column]:
            # Deactivate
            self.active_columns[column] = False
            button.config(bg="light gray", activebackground="light gray")
        else:
            # Activate
            self.active_columns[column] = True
            button.config(bg="light green", activebackground="light green")
        
        # Notify parent of changes
        if self.on_columns_updated_callback:
            self.on_columns_updated_callback()
    
    def show_column_context_menu(self, event, original_column, button):
        """Show context menu for column operations"""
        context_menu = tk.Menu(self.parent, tearoff=0)
        
        # Add menu items
        context_menu.add_command(
            label="Rename Column",
            command=lambda: self.rename_column(original_column, button)
        )
        
        context_menu.add_command(
            label="View/Edit Column Data",
            command=lambda: self.show_column_data(original_column)
        )
        
        context_menu.add_separator()
        
        context_menu.add_command(
            label="Remove Constant Columns",
            command=self.remove_constant_columns
        )
        
        context_menu.add_command(
            label="Deselect All Columns",
            command=self.deselect_all_columns
        )
        
        # Show menu
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
    
    def rename_column(self, original_column, button):
        """Rename a column"""
        current_name = button['text']
        new_name = simpledialog.askstring(
            "Rename Column",
            f"Rename column '{current_name}' to:",
            initialvalue=current_name,
            parent=self.parent
        )
        
        if new_name and new_name.strip() and new_name != current_name:
            button.config(text=new_name)
            self.column_mapping[original_column] = new_name
            
            if self.on_columns_updated_callback:
                self.on_columns_updated_callback()
    
    def show_column_data(self, column_name):
        """Show column data in viewer window"""
        viewer = DataViewer(self.parent, self.df, column_name)
        viewer.show()
    
    def remove_constant_columns(self):
        """Remove columns that have constant values"""
        if self.df is None or len(self.df) <= 1:
            messagebox.showinfo("Info", "No data available to analyze")
            return
        
        constant_columns = []
        
        for col in self.df_columns:
            unique_values = self.df[col].dropna().unique()
            
            if len(unique_values) == 1 or self.df[col].isna().all():
                constant_columns.append(col)
                if col in self.active_columns:
                    self.active_columns[col] = False
                    if col in self.column_buttons:
                        self.column_buttons[col].config(bg="light gray", activebackground="light gray")
        
        if self.on_columns_updated_callback:
            self.on_columns_updated_callback()
        
        # Show results
        if constant_columns:
            messagebox.showinfo(
                "Constant Columns Removed",
                f"Removed {len(constant_columns)} constant column(s):\n" +
                "\n".join(constant_columns[:10]) +
                ("\n..." if len(constant_columns) > 10 else "")
            )
        else:
            messagebox.showinfo("No Constant Columns", "No constant columns found in the data")
    
    def deselect_all_columns(self):
        """Deselect all columns"""
        for column in self.df_columns:
            self.active_columns[column] = False
            if column in self.column_buttons:
                self.column_buttons[column].config(bg="light gray", activebackground="light gray")
        
        if self.on_columns_updated_callback:
            self.on_columns_updated_callback()
    
    def get_active_columns_with_display_names(self):
        """Get active columns with their display names"""
        active_cols = []
        for col in self.df_columns:
            if self.active_columns.get(col, True):
                display_name = self.column_mapping.get(col, col)
                active_cols.append(display_name)
        return active_cols
    
    def get_active_columns_df(self):
        """Get DataFrame with only active columns and renamed as needed"""
        if self.df is None:
            return None
        
        active_cols = [col for col in self.df_columns if self.active_columns.get(col, True)]
        
        if not active_cols:
            return None
        
        # Create copy with active columns
        active_df = self.df[active_cols].copy()
        
        # Apply renames
        rename_dict = {col: self.column_mapping[col] 
                      for col in active_cols 
                      if col in self.column_mapping}
        
        if rename_dict:
            active_df.rename(columns=rename_dict, inplace=True)
        
        return active_df
    
    def update_columns(self, df, df_columns):
        """Update the columns and DataFrame reference"""
        self.df = df
        self.df_columns = df_columns
        self.active_columns = {col: True for col in df_columns}
    
    def handle_new_column_added(self, column_name):
        """Handle addition of a new column"""
        if column_name not in self.df_columns:
            self.df_columns.append(column_name)
            self.create_column_grid(self.columns_grid_frame)
        else:
            # Existing column was overwritten, ensure it's active
            self.active_columns[column_name] = True
            if column_name in self.column_buttons:
                self.column_buttons[column_name].config(bg="light green", activebackground="light green")
        
        if self.on_columns_updated_callback:
            self.on_columns_updated_callback()

