import hiplot as hip
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
import os
import webbrowser

class HiPlotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("HiPlot Visualization Tool")
        self.root.geometry("600x400")
        self.csv_file_path = None
        self.html_output_path = "hiplot_visualization.html"
        
        # Create GUI elements
        self.setup_ui()
    
    def setup_ui(self):
        # Frame for file selection
        file_frame = tk.Frame(self.root, padx=20, pady=20)
        file_frame.pack(fill=tk.X)
        
        # Load CSV button
        self.load_btn = tk.Button(file_frame, text="Load CSV File", command=self.load_csv, width=20, height=2)
        self.load_btn.pack(pady=10)
        
        # Label to show selected file
        self.file_label = tk.Label(file_frame, text="No file selected", wraplength=550)
        self.file_label.pack(pady=10)
        
        # Configuration frame
        config_frame = tk.Frame(self.root, padx=20, pady=10)
        config_frame.pack(fill=tk.X)
        
        # Color by selection
        tk.Label(config_frame, text="Color by:").grid(row=0, column=0, sticky="w", pady=5)
        self.color_by = tk.Entry(config_frame, width=20)
        self.color_by.grid(row=0, column=1, sticky="w", pady=5)
        
        # X-axis selection
        tk.Label(config_frame, text="X-axis:").grid(row=1, column=0, sticky="w", pady=5)
        self.x_axis = tk.Entry(config_frame, width=20)
        self.x_axis.grid(row=1, column=1, sticky="w", pady=5)
        
        # Y-axis selection
        tk.Label(config_frame, text="Y-axis:").grid(row=2, column=0, sticky="w", pady=5)
        self.y_axis = tk.Entry(config_frame, width=20)
        self.y_axis.grid(row=2, column=1, sticky="w", pady=5)
        
        # Height selection
        tk.Label(config_frame, text="Plot Height:").grid(row=3, column=0, sticky="w", pady=5)
        self.plot_height = tk.Entry(config_frame, width=20)
        self.plot_height.insert(0, "500")  # Default value
        self.plot_height.grid(row=3, column=1, sticky="w", pady=5)
        
        # Buttons frame
        button_frame = tk.Frame(self.root, padx=20, pady=20)
        button_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        # Generate and view buttons
        self.generate_btn = tk.Button(button_frame, text="Generate HTML", command=self.generate_html, width=15, height=2)
        self.generate_btn.pack(side=tk.LEFT, padx=10)
        
        self.view_btn = tk.Button(button_frame, text="View in Browser", command=self.view_html, width=15, height=2, state=tk.DISABLED)
        self.view_btn.pack(side=tk.LEFT, padx=10)
    
    def load_csv(self):
        """Open file dialog to select a CSV file"""
        file_path = filedialog.askopenfilename(
            title="Select CSV File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if file_path:
            self.csv_file_path = file_path
            self.file_label.config(text=f"Selected: {os.path.basename(file_path)}")
            
            # Try to read the CSV to get column names
            try:
                df = pd.read_csv(file_path)
                columns = df.columns.tolist()
                
                # Suggest columns for visualization
                numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                
                # Set default values if columns are available
                if len(numeric_cols) > 0:
                    self.color_by.delete(0, tk.END)
                    self.color_by.insert(0, numeric_cols[-1])  # Last numeric column
                    
                    self.x_axis.delete(0, tk.END)
                    self.x_axis.insert(0, numeric_cols[0])  # First numeric column
                    
                    if len(numeric_cols) > 1:
                        self.y_axis.delete(0, tk.END)
                        self.y_axis.insert(0, numeric_cols[-1])  # Last numeric column
            
            except Exception as e:
                messagebox.showerror("Error", f"Could not read CSV file: {str(e)}")
    
    def generate_html(self):
        """Generate HiPlot HTML from the selected CSV file"""
        if not self.csv_file_path:
            messagebox.showwarning("Warning", "Please select a CSV file first")
            return
        
        try:
            # Load data from CSV
            experiment = hip.Experiment.from_csv(self.csv_file_path)
            
            # Configure experiment
            color_by = self.color_by.get()
            x_axis = self.x_axis.get()
            y_axis = self.y_axis.get()
            
            try:
                plot_height = int(self.plot_height.get())
            except ValueError:
                plot_height = 500
            
            if color_by:
                experiment.colorby = color_by
            
            # Configure parallel plot display
            experiment.display_data(hip.Displays.PARALLEL_PLOT).update({
                'height': plot_height,
            })
            
            # Configure XY plot display if both axes are specified
            if x_axis and y_axis:
                experiment.display_data(hip.Displays.XY).update({
                    'axis_x': x_axis,
                    'axis_y': y_axis,
                })
            
            # Save experiment as HTML
            experiment.to_html(self.html_output_path)
            
            messagebox.showinfo("Success", f"HiPlot visualization saved to: {self.html_output_path}")
            self.view_btn.config(state=tk.NORMAL)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate HTML: {str(e)}")
    
    def view_html(self):
        """Open the generated HTML file in the default web browser"""
        if os.path.exists(self.html_output_path):
            webbrowser.open('file://' + os.path.realpath(self.html_output_path))
        else:
            messagebox.showwarning("Warning", "HTML file not found. Generate it first.")

if __name__ == "__main__":
    root = tk.Tk()
    app = HiPlotGUI(root)
    root.mainloop()
