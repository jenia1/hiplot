"""
Optimized Parameters module for organizing and exporting parameter configurations.
"""
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import pandas as pd
import numpy as np
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
        
        # Store results from processing
        self.results_df = None
        self.filtered_df = None
        self.analysis_summary = None
        
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
                    # Only add to conditions list if there are actual conditions defined
                    if result and len(result) > 0:  # If there are conditions defined
                        self.conditions.append(item)
                        self.condition_definitions[item] = result
                    else:
                        # Don't add to conditions if no conditions defined
                        if item in self.condition_definitions:
                            del self.condition_definitions[item]
                        messagebox.showinfo(
                            "No Conditions Defined",
                            f"'{item}' was not added to Conditions section because no conditions were defined.\n\n"
                            "Please add at least one condition to include this column."
                        )
                    
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
            if result and len(result) > 0:  # If there are conditions defined
                self.condition_definitions[column_name] = result
            else:
                # Remove from conditions section if no conditions defined
                if column_name in self.condition_definitions:
                    del self.condition_definitions[column_name]
                if column_name in self.conditions:
                    self.conditions.remove(column_name)
                messagebox.showinfo(
                    "Removed from Conditions",
                    f"'{column_name}' was removed from Conditions section because all conditions were cleared.\n\n"
                    "Add it back with at least one condition to include it."
                )
            
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
        """Handle the Start button click - find optimized parameters"""
        # Validate configuration
        if not self.inputs:
            messagebox.showwarning(
                "Missing Configuration",
                "Please add at least one column to the 'Inputs' section"
            )
            return
        
        if not self.apply_to_all:
            messagebox.showwarning(
                "Missing Configuration",
                "Please add at least one column to the 'Apply to All' section"
            )
            return
        
        # Validate that all conditions have defined filters
        conditions_without_definitions = []
        for col in self.conditions:
            if col not in self.condition_definitions or not self.condition_definitions[col]:
                conditions_without_definitions.append(col)
        
        if conditions_without_definitions:
            messagebox.showerror(
                "Invalid Conditions",
                f"The following columns in 'Conditions' section have no conditions defined:\n\n" +
                "\n".join(conditions_without_definitions) +
                "\n\nPlease either:\n" +
                "1. Define conditions for these columns, or\n" +
                "2. Remove them from the Conditions section"
            )
            return
        
        # Validate that all columns exist in the dataframe
        all_required_columns = set(self.inputs + self.conditions + self.apply_to_all)
        missing_columns = [col for col in all_required_columns if col not in self.df.columns]
        
        if missing_columns:
            messagebox.showerror(
                "Missing Columns",
                f"The following columns are not found in the loaded data:\n\n" +
                "\n".join(missing_columns) +
                "\n\nPlease check your column selections."
            )
            return
        
        try:
            # Show processing message
            progress_window = self._show_progress_window("Processing data...")
            self.window.update()
            
            # Step 1: Filter data by conditions
            self._update_progress(progress_window, "Step 1/3: Filtering data by conditions...")
            filtered_df = self._apply_conditions_filter()
            
            if filtered_df.empty:
                progress_window.destroy()
                messagebox.showwarning(
                    "No Data",
                    "No data remains after applying conditions. Please adjust your conditions."
                )
                return
            
            # Step 2: Find optimized parameters
            self._update_progress(progress_window, "Step 2/3: Analyzing parameter combinations...")
            results = self._find_optimized_parameters(filtered_df)
            
            # Step 3: Store results
            self._update_progress(progress_window, "Step 3/3: Preparing results...")
            self.filtered_df = filtered_df
            self.results_df = results['results_df']
            self.analysis_summary = results['summary']
            
            progress_window.destroy()
            
            # Show completion message with detailed info
            conditions_summary = ""
            if self.conditions:
                conditions_summary = "\nConditions Applied:\n"
                for col in self.conditions:
                    cond_list = self.condition_definitions.get(col, [])
                    for cond in cond_list:
                        conditions_summary += f"  • {col} {cond['operator']} {cond['value']}\n"
            
            messagebox.showinfo(
                "Processing Complete",
                f"Analysis completed successfully!\n\n"
                f"Original data: {len(self.df)} rows\n"
                f"Filtered data: {len(filtered_df)} rows\n"
                f"{conditions_summary}\n"
                f"Unique input combinations: {results['summary']['total_input_combinations']}\n"
                f"Optimized combinations: {results['summary']['optimized_combinations']}\n"
                f"Apply to All groups: {results['summary']['total_groups']}\n\n"
                f"Click 'Show Results' to view details."
            )
            
        except Exception as e:
            if 'progress_window' in locals():
                progress_window.destroy()
            
            import traceback
            error_details = traceback.format_exc()
            print(f"Error during processing: {str(e)}\n{error_details}")
            messagebox.showerror(
                "Processing Error",
                f"An error occurred during processing:\n\n{str(e)}"
            )
    
    def _show_progress_window(self, message):
        """Show a progress window"""
        progress = tk.Toplevel(self.window)
        progress.title("Processing")
        progress.geometry("400x100")
        progress.transient(self.window)
        
        label = tk.Label(progress, text=message, padx=20, pady=20)
        label.pack()
        
        progress.progress_label = label
        return progress
    
    def _update_progress(self, progress_window, message):
        """Update progress window message"""
        if progress_window and hasattr(progress_window, 'progress_label'):
            progress_window.progress_label.config(text=message)
            progress_window.update()
    
    def _apply_conditions_filter(self):
        """Apply all condition filters to the dataframe"""
        filtered_df = self.df.copy()
        
        # Apply each condition
        for column_name in self.conditions:
            if column_name not in filtered_df.columns:
                raise ValueError(f"Condition column '{column_name}' not found in data")
            
            conditions_list = self.condition_definitions.get(column_name, [])
            
            # Skip if no conditions defined (safety check - shouldn't happen with new validation)
            if not conditions_list:
                print(f"Warning: Column '{column_name}' in Conditions section has no defined conditions. Skipping.")
                continue
            
            for condition in conditions_list:
                operator = condition['operator']
                value = condition['value']
                
                # Apply the condition filter
                if operator == '>':
                    filtered_df = filtered_df[filtered_df[column_name] > value]
                elif operator == '>=':
                    filtered_df = filtered_df[filtered_df[column_name] >= value]
                elif operator == '<':
                    filtered_df = filtered_df[filtered_df[column_name] < value]
                elif operator == '<=':
                    filtered_df = filtered_df[filtered_df[column_name] <= value]
                elif operator == '==':
                    filtered_df = filtered_df[filtered_df[column_name] == value]
                elif operator == '!=':
                    filtered_df = filtered_df[filtered_df[column_name] != value]
        
        return filtered_df
    
    def _find_optimized_parameters(self, filtered_df):
        """Find input combinations that exist across all 'Apply to All' groups"""
        # Validate columns exist
        for col in self.inputs:
            if col not in filtered_df.columns:
                raise ValueError(f"Input column '{col}' not found in data")
        
        for col in self.apply_to_all:
            if col not in filtered_df.columns:
                raise ValueError(f"Apply to All column '{col}' not found in data")
        
        # IMPORTANT: Get ALL unique groups from ORIGINAL dataframe (before filtering)
        # This ensures we check against all possible groups, not just those that remain after filtering
        if len(self.apply_to_all) == 1:
            all_groups = self.df[self.apply_to_all[0]].unique()  # Use self.df, not filtered_df
            group_col_name = self.apply_to_all[0]
        else:
            # Create combined group column for multiple "Apply to All" columns
            group_col_name = '_'.join(self.apply_to_all)
            self.df[group_col_name] = self.df[self.apply_to_all].apply(
                lambda row: '_'.join(map(str, row)), axis=1
            )
            filtered_df[group_col_name] = filtered_df[self.apply_to_all].apply(
                lambda row: '_'.join(map(str, row)), axis=1
            )
            all_groups = self.df[group_col_name].unique()
        
        total_groups = len(all_groups)  # Total groups from original data, not filtered
        
        # Get all unique input combinations across all data
        if len(self.inputs) == 1:
            all_input_combos = set(filtered_df[self.inputs[0]].unique())
            input_combo_col = self.inputs[0]
        else:
            # Create combined input column
            input_combo_col = '_'.join(self.inputs)
            filtered_df[input_combo_col] = filtered_df[self.inputs].apply(
                lambda row: tuple(row), axis=1
            )
            all_input_combos = set(filtered_df[input_combo_col].unique())
        
        # For each group (from ALL groups, not just filtered), find which input combinations exist
        group_input_map = {}
        for group in all_groups:  # Use all_groups from original data
            group_data = filtered_df[filtered_df[group_col_name] == group]
            if len(self.inputs) == 1:
                # If group has no data after filtering, it has no combinations
                group_inputs = set(group_data[input_combo_col].unique()) if not group_data.empty else set()
            else:
                group_inputs = set(group_data[input_combo_col].unique()) if not group_data.empty else set()
            group_input_map[group] = group_inputs
        
        # Find input combinations that appear in ALL groups (optimized parameters)
        optimized_combos = all_input_combos.copy()
        for group_inputs in group_input_map.values():
            optimized_combos = optimized_combos.intersection(group_inputs)
        
        # Create results dataframe
        results_data = []
        
        for combo in all_input_combos:
            # Count in how many groups this combination appears
            appears_in_groups = sum(1 for group_inputs in group_input_map.values() 
                                   if combo in group_inputs)
            
            is_optimized = combo in optimized_combos
            
            # Determine which groups have/miss this combination
            present_in = [str(group) for group, group_inputs in group_input_map.items() 
                         if combo in group_inputs]
            missing_in = [str(group) for group, group_inputs in group_input_map.items() 
                         if combo not in group_inputs]
            
            # Extract individual input values
            if len(self.inputs) == 1:
                input_values = {self.inputs[0]: combo}
            else:
                input_values = {self.inputs[i]: combo[i] for i in range(len(self.inputs))}
            
            row = {
                **input_values,
                'Appears_in_Groups': appears_in_groups,
                'Total_Groups': total_groups,
                'Is_Optimized': 'Yes' if is_optimized else 'No',
                'Coverage_Percent': (appears_in_groups / total_groups * 100),
                'Present_in': ', '.join(present_in) if present_in else 'None',
                'Missing_in': ', '.join(missing_in) if missing_in else 'None'
            }
            results_data.append(row)
        
        # Create DataFrame and sort by coverage
        results_df = pd.DataFrame(results_data)
        results_df = results_df.sort_values('Coverage_Percent', ascending=False)
        
        # Create summary with group details (for ALL groups, including those with 0 rows after filtering)
        group_details = {}
        for group in all_groups:  # Use all_groups from original data
            group_data = filtered_df[filtered_df[group_col_name] == group]
            group_details[str(group)] = {
                'rows': len(group_data),
                'unique_combinations': len(group_input_map[group])
            }
        
        summary = {
            'total_input_combinations': len(all_input_combos),
            'optimized_combinations': len(optimized_combos),
            'total_groups': total_groups,
            'input_columns': self.inputs.copy(),
            'apply_to_all_columns': self.apply_to_all.copy(),
            'condition_columns': self.conditions.copy(),
            'filtered_rows': len(filtered_df),
            'group_details': group_details
        }
        
        return {
            'results_df': results_df,
            'summary': summary
        }
    
    def _show_results(self):
        """Handle the Show Results button click"""
        if self.results_df is None or self.analysis_summary is None:
            messagebox.showwarning(
                "No Results",
                "Please click 'Start' to process the data first."
            )
            return
        
        # Create results window
        results_window = tk.Toplevel(self.window)
        results_window.title("Optimized Parameters Results")
        results_window.geometry("1000x700")
        
        # Main frame
        main_frame = tk.Frame(results_window, padx=15, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Summary section
        summary_frame = tk.LabelFrame(main_frame, text="Analysis Summary", padx=10, pady=10)
        summary_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Build conditions summary
        conditions_text = "None"
        if self.analysis_summary['condition_columns']:
            conditions_text = ""
            for col in self.analysis_summary['condition_columns']:
                cond_list = self.condition_definitions.get(col, [])
                for cond in cond_list:
                    conditions_text += f"{col} {cond['operator']} {cond['value']}; "
            conditions_text = conditions_text.rstrip("; ")
        
        # Build group details
        group_details_text = "\n\nGroup Details (after filtering):\n"
        for group, details in self.analysis_summary.get('group_details', {}).items():
            group_details_text += f"  • {group}: {details['rows']} rows, {details['unique_combinations']} unique input combinations\n"
        
        summary_text = (
            f"Input Parameters: {', '.join(self.analysis_summary['input_columns'])}\n"
            f"Apply to All: {', '.join(self.analysis_summary['apply_to_all_columns'])}\n"
            f"Conditions: {conditions_text}\n"
            f"Filtered Rows: {self.analysis_summary['filtered_rows']}\n"
            f"Total Groups: {self.analysis_summary['total_groups']}\n"
            f"Total Input Combinations: {self.analysis_summary['total_input_combinations']}\n"
            f"Optimized Combinations (100% coverage): {self.analysis_summary['optimized_combinations']}"
            f"{group_details_text}"
        )
        
        summary_label = tk.Label(summary_frame, text=summary_text, justify='left', font=('TkDefaultFont', 9))
        summary_label.pack(anchor='w')
        
        # Results table section
        table_frame = tk.LabelFrame(main_frame, text="Results Table", padx=10, pady=10)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Create Treeview with scrollbars
        tree_container = tk.Frame(table_frame)
        tree_container.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_container, orient="vertical")
        hsb = ttk.Scrollbar(tree_container, orient="horizontal")
        
        # Create Treeview
        columns = list(self.results_df.columns)
        tree = ttk.Treeview(
            tree_container,
            columns=columns,
            show='tree headings',
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set
        )
        
        vsb.config(command=tree.yview)
        hsb.config(command=tree.xview)
        
        # Pack scrollbars and treeview
        vsb.pack(side='right', fill='y')
        hsb.pack(side='bottom', fill='x')
        tree.pack(side='left', fill='both', expand=True)
        
        # Configure columns
        tree.column('#0', width=50, minwidth=50)
        tree.heading('#0', text='#')
        
        for col in columns:
            tree.column(col, width=120, minwidth=80)
            tree.heading(col, text=col)
        
        # Add data to treeview
        for idx, row in self.results_df.iterrows():
            values = [row[col] for col in columns]
            # Format numeric values
            formatted_values = []
            for val in values:
                if isinstance(val, float):
                    formatted_values.append(f"{val:.2f}")
                else:
                    formatted_values.append(str(val))
            
            # Color code based on optimization status
            tag = 'optimized' if row['Is_Optimized'] == 'Yes' else 'not_optimized'
            tree.insert('', 'end', text=str(idx + 1), values=formatted_values, tags=(tag,))
        
        # Configure tags for color coding
        tree.tag_configure('optimized', background='light green')
        tree.tag_configure('not_optimized', background='light yellow')
        
        # Buttons frame
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        # Export results button
        export_btn = tk.Button(
            button_frame,
            text="Export Results to CSV",
            command=lambda: self._export_results_to_csv(),
            width=20,
            height=2,
            bg="light blue"
        )
        export_btn.pack(side=tk.LEFT, padx=10)
        
        # Filter optimized only
        filter_btn = tk.Button(
            button_frame,
            text="Show Optimized Only",
            command=lambda: self._show_optimized_only(tree),
            width=20,
            height=2,
            bg="light green"
        )
        filter_btn.pack(side=tk.LEFT, padx=10)
        
        # Show all
        show_all_btn = tk.Button(
            button_frame,
            text="Show All",
            command=lambda: self._populate_results_tree(tree),
            width=15,
            height=2
        )
        show_all_btn.pack(side=tk.LEFT, padx=10)
        
        # Close button
        close_btn = tk.Button(
            button_frame,
            text="Close",
            command=results_window.destroy,
            width=15,
            height=2
        )
        close_btn.pack(side=tk.RIGHT, padx=10)
    
    def _populate_results_tree(self, tree, filter_optimized=False):
        """Populate results tree with data"""
        # Clear existing items
        for item in tree.get_children():
            tree.delete(item)
        
        # Filter if needed
        if filter_optimized:
            df_to_show = self.results_df[self.results_df['Is_Optimized'] == 'Yes']
        else:
            df_to_show = self.results_df
        
        columns = list(df_to_show.columns)
        
        # Add data
        for idx, row in df_to_show.iterrows():
            values = [row[col] for col in columns]
            formatted_values = []
            for val in values:
                if isinstance(val, float):
                    formatted_values.append(f"{val:.2f}")
                else:
                    formatted_values.append(str(val))
            
            tag = 'optimized' if row['Is_Optimized'] == 'Yes' else 'not_optimized'
            tree.insert('', 'end', text=str(idx + 1), values=formatted_values, tags=(tag,))
    
    def _show_optimized_only(self, tree):
        """Show only optimized parameters in the tree"""
        self._populate_results_tree(tree, filter_optimized=True)
    
    def _export_results_to_csv(self):
        """Export the results dataframe to CSV"""
        if self.results_df is None:
            messagebox.showwarning("No Results", "No results to export")
            return
        
        # Ask for save location
        file_path = filedialog.asksaveasfilename(
            title="Export Results",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile="optimized_parameters_results.csv"
        )
        
        if not file_path:
            return
        
        try:
            self.results_df.to_csv(file_path, index=False)
            messagebox.showinfo(
                "Export Successful",
                f"Results exported to:\n{file_path}"
            )
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export: {str(e)}")

