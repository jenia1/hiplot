"""
Data viewing and editing module for column data inspection and modification.
"""
import tkinter as tk
from tkinter import messagebox, ttk
import pandas as pd
import numpy as np
import math


class DataViewer:
    """Window for viewing and editing column data with pagination"""
    
    def __init__(self, parent, df, column_name):
        self.parent = parent
        self.df = df
        self.column_name = column_name
        self.window = None
        
        # Pagination settings
        self.rows_per_page = 100
        self.current_page = 0
        self.total_pages = 1
        self.show_unique_only = tk.BooleanVar(value=False)
        self.page_var = tk.StringVar()
        self.value_entries = {}
    
    def show(self):
        """Show the data viewer window"""
        if self.df is None or self.column_name not in self.df.columns:
            messagebox.showwarning("Warning", "No data available for this column")
            return
        
        # Create window
        self.window = tk.Toplevel(self.parent)
        self.window.title(f"Column Data: {self.column_name}")
        self.window.geometry("650x550")
        
        # Reset pagination
        self.current_page = 0
        column_data = self.df[self.column_name].copy()
        self.total_pages = math.ceil(len(column_data) / self.rows_per_page)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the user interface"""
        frame = tk.Frame(self.window, padx=15, pady=15)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Statistics section
        self._create_statistics_section(frame)
        
        # View mode toggle section
        self._create_toggle_section(frame)
        
        # Pagination controls
        self._create_pagination_controls(frame)
        
        # Data editing section
        self.scrollable_frame = self._create_data_section(frame)
        
        # Buttons
        self._create_buttons(frame)
        
        # Initialize view
        self._refresh_data_view()
    
    def _create_statistics_section(self, parent):
        """Create the statistics display section"""
        stats_frame = tk.LabelFrame(parent, text="Column Statistics", padx=10, pady=10)
        stats_frame.pack(fill=tk.X, pady=10)
        
        column_data = self.df[self.column_name].copy()
        unique_count = len(column_data.dropna().unique())
        data_type = column_data.dtype
        
        if np.issubdtype(data_type, np.number):
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
            stats_text = (
                f"Type: {data_type}\n"
                f"Count: {len(column_data)}\n"
                f"Unique Values: {unique_count}"
            )
        
        tk.Label(stats_frame, text=stats_text, justify='left').pack(anchor='w')
    
    def _create_toggle_section(self, parent):
        """Create the view mode toggle section"""
        toggle_frame = tk.Frame(parent)
        toggle_frame.pack(fill=tk.X, pady=5)
        
        tk.Radiobutton(
            toggle_frame, 
            text="Show All Values", 
            variable=self.show_unique_only, 
            value=False,
            command=self._on_view_mode_changed
        ).pack(side=tk.LEFT, padx=20)
        
        tk.Radiobutton(
            toggle_frame, 
            text="Show Unique Values Only", 
            variable=self.show_unique_only, 
            value=True,
            command=self._on_view_mode_changed
        ).pack(side=tk.LEFT, padx=20)
    
    def _create_pagination_controls(self, parent):
        """Create pagination control section"""
        page_control_frame = tk.Frame(parent)
        page_control_frame.pack(fill=tk.X, pady=5)
        
        self.page_var.set(f"1 / {self.total_pages}")
        
        # Navigation elements
        tk.Label(page_control_frame, text="Page:").pack(side=tk.LEFT, padx=5)
        tk.Label(page_control_frame, textvariable=self.page_var, width=10).pack(side=tk.LEFT, padx=5)
        
        # Previous/Next buttons
        prev_btn = tk.Button(
            page_control_frame, 
            text="Previous", 
            command=lambda: self._change_page(-1)
        )
        prev_btn.pack(side=tk.LEFT, padx=5)
        
        next_btn = tk.Button(
            page_control_frame, 
            text="Next", 
            command=lambda: self._change_page(1)
        )
        next_btn.pack(side=tk.LEFT, padx=5)
        
        # Jump to page
        tk.Label(page_control_frame, text="Go to:").pack(side=tk.LEFT, padx=(20, 5))
        self.page_entry = tk.Entry(page_control_frame, width=8)
        self.page_entry.pack(side=tk.LEFT, padx=5)
        
        go_btn = tk.Button(
            page_control_frame, 
            text="Go", 
            command=self._go_to_page
        )
        go_btn.pack(side=tk.LEFT, padx=5)
    
    def _create_data_section(self, parent):
        """Create the scrollable data editing section"""
        edit_frame = tk.LabelFrame(parent, text="View/Edit Data", padx=10, pady=10)
        edit_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Create scrollable canvas
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
        
        return scrollable_frame
    
    def _create_buttons(self, parent):
        """Create action buttons"""
        button_frame = tk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=10)
        
        save_btn = tk.Button(
            button_frame, 
            text="Save Changes", 
            command=self._save_changes
        )
        save_btn.pack(side=tk.LEFT, padx=10)
        
        cancel_btn = tk.Button(
            button_frame, 
            text="Cancel", 
            command=self.window.destroy
        )
        cancel_btn.pack(side=tk.LEFT, padx=10)
    
    def _change_page(self, delta):
        """Change the current page"""
        new_page = self.current_page + delta
        if 0 <= new_page < self.total_pages:
            self.current_page = new_page
            self.page_var.set(f"{self.current_page + 1} / {self.total_pages}")
            self._refresh_data_view()
    
    def _go_to_page(self):
        """Jump to a specific page"""
        try:
            page = int(self.page_entry.get()) - 1
            if 0 <= page < self.total_pages:
                self.current_page = page
                self.page_var.set(f"{self.current_page + 1} / {self.total_pages}")
                self._refresh_data_view()
            else:
                messagebox.showwarning("Invalid Page", 
                                    f"Please enter a page number between 1 and {self.total_pages}")
        except ValueError:
            messagebox.showwarning("Invalid Input", "Please enter a valid page number")
    
    def _on_view_mode_changed(self):
        """Handle view mode changes"""
        self.current_page = 0
        self._refresh_data_view()
    
    def _refresh_data_view(self):
        """Refresh the data view based on current settings"""
        # Clear existing widgets
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        column_data = self.df[self.column_name].copy()
        self.value_entries = {}
        
        if self.show_unique_only.get():
            self._show_unique_values(column_data)
        else:
            self._show_all_values(column_data)
    
    def _show_unique_values(self, column_data):
        """Display unique values with edit capability"""
        unique_values = column_data.dropna().unique()
        
        # Sort unique values
        try:
            unique_values = sorted(unique_values)
        except TypeError:
            unique_values = sorted(unique_values, key=str)
        
        # Update pagination
        self.total_pages = math.ceil(len(unique_values) / self.rows_per_page)
        self.page_var.set(f"{self.current_page + 1} / {self.total_pages}")
        
        # Get page data
        start_idx = self.current_page * self.rows_per_page
        end_idx = min(start_idx + self.rows_per_page, len(unique_values))
        page_unique_values = unique_values[start_idx:end_idx]
        
        # Headers
        tk.Label(self.scrollable_frame, text="Value", font=('bold'), width=20).grid(row=0, column=0, padx=5, pady=5)
        tk.Label(self.scrollable_frame, text="New Value", font=('bold'), width=20).grid(row=0, column=1, padx=5, pady=5)
        tk.Label(self.scrollable_frame, text="Occurrences", font=('bold'), width=10).grid(row=0, column=2, padx=5, pady=5)
        
        # Data rows
        for i, value in enumerate(page_unique_values, 1):
            occurrences = len(self.df[self.df[self.column_name] == value])
            original_value_str = str(value)
            
            tk.Label(self.scrollable_frame, text=original_value_str, width=20).grid(row=i, column=0, padx=5, pady=2)
            
            value_var = tk.StringVar(value=original_value_str)
            entry = tk.Entry(self.scrollable_frame, textvariable=value_var, width=20)
            entry.grid(row=i, column=1, padx=5, pady=2)
            
            tk.Label(self.scrollable_frame, text=str(occurrences), width=10).grid(row=i, column=2, padx=5, pady=2)
            
            self.value_entries[f"unique:{original_value_str}"] = value_var
    
    def _show_all_values(self, column_data):
        """Display all values with edit capability"""
        self.total_pages = math.ceil(len(column_data) / self.rows_per_page)
        self.page_var.set(f"{self.current_page + 1} / {self.total_pages}")
        
        # Get page data
        start_idx = self.current_page * self.rows_per_page
        end_idx = min(start_idx + self.rows_per_page, len(column_data))
        
        try:
            page_data = column_data.iloc[start_idx:end_idx]
            page_indices = column_data.index[start_idx:end_idx]
        except:
            page_data = column_data.iloc[start_idx:end_idx]
            page_indices = list(range(start_idx, end_idx))
        
        # Headers
        tk.Label(self.scrollable_frame, text="Index", font=('bold'), width=10).grid(row=0, column=0, padx=5, pady=5)
        tk.Label(self.scrollable_frame, text="Value", font=('bold'), width=30).grid(row=0, column=1, padx=5, pady=5)
        
        # Data rows
        for i, (idx, value) in enumerate(zip(page_indices, page_data), 1):
            tk.Label(self.scrollable_frame, text=str(idx), width=10).grid(row=i, column=0, padx=5, pady=2)
            
            value_var = tk.StringVar(value=str(value))
            entry = tk.Entry(self.scrollable_frame, textvariable=value_var, width=30)
            entry.grid(row=i, column=1, padx=5, pady=2)
            
            self.value_entries[idx] = value_var
    
    def _save_changes(self):
        """Save the changes made to the data"""
        if self.df is None:
            return
        
        try:
            original_dtype = self.df[self.column_name].dtype
            
            if self.show_unique_only.get():
                self._save_unique_value_changes(original_dtype)
            else:
                self._save_individual_changes(original_dtype)
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save changes: {str(e)}")
    
    def _save_unique_value_changes(self, original_dtype):
        """Save changes when in unique values mode"""
        value_mapping = {}
        changes_made = 0
        
        for key, value_var in self.value_entries.items():
            if key.startswith("unique:"):
                original_val_str = key.split(":", 1)[1]
                new_val_str = value_var.get()
                
                if original_val_str != new_val_str:
                    changes_made += 1
                    
                    if np.issubdtype(original_dtype, np.number):
                        try:
                            # Convert back to numbers
                            try:
                                original_val = float(original_val_str)
                                if original_val.is_integer():
                                    original_val = int(original_val)
                            except:
                                original_val = original_val_str
                            
                            try:
                                new_val = float(new_val_str)
                                if new_val.is_integer():
                                    new_val = int(new_val)
                            except:
                                new_val = new_val_str
                            
                            value_mapping[original_val] = new_val
                        except ValueError:
                            value_mapping[original_val_str] = new_val_str
                    else:
                        value_mapping[original_val_str] = new_val_str
        
        # Apply mapping
        for old_val, new_val in value_mapping.items():
            self.df.loc[self.df[self.column_name] == old_val, self.column_name] = new_val
        
        if changes_made > 0:
            messagebox.showinfo("Success", f"Changes to {changes_made} unique value(s) have been applied throughout the dataset")
        else:
            messagebox.showinfo("No Changes", "No changes were made to any values")
    
    def _save_individual_changes(self, original_dtype):
        """Save changes when in all values mode"""
        changes_made = 0
        
        for idx, value_var in self.value_entries.items():
            if isinstance(idx, (int, np.integer)) or (isinstance(idx, str) and idx.isdigit()):
                if isinstance(idx, str) and idx.isdigit():
                    idx = int(idx)
                
                if idx in self.df.index:
                    new_value = value_var.get()
                    old_value = str(self.df.at[idx, self.column_name])
                    
                    if new_value != old_value:
                        changes_made += 1
                        
                        try:
                            if np.issubdtype(original_dtype, np.number):
                                if pd.isna(new_value) or new_value == '':
                                    self.df.at[idx, self.column_name] = np.nan
                                else:
                                    self.df.at[idx, self.column_name] = original_dtype.type(float(new_value))
                            else:
                                self.df.at[idx, self.column_name] = new_value
                        except ValueError:
                            self.df.at[idx, self.column_name] = new_value
        
        if changes_made > 0:
            messagebox.showinfo("Success", f"Changes to {changes_made} value(s) have been saved")
        else:
            messagebox.showinfo("No Changes", "No changes were made to any values")

