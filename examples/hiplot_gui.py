import hiplot as hip
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
import os
import webbrowser

class HiPlotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("HiPlot Visualization Tool")
        self.root.geometry("650x500")
        self.csv_file_path = None
        self.output_directory = os.getcwd()  # Default to current directory
        self.html_filename = "hiplot_visualization.html"
        self.df_columns = []
        
        # Create GUI elements
        self.setup_ui()
    
    def setup_ui(self):
        # Frame for file selection
        file_frame = tk.LabelFrame(self.root, text="Input File", padx=15, pady=15)
        file_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Load CSV button
        self.load_btn = tk.Button(file_frame, text="Load CSV File", command=self.load_csv, width=20, height=2)
        self.load_btn.pack(pady=5)
        
        # Label to show selected file
        self.file_label = tk.Label(file_frame, text="No file selected", wraplength=550)
        self.file_label.pack(pady=5)
        
        # Frame for output settings
        output_frame = tk.LabelFrame(self.root, text="Output Settings", padx=15, pady=15)
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
        config_frame = tk.LabelFrame(self.root, text="Visualization Options", padx=15, pady=15)
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
        button_frame = tk.Frame(self.root, padx=20, pady=20)
        button_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        # Generate and view buttons
        self.generate_btn = tk.Button(button_frame, text="Generate HTML", command=self.generate_html, width=15, height=2)
        self.generate_btn.pack(side=tk.LEFT, padx=10)
        
        self.view_btn = tk.Button(button_frame, text="View in Browser", command=self.view_html, width=15, height=2, state=tk.DISABLED)
        self.view_btn.pack(side=tk.LEFT, padx=10)
    
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
                self.df = pd.read_csv(file_path)
                columns = self.df.columns.tolist()
                self.update_dropdown_options(columns)
            
            except Exception as e:
                messagebox.showerror("Error", f"Could not read CSV file: {str(e)}")
    
    def get_full_output_path(self):
        """Get the full path for the HTML output file"""
        filename = self.filename_var.get().strip()
        
        # Make sure filename has .html extension
        if not filename.lower().endswith('.html'):
            filename += '.html'
        
        return os.path.join(self.output_directory, filename)
    
    def generate_html(self):
        """Generate HiPlot HTML from the selected CSV file"""
        if not self.csv_file_path:
            messagebox.showwarning("Warning", "Please select a CSV file first")
            return
        
        # Get full output path
        output_path = self.get_full_output_path()
        
        try:
            # Load data from CSV
            experiment = hip.Experiment.from_csv(self.csv_file_path)
            
            # Configure experiment
            color_by = self.color_by_var.get()
            x_axis = self.x_axis_var.get()
            y_axis = self.y_axis_var.get()
            
            if color_by:
                experiment.colorby = color_by
            
            # Configure parallel plot display with a responsive height
            experiment.display_data(hip.Displays.PARALLEL_PLOT).update({
                'height': 700,  # Reasonable default for most displays
            })
            
            # Configure XY plot display if both axes are specified
            if x_axis and y_axis:
                experiment.display_data(hip.Displays.XY).update({
                    'axis_x': x_axis,
                    'axis_y': y_axis,
                })
            
            # Save experiment as HTML
            experiment.to_html(output_path)
            
            messagebox.showinfo("Success", f"HiPlot visualization saved to:\n{output_path}")
            self.view_btn.config(state=tk.NORMAL)
            
        except Exception as e:
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
