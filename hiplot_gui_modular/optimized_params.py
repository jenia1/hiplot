"""
Optimized Parameters module for organizing and exporting parameter configurations.
"""
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import pandas as pd
import os


class ConditionDefinitionDialog:
    """Dialog for defining conditions for a variable"""
    
    def __init__(self, parent, variable_name, existing_conditions=None):
        self.parent = parent
        self.variable_name = variable_name
        self.conditions = existing_conditions.copy() if existing_conditions else []
        self.window = None
        self.result = None
        
        # UI components
        self.conditions_listbox = None
        self.operator_var = None
        self.value_entry = None
    
    def show(self):
        """Show the condition definition dialog"""
        self.window = tk.Toplevel(self.parent)
        self.window.title(f"Define Conditions for '{self.variable_name}'")
        self.window.geometry("500x450")
        self.window.transient(self.parent)
        self.window.grab_set()
        
        self._setup_ui()
        
        # Wait for window to close
        self.parent.wait_window(self.window)
        return self.result
    
    def _setup_ui(self):
        """Setup the user interface"""
        main_frame = tk.Frame(self.window, padx=15, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = tk.Label(
            main_frame,
            text=f"Define Conditions for: {self.variable_name}",
            font=('TkDefaultFont', 11, 'bold')
        )
        title_label.pack(pady=(0, 10))
        
        # Existing conditions section
        conditions_frame = tk.LabelFrame(
            main_frame,
            text="Defined Conditions",
            padx=10,
            pady=10
        )
        conditions_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Listbox with scrollbar
        list_frame = tk.Frame(conditions_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.conditions_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            font=('TkDefaultFont', 10)
        )
        self.conditions_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.conditions_listbox.yview)
        
        # Populate existing conditions
        self._refresh_conditions_list()
        
        # Add condition section
        add_frame = tk.LabelFrame(
            main_frame,
            text="Add New Condition",
            padx=10,
            pady=10
        )
        add_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Operator selection
        operator_frame = tk.Frame(add_frame)
        operator_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(operator_frame, text="Operator:").pack(side=tk.LEFT, padx=5)
        
        self.operator_var = tk.StringVar(value=">")
        operators = [">", ">=", "<", "<=", "==", "!="]
        
        for op in operators:
            tk.Radiobutton(
                operator_frame,
                text=op,
                variable=self.operator_var,
                value=op
            ).pack(side=tk.LEFT, padx=5)
        
        # Value entry
        value_frame = tk.Frame(add_frame)
        value_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(value_frame, text="Value:").pack(side=tk.LEFT, padx=5)
        
        self.value_entry = tk.Entry(value_frame, width=30)
        self.value_entry.pack(side=tk.LEFT, padx=5)
        
        # Add button
        add_btn = tk.Button(
            add_frame,
            text="Add Condition",
            command=self._add_condition,
            bg="light green",
            width=15
        )
        add_btn.pack(pady=5)
        
        # Remove button
        remove_btn = tk.Button(
            add_frame,
            text="Remove Selected",
            command=self._remove_condition,
            bg="light coral",
            width=15
        )
        remove_btn.pack(pady=5)
        
        # Bottom buttons
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        save_btn = tk.Button(
            button_frame,
            text="Save",
            command=self._save_conditions,
            width=15,
            height=2,
            bg="light blue"
        )
        save_btn.pack(side=tk.LEFT, padx=10)
        
        cancel_btn = tk.Button(
            button_frame,
            text="Cancel",
            command=self._cancel,
            width=15,
            height=2
        )
        cancel_btn.pack(side=tk.LEFT, padx=10)
    
    def _refresh_conditions_list(self):
        """Refresh the conditions listbox"""
        self.conditions_listbox.delete(0, tk.END)
        for condition in self.conditions:
            display_text = f"{condition['operator']} {condition['value']}"
            self.conditions_listbox.insert(tk.END, display_text)
    
    def _add_condition(self):
        """Add a new condition"""
        operator = self.operator_var.get()
        value = self.value_entry.get().strip()
        
        if not value:
            messagebox.showwarning("Invalid Value", "Please enter a value for the condition")
            return
        
        # Try to convert to number if possible
        try:
            numeric_value = float(value)
            if numeric_value.is_integer():
                numeric_value = int(numeric_value)
            value = numeric_value
        except ValueError:
            # Keep as string
            pass
        
        # Add condition
        condition = {
            'operator': operator,
            'value': value
        }
        self.conditions.append(condition)
        
        # Refresh display
        self._refresh_conditions_list()
        
        # Clear value entry
        self.value_entry.delete(0, tk.END)
    
    def _remove_condition(self):
        """Remove selected condition"""
        selection = self.conditions_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a condition to remove")
            return
        
        # Remove in reverse order to avoid index issues
        for idx in reversed(selection):
            del self.conditions[idx]
        
        # Refresh display
        self._refresh_conditions_list()
    
    def _save_conditions(self):
        """Save conditions and close dialog"""
        self.result = self.conditions.copy() if self.conditions else None
        self.window.destroy()
    
    def _cancel(self):
        """Cancel without saving"""
        self.result = None
        self.window.destroy()


