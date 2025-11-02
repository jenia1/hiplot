"""
Expression dialog module for creating new columns with mathematical expressions.
"""
import tkinter as tk
from tkinter import messagebox, ttk
import pandas as pd
import numpy as np
import re


class ExpressionDialog:
    """Dialog for creating new columns using mathematical expressions"""
    
    def __init__(self, parent, df, df_columns, on_column_created_callback):
        self.parent = parent
        self.df = df
        self.df_columns = df_columns
        self.on_column_created_callback = on_column_created_callback
        self.dialog = None
    
    def show(self):
        """Show the expression dialog"""
        if self.df is None:
            messagebox.showwarning("Warning", "Please load a CSV file first")
            return
        
        # Create a new top-level window
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Add Column with Expression")
        self.dialog.geometry("800x500")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the user interface for the dialog"""
        # Create and configure the main frame
        main_frame = tk.Frame(self.dialog, padx=15, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Column name entry
        self._create_name_entry(main_frame)
        
        # Create content frame with three panels
        content_frame = tk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Create the three panels
        self._create_columns_panel(content_frame)
        self._create_expression_panel(content_frame)
        self._create_reference_panel(content_frame)
        
        # Create buttons
        self._create_buttons(main_frame)
    
    def _create_name_entry(self, parent):
        """Create the column name entry section"""
        name_frame = tk.Frame(parent)
        name_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(name_frame, text="New Column Name:", width=15, anchor="w").pack(side=tk.LEFT)
        self.name_var = tk.StringVar()
        name_entry = tk.Entry(name_frame, textvariable=self.name_var, width=30)
        name_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
    
    def _create_columns_panel(self, parent):
        """Create the available columns panel"""
        columns_frame = tk.LabelFrame(parent, text="Available Columns (click to copy)", padx=10, pady=10)
        columns_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Create listbox with scrollbar
        columns_listbox_frame = tk.Frame(columns_frame)
        columns_listbox_frame.pack(fill=tk.BOTH, expand=True)
        
        columns_scrollbar = ttk.Scrollbar(columns_listbox_frame)
        columns_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.columns_listbox = tk.Listbox(
            columns_listbox_frame,
            width=25,
            selectmode=tk.SINGLE,
            yscrollcommand=columns_scrollbar.set
        )
        self.columns_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        columns_scrollbar.config(command=self.columns_listbox.yview)
        
        # Populate columns
        for col in self.df_columns:
            self.columns_listbox.insert(tk.END, col)
        
        # Bind double-click to copy column
        self.columns_listbox.bind("<Double-1>", lambda e: self._copy_column_to_expression())
        
        # Copy button
        copy_btn = tk.Button(
            columns_frame,
            text="Copy Selected to Expression",
            command=self._copy_column_to_expression
        )
        copy_btn.pack(pady=5)
    
    def _create_expression_panel(self, parent):
        """Create the expression entry panel"""
        expr_frame = tk.LabelFrame(parent, text="Enter Expression", padx=10, pady=10)
        expr_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Create scrollable text widget
        self.expr_text = tk.Text(expr_frame, width=30, height=10, wrap=tk.WORD)
        self.expr_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        expr_scrollbar = ttk.Scrollbar(expr_frame, orient="vertical", command=self.expr_text.yview)
        expr_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.expr_text.configure(yscrollcommand=expr_scrollbar.set)
        
        self.expr_text.focus_set()
    
    def _create_reference_panel(self, parent):
        """Create the operations and examples reference panel"""
        ref_frame = tk.LabelFrame(parent, text="Operations & Examples", padx=10, pady=10)
        ref_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Create scrollable text widget
        ref_text = tk.Text(ref_frame, width=30, height=10, wrap=tk.WORD)
        ref_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        ref_scrollbar = ttk.Scrollbar(ref_frame, orient="vertical", command=ref_text.yview)
        ref_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        ref_text.configure(yscrollcommand=ref_scrollbar.set)
        
        # Populate with reference content
        reference_content = self._get_reference_content()
        ref_text.insert("1.0", reference_content)
        ref_text.config(state=tk.DISABLED)
    
    def _create_buttons(self, parent):
        """Create the dialog buttons"""
        button_frame = tk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=10)
        
        # Cancel button
        cancel_btn = tk.Button(
            button_frame, 
            text="Cancel", 
            command=self.dialog.destroy, 
            width=10
        )
        cancel_btn.pack(side=tk.RIGHT, padx=5)
        
        # Add Column button
        add_btn = tk.Button(
            button_frame, 
            text="Add Column", 
            command=self._add_column, 
            width=15
        )
        add_btn.pack(side=tk.RIGHT, padx=5)
    
    def _copy_column_to_expression(self):
        """Copy selected column name to expression text area"""
        selection = self.columns_listbox.curselection()
        if selection:
            selected_col = self.columns_listbox.get(selection[0])
            current_pos = self.expr_text.index(tk.INSERT)
            self.expr_text.insert(current_pos, selected_col)
            self.expr_text.focus_set()
    
    def _add_column(self):
        """Process the addition of a new column"""
        column_name = self.name_var.get().strip()
        expression = self.expr_text.get("1.0", tk.END).strip()
        
        if not column_name:
            messagebox.showwarning("Warning", "Please enter a column name", parent=self.dialog)
            return
        
        if not expression:
            messagebox.showwarning("Warning", "Please enter an expression", parent=self.dialog)
            return
        
        # Check if column exists
        if column_name in self.df.columns:
            overwrite = messagebox.askyesno(
                "Column Exists", 
                f"Column '{column_name}' already exists. Overwrite?",
                default=messagebox.NO,
                parent=self.dialog
            )
            if not overwrite:
                return
        
        try:
            result = self._evaluate_expression(expression)
            
            # Assign result to DataFrame
            if isinstance(result, (pd.Series, np.ndarray)) and len(result) == len(self.df):
                self.df[column_name] = result
            else:
                self.df[column_name] = result
            
            # Notify parent of successful column creation
            self.on_column_created_callback(column_name)
            
            # Close dialog
            self.dialog.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create column: {str(e)}", parent=self.dialog)
    
    def _evaluate_expression(self, expression):
        """Safely evaluate the mathematical expression"""
        # Create local environment
        local_env = {'np': np, 'pd': pd}
        
        # Add columns to environment
        for col in self.df.columns:
            # Create safe variable names
            safe_col_name = re.sub(r'\W|^(?=\d)', '_', col)
            local_env[safe_col_name] = self.df[col]
            
            # Also add original name if valid Python identifier
            if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', col):
                local_env[col] = self.df[col]
        
        # Replace column names in expression
        mod_expression = expression
        for col in sorted(self.df.columns, key=len, reverse=True):
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', col):
                safe_name = re.sub(r'\W|^(?=\d)', '_', col)
                mod_expression = re.sub(r'\b' + re.escape(col) + r'\b', safe_name, mod_expression)
        
        # Execute expression
        return eval(mod_expression, {"__builtins__": {}}, local_env)
    
    def _get_reference_content(self):
        """Get the reference content for operations and examples"""
        return """BASIC OPERATIONS:
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