class OptimizedParamsWindow:
    """Window for managing optimized parameters with categorization and export"""
    
    def __init__(self, parent, df, df_columns):
        self.parent = parent
        self.df = df
        self.df_columns = df_columns.copy() if df_columns else []
        self.window = None
        
        # Data storage for each section
        self.all_columns = self.df_columns.copy()  # Section 1: All available columns
        self.inputs = []  # Section 2: Input parameters
        self.conditions = []  # Section 3: Conditions
        self.apply_to_all = []  # Section 4: Apply to All columns
        
        # Store condition definitions: {column_name: [list of conditions]}
        self.condition_definitions = {}
        
        # UI components
        self.all_columns_listbox = None
        self.inputs_listbox = None
        self.conditions_listbox = None
        self.apply_to_all_listbox = None
    
    def show(self):
        """Show the optimized parameters window"""
        if not self.df_columns:
            messagebox.showwarning("Warning", "Please load a CSV file first")
            return
        
        # Create window
        self.window = tk.Toplevel(self.parent)
        self.window.title("Optimized Parameters")
        self.window.geometry("900x700")
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the user interface"""
        main_frame = tk.Frame(self.window, padx=15, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title and instructions
        title_label = tk.Label(
            main_frame,
            text="Optimized Parameters Configuration",
            font=('TkDefaultFont', 12, 'bold')
        )
        title_label.pack(pady=(0, 5))
        
        instructions_label = tk.Label(
            main_frame,
            text="Right-click on items in 'All Columns' to move them to other sections",
            fg="gray"
        )
        instructions_label.pack(pady=(0, 10))
        
        # Create sections frame
        sections_frame = tk.Frame(main_frame)
        sections_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configure grid weights for equal distribution
        sections_frame.grid_columnconfigure(0, weight=1)
        sections_frame.grid_columnconfigure(1, weight=1)
        sections_frame.grid_rowconfigure(0, weight=1)
        sections_frame.grid_rowconfigure(1, weight=1)
        
        # Create the 4 sections
        self._create_all_columns_section(sections_frame, row=0, col=0)
        self._create_inputs_section(sections_frame, row=0, col=1)
        self._create_conditions_section(sections_frame, row=1, col=0)
        self._create_apply_to_all_section(sections_frame, row=1, col=1)
        
        # Buttons
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(15, 0))
        
        # Start button
        start_btn = tk.Button(
            button_frame,
            text="Start",
            command=self._start_processing,
            width=15,
            height=2,
            bg="light green",
            font=('TkDefaultFont', 10, 'bold')
        )
        start_btn.pack(side=tk.LEFT, padx=10)
        
        # Show Results button
        show_results_btn = tk.Button(
            button_frame,
            text="Show Results",
            command=self._show_results,
            width=15,
            height=2,
            bg="light yellow",
            font=('TkDefaultFont', 10, 'bold')
        )
        show_results_btn.pack(side=tk.LEFT, padx=10)
        
        # Export button
        export_btn = tk.Button(
            button_frame,
            text="Export to CSV",
            command=self._export_to_csv,
            width=15,
            height=2,
            bg="light blue"
        )
        export_btn.pack(side=tk.LEFT, padx=10)
        
        # Clear all button
        clear_btn = tk.Button(
            button_frame,
            text="Clear All Sections",
            command=self._clear_all_sections,
            width=18,
            height=2,
            bg="light coral"
        )
        clear_btn.pack(side=tk.RIGHT, padx=10)
        
        # Close button
        close_btn = tk.Button(
            button_frame,
            text="Close",
            command=self.window.destroy,
            width=12,
            height=2
        )
        close_btn.pack(side=tk.RIGHT, padx=10)
    
    def _create_all_columns_section(self, parent, row, col):
        """Create the 'All Columns' section (Section 1)"""
        frame = tk.LabelFrame(
            parent,
            text="1. All Columns (Right-click to move)",
            padx=10,
            pady=10,
            font=('TkDefaultFont', 10, 'bold')
        )
        frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
        
        # Create scrollable listbox
        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.all_columns_listbox = tk.Listbox(
            frame,
            yscrollcommand=scrollbar.set,
            selectmode=tk.EXTENDED,
            font=('TkDefaultFont', 9)
        )
        self.all_columns_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.all_columns_listbox.yview)
        
        # Populate with columns
        for col_name in self.all_columns:
            self.all_columns_listbox.insert(tk.END, col_name)
        
        # Bind right-click
        self.all_columns_listbox.bind("<Button-3>", self._show_all_columns_context_menu)
    
    def _create_inputs_section(self, parent, row, col):
        """Create the 'Inputs' section (Section 2)"""
        frame = tk.LabelFrame(
            parent,
            text="2. Inputs (Right-click to remove)",
            padx=10,
            pady=10,
            font=('TkDefaultFont', 10, 'bold')
        )
        frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
        
        # Create scrollable listbox
        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.inputs_listbox = tk.Listbox(
            frame,
            yscrollcommand=scrollbar.set,
            selectmode=tk.EXTENDED,
            font=('TkDefaultFont', 9),
            bg="light yellow"
        )
        self.inputs_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.inputs_listbox.yview)
        
        # Bind right-click
        self.inputs_listbox.bind("<Button-3>", 
                                lambda event: self._show_removal_context_menu(event, 'inputs'))
    
    def _create_conditions_section(self, parent, row, col):
        """Create the 'Conditions' section (Section 3)"""
        frame = tk.LabelFrame(
            parent,
            text="3. Conditions (Right-click to remove)",
            padx=10,
            pady=10,
            font=('TkDefaultFont', 10, 'bold')
        )
        frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
        
        # Create scrollable listbox
        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.conditions_listbox = tk.Listbox(
            frame,
            yscrollcommand=scrollbar.set,
            selectmode=tk.EXTENDED,
            font=('TkDefaultFont', 9),
            bg="light cyan"
        )
        self.conditions_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.conditions_listbox.yview)
        
        # Bind right-click
        self.conditions_listbox.bind("<Button-3>", 
                                     lambda event: self._show_removal_context_menu(event, 'conditions'))
        
        # Bind double-click to edit conditions
        self.conditions_listbox.bind("<Double-Button-1>", self._edit_condition_on_doubleclick)
    
    def _create_apply_to_all_section(self, parent, row, col):
        """Create the 'Apply to All' section (Section 4)"""
        frame = tk.LabelFrame(
            parent,
            text="4. Apply to All (Right-click to remove)",
            padx=10,
            pady=10,
            font=('TkDefaultFont', 10, 'bold')
        )
        frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
        
        # Create scrollable listbox
        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.apply_to_all_listbox = tk.Listbox(
            frame,
            yscrollcommand=scrollbar.set,
            selectmode=tk.EXTENDED,
            font=('TkDefaultFont', 9),
            bg="light green"
        )
        self.apply_to_all_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.apply_to_all_listbox.yview)
        
        # Bind right-click
        self.apply_to_all_listbox.bind("<Button-3>", 
                                       lambda event: self._show_removal_context_menu(event, 'apply_to_all'))
    
    def _show_all_columns_context_menu(self, event):
        """Show context menu for 'All Columns' section"""
        # Get selected items
        selection = self.all_columns_listbox.curselection()
        if not selection:
            return
        
        selected_items = [self.all_columns_listbox.get(idx) for idx in selection]
        
        # Create context menu
        context_menu = tk.Menu(self.window, tearoff=0)
        
        context_menu.add_command(
            label=f"Move to Inputs ({len(selected_items)} item(s))",
            command=lambda: self._move_to_section(selected_items, 'inputs')
        )
        
        context_menu.add_command(
            label=f"Move to Conditions ({len(selected_items)} item(s))",
            command=lambda: self._move_to_conditions_with_dialog(selected_items)
        )
        
        context_menu.add_command(
            label=f"Move to Apply to All ({len(selected_items)} item(s))",
            command=lambda: self._move_to_section(selected_items, 'apply_to_all')
        )
        
        # Show menu
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
    
    def _show_removal_context_menu(self, event, section_name):
        """Show context menu for removing items from a section"""
        # Get the appropriate listbox
        listbox = getattr(self, f"{section_name}_listbox")
        
        # Get selected items
        selection = listbox.curselection()
        if not selection:
            return
        
        selected_items = [listbox.get(idx) for idx in selection]
        
        # Create context menu
        context_menu = tk.Menu(self.window, tearoff=0)
        
        # Add edit option for conditions section
        if section_name == 'conditions' and len(selected_items) == 1:
            # Extract actual column name (remove condition count suffix if present)
            item_text = selected_items[0]
            column_name = self._extract_column_name(item_text)
            
            context_menu.add_command(
                label="Edit Conditions",
                command=lambda: self._edit_condition(column_name)
            )
            context_menu.add_separator()
        
        context_menu.add_command(
            label=f"Remove from {section_name.capitalize()} ({len(selected_items)} item(s))",
            command=lambda: self._remove_from_section(selected_items, section_name)
        )
        
        # Show menu
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
    
    def _move_to_conditions_with_dialog(self, items):
        """Move items to Conditions section and open condition definition dialog"""
        for item in items:
            if item not in self.conditions:
                # Open condition definition dialog
                existing_conditions = self.condition_definitions.get(item, None)
                dialog = ConditionDefinitionDialog(self.window, item, existing_conditions)
                result = dialog.show()
                
                if result is not None:  # User clicked Save
                    # Add to conditions list
                    self.conditions.append(item)
                    
                    # Store condition definitions
                    if result:  # If there are conditions defined
                        self.condition_definitions[item] = result
                    elif item in self.condition_definitions:
                        # Remove if no conditions defined
                        del self.condition_definitions[item]
                    
                    # Update display
                    self._refresh_conditions_display()
    
    def _move_to_section(self, items, target_section):
        """Move items from 'All Columns' to a target section"""
        if target_section == 'inputs':
            target_list = self.inputs
            target_listbox = self.inputs_listbox
        elif target_section == 'conditions':
            target_list = self.conditions
            target_listbox = self.conditions_listbox
        elif target_section == 'apply_to_all':
            target_list = self.apply_to_all
            target_listbox = self.apply_to_all_listbox
        else:
            return
        
        # Add items to target section (avoid duplicates)
        for item in items:
            if item not in target_list:
                target_list.append(item)
                target_listbox.insert(tk.END, item)
    
    def _remove_from_section(self, items, section_name):
        """Remove items from a section"""
        if section_name == 'inputs':
            target_list = self.inputs
            target_listbox = self.inputs_listbox
        elif section_name == 'conditions':
            target_list = self.conditions
            target_listbox = self.conditions_listbox
        elif section_name == 'apply_to_all':
            target_list = self.apply_to_all
            target_listbox = self.apply_to_all_listbox
        else:
            return
        
        # Remove items
        for item in items:
            # Extract actual column name
            column_name = self._extract_column_name(item)
            
            if column_name in target_list:
                target_list.remove(column_name)
            
            # Remove condition definitions if from conditions section
            if section_name == 'conditions' and column_name in self.condition_definitions:
                del self.condition_definitions[column_name]
        
        # Refresh listbox
        if section_name == 'conditions':
            self._refresh_conditions_display()
        else:
            target_listbox.delete(0, tk.END)
            for item in target_list:
                target_listbox.insert(tk.END, item)
    
    def _clear_all_sections(self):
        """Clear all items from inputs, conditions, and apply to all sections"""
        response = messagebox.askyesno(
            "Clear All Sections",
            "Are you sure you want to clear all items from Inputs, Conditions, and Apply to All sections?"
        )
        
        if response:
            # Clear data
            self.inputs.clear()
            self.conditions.clear()
            self.apply_to_all.clear()
            
            # Clear listboxes
            self.inputs_listbox.delete(0, tk.END)
            self.conditions_listbox.delete(0, tk.END)
            self.apply_to_all_listbox.delete(0, tk.END)
            
            # Clear condition definitions
            self.condition_definitions.clear()
            
            messagebox.showinfo("Cleared", "All sections have been cleared")
    
    def _refresh_conditions_display(self):
        """Refresh the conditions listbox with condition counts"""
        self.conditions_listbox.delete(0, tk.END)
        for item in self.conditions:
            # Check if conditions are defined
            if item in self.condition_definitions and self.condition_definitions[item]:
                num_conditions = len(self.condition_definitions[item])
                display_text = f"{item} ({num_conditions} condition(s))"
            else:
                display_text = f"{item} (no conditions)"
            
            self.conditions_listbox.insert(tk.END, display_text)
    
    def _extract_column_name(self, display_text):
        """Extract the actual column name from display text"""
        # Remove the condition count suffix if present
        if " (" in display_text:
            return display_text.split(" (")[0]
        return display_text
    
    def _edit_condition(self, column_name):
        """Edit conditions for a column"""
        existing_conditions = self.condition_definitions.get(column_name, None)
        dialog = ConditionDefinitionDialog(self.window, column_name, existing_conditions)
        result = dialog.show()
        
        if result is not None:  # User clicked Save
            if result:  # If there are conditions defined
                self.condition_definitions[column_name] = result
            elif column_name in self.condition_definitions:
                # Remove if no conditions defined
                del self.condition_definitions[column_name]
            
            # Refresh display
            self._refresh_conditions_display()
    
    def _edit_condition_on_doubleclick(self, event):
        """Handle double-click on condition item to edit"""
        selection = self.conditions_listbox.curselection()
        if not selection:
            return
        
        item_text = self.conditions_listbox.get(selection[0])
        column_name = self._extract_column_name(item_text)
        self._edit_condition(column_name)
    
    def _export_to_csv(self):
        """Export the optimized parameters configuration to CSV"""
        if not self.inputs and not self.conditions and not self.apply_to_all:
            messagebox.showwarning(
                "Nothing to Export",
                "Please move some columns to Inputs, Conditions, or Apply to All sections before exporting"
            )
            return
        
        # Ask for save location
        file_path = filedialog.asksaveasfilename(
            title="Export Optimized Parameters Configuration",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile="optimized_parameters.csv"
        )
        
        if not file_path:
            return
        
        try:
            # Create export data
            export_data = self._prepare_export_data()
            
            # Save to CSV
            export_df = pd.DataFrame(export_data)
            export_df.to_csv(file_path, index=False)
            
            messagebox.showinfo(
                "Export Successful",
                f"Optimized parameters configuration saved to:\n{file_path}"
            )
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export: {str(e)}")
    
    def _prepare_export_data(self):
        """Prepare data for export in a structured format"""
        # Determine the maximum length among all sections
        max_length = max(
            len(self.inputs),
            len(self.conditions),
            len(self.apply_to_all)
        )
        
        # Create export data with aligned columns
        export_data = {
            'Inputs': self.inputs + [''] * (max_length - len(self.inputs)),
            'Conditions': self.conditions + [''] * (max_length - len(self.conditions)),
            'Apply_to_All': self.apply_to_all + [''] * (max_length - len(self.apply_to_all))
        }
        
        return export_data
    
    def _start_processing(self):
        """Handle the Start button click"""
        # Placeholder for start processing logic
        if not self.inputs and not self.conditions and not self.apply_to_all:
            messagebox.showwarning(
                "No Configuration",
                "Please configure at least one section (Inputs, Conditions, or Apply to All) before starting"
            )
            return
        
        messagebox.showinfo(
            "Start Processing",
            f"Configuration:\n\n"
            f"Inputs: {len(self.inputs)} columns\n"
            f"Conditions: {len(self.conditions)} columns\n"
            f"Apply to All: {len(self.apply_to_all)} columns\n\n"
            f"Processing will be implemented here."
        )
    
    def _show_results(self):
        """Handle the Show Results button click"""
        # Placeholder for show results logic
        messagebox.showinfo(
            "Show Results",
            "Results display will be implemented here."
        )

