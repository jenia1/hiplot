"""
Main GUI class for the HiPlot application using modular components.
"""
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
import os
import sys
import subprocess
import webbrowser
import pandas as pd
import hiplot as hip

from utils import resource_path, configure_window_size
from column_manager import ColumnManager
from expression_dialog import ExpressionDialog


class HiPlotGUI:
    """Main GUI application for HiPlot visualization"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Mr.Spaghetti 🤌")
        
        # Set window icon
        self._set_window_icon()
        
        self.root.geometry("750x650")
        
        # Initialize data attributes
        self.csv_file_path = None
        self.output_directory = os.getcwd()
        self.html_filename = "hiplot_visualization.html"
        self.df_columns = []
        self.df = None
        
        # Initialize components
        self.column_manager = None
        
        # Setup UI
        self.setup_ui()
    
    def _set_window_icon(self):
        """Set the window icon"""
        try:
            icon_path = resource_path('spaghetti.ico')
            self.root.iconbitmap(icon_path)
        except tk.TclError:
            try:
                icon_path = resource_path('spaghetti.png')
                icon_img = tk.PhotoImage(file=icon_path)
                self.root.tk.call('wm', 'iconphoto', self.root._w, icon_img)
            except Exception as e:
                print(f"Failed to set icon: {e}")
    
    def setup_ui(self):
        """Setup the main user interface"""
        # Create scrollable main frame
        self._create_scrollable_frame()
        
        # Create UI sections
        self._create_file_section()
        self._create_column_section()
        self._create_add_column_section()
        self._create_output_section()
        self._create_config_section()
        self._create_buttons_section()
    
    def _create_scrollable_frame(self):
        """Create the scrollable main frame structure"""
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Canvas and scrollbar
        self.canvas = tk.Canvas(self.main_frame)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.scrollbar = ttk.Scrollbar(self.main_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Mouse wheel scrolling
        self.canvas.bind_all("<MouseWheel>", lambda event: self.canvas.yview_scroll(int(-1*(event.delta/120)), "units"))
        
        # Content frame
        self.content_frame = tk.Frame(self.canvas)
        self.canvas_frame = self.canvas.create_window((0, 0), window=self.content_frame, anchor="nw")
        
        # Configure frame bindings
        self.content_frame.bind("<Configure>", self.on_frame_configure)
        self.canvas.bind("<Configure>", self.on_canvas_configure)
    
    def _create_file_section(self):
        """Create the file selection section"""
        file_frame = tk.LabelFrame(self.content_frame, text="Input File", padx=15, pady=15)
        file_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.load_btn = tk.Button(file_frame, text="Load CSV File", command=self.load_csv, width=20, height=2)
        self.load_btn.pack(pady=5)
        
        self.file_label = tk.Label(file_frame, text="No file selected", wraplength=550)
        self.file_label.pack(pady=5)
    
    def _create_column_section(self):
        """Create the column selection section"""
        self.columns_frame = tk.LabelFrame(
            self.content_frame,
            text="Column Selection (green = visible, gray = hidden, right-click for options)",
            padx=15, pady=15
        )
        self.columns_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.columns_grid_frame = tk.Frame(self.columns_frame)
        self.columns_grid_frame.pack(fill=tk.BOTH, expand=True)
    
    def _create_add_column_section(self):
        """Create the add column section"""
        add_column_frame = tk.Frame(self.content_frame)
        add_column_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.add_column_btn = tk.Button(
            add_column_frame,
            text="Add Column with Expression",
            command=self.show_add_column_dialog,
            width=25,
            state=tk.DISABLED
        )
        self.add_column_btn.pack(side=tk.LEFT, padx=10)
        
        tk.Label(
            add_column_frame,
            text="(e.g., 'col1 + col2', 'col1 * 2', 'np.log(col1)')",
            fg="gray"
        ).pack(side=tk.LEFT, padx=5)
    
    def _create_output_section(self):
        """Create the output settings section"""
        output_frame = tk.LabelFrame(self.content_frame, text="Output Settings", padx=15, pady=15)
        output_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Output directory
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
    
    def _create_config_section(self):
        """Create the visualization configuration section"""
        config_frame = tk.LabelFrame(self.content_frame, text="Visualization Options", padx=15, pady=15)
        config_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Visualization library selection
        tk.Label(config_frame, text="Visualization Library:").grid(row=0, column=0, sticky="w", pady=5)
        lib_frame = tk.Frame(config_frame)
        lib_frame.grid(row=0, column=1, sticky="w", pady=5)
        
        self.viz_library_var = tk.StringVar(value="hiplot")
        tk.Radiobutton(
            lib_frame, 
            text="HiPlot (Interactive & Feature-rich)", 
            variable=self.viz_library_var, 
            value="hiplot"
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Radiobutton(
            lib_frame, 
            text="Plotly (Fast & Lightweight)", 
            variable=self.viz_library_var, 
            value="plotly"
        ).pack(side=tk.LEFT, padx=5)
        
        # Color by dropdown
        tk.Label(config_frame, text="Color by:").grid(row=1, column=0, sticky="w", pady=5)
        self.color_by_var = tk.StringVar()
        self.color_by_dropdown = ttk.Combobox(config_frame, textvariable=self.color_by_var, width=30, state="readonly")
        self.color_by_dropdown.grid(row=1, column=1, sticky="w", pady=5)
        
        # X-axis dropdown
        tk.Label(config_frame, text="X-axis:").grid(row=2, column=0, sticky="w", pady=5)
        self.x_axis_var = tk.StringVar()
        self.x_axis_dropdown = ttk.Combobox(config_frame, textvariable=self.x_axis_var, width=30, state="readonly")
        self.x_axis_dropdown.grid(row=2, column=1, sticky="w", pady=5)
        
        # Y-axis dropdown
        tk.Label(config_frame, text="Y-axis:").grid(row=3, column=0, sticky="w", pady=5)
        self.y_axis_var = tk.StringVar()
        self.y_axis_dropdown = ttk.Combobox(config_frame, textvariable=self.y_axis_var, width=30, state="readonly")
        self.y_axis_dropdown.grid(row=3, column=1, sticky="w", pady=5)
    
    def _create_buttons_section(self):
        """Create the action buttons section"""
        button_frame = tk.Frame(self.content_frame, padx=20, pady=20)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.generate_btn = tk.Button(button_frame, text="Generate HTML", command=self.generate_html, width=15, height=2)
        self.generate_btn.pack(side=tk.LEFT, padx=10)
        
        self.view_btn = tk.Button(button_frame, text="View in Browser", command=self.view_html, width=15, height=2, state=tk.DISABLED)
        self.view_btn.pack(side=tk.LEFT, padx=10)
    
    def on_frame_configure(self, event=None):
        """Handle frame configuration changes"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def on_canvas_configure(self, event=None):
        """Handle canvas configuration changes"""
        if event:
            canvas_width = event.width
            self.canvas.itemconfig(self.canvas_frame, width=canvas_width)
    
    def load_csv(self):
        """Load CSV file and initialize data"""
        file_path = filedialog.askopenfilename(
            title="Select CSV File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if file_path:
            # Save previous column selection state before loading new file
            previous_selection = None
            if self.column_manager:
                previous_selection = self.column_manager.get_column_selection_state()
            
            self.csv_file_path = file_path
            self.file_label.config(text=f"Selected: {os.path.basename(file_path)}")
            
            # Update default HTML filename
            csv_basename = os.path.splitext(os.path.basename(file_path))[0]
            self.filename_var.set(f"{csv_basename}_hiplot.html")
            
            try:
                # Show loading message
                self.file_label.config(text=f"Loading {os.path.basename(file_path)}... This may take a moment.")
                self.root.update()
                
                # Load data
                self.df = pd.read_csv(file_path)
                columns = self.df.columns.tolist()
                
                # Update file label with info
                self.file_label.config(text=f"Selected: {os.path.basename(file_path)} ({len(self.df)} rows, {len(columns)} columns)")
                
                # Initialize column manager and update UI (pass previous selection)
                self._initialize_data(columns, previous_selection)
                
                # Adjust window size
                configure_window_size(self.root, len(columns))
                
                # Enable add column button
                self.add_column_btn.config(state=tk.NORMAL)
                
            except Exception as e:
                self.file_label.config(text=f"Error: {os.path.basename(file_path)}")
                messagebox.showerror("Error", f"Could not read CSV file: {str(e)}")
    
    def _initialize_data(self, columns, previous_selection=None):
        """Initialize data and create column manager"""
        self.df_columns = columns
        
        # Create column manager
        self.column_manager = ColumnManager(self.root, self.df, self.df_columns)
        self.column_manager.set_columns_updated_callback(self.update_dropdown_lists)
        
        # Create column grid (with previous selection if available)
        self.column_manager.create_column_grid(self.columns_grid_frame, previous_selection)
        
        # Update dropdowns
        self.update_dropdown_lists()
        self._set_default_dropdown_values(columns)
        
        # Update scroll region
        self.root.update_idletasks()
        self.on_frame_configure()
    
    def _set_default_dropdown_values(self, columns):
        """Set intelligent default values for dropdowns"""
        if not columns:
            return
        
        try:
            numeric_cols = self.df.select_dtypes(include=['number']).columns.tolist()
            
            if numeric_cols:
                self.color_by_var.set(numeric_cols[-1])
                self.x_axis_var.set(numeric_cols[0])
                
                if len(numeric_cols) > 1:
                    self.y_axis_var.set(numeric_cols[-1])
                else:
                    self.y_axis_var.set(columns[min(1, len(columns)-1)])
            else:
                self.color_by_var.set(columns[0])
                self.x_axis_var.set(columns[0])
                self.y_axis_var.set(columns[min(1, len(columns)-1)])
        except:
            # Fallback
            self.color_by_var.set(columns[0])
            self.x_axis_var.set(columns[0])
            self.y_axis_var.set(columns[min(1, len(columns)-1)])
    
    def update_dropdown_lists(self):
        """Update dropdown lists with active columns"""
        if not self.column_manager:
            return
        
        active_cols = self.column_manager.get_active_columns_with_display_names()
        
        for dropdown in [self.color_by_dropdown, self.x_axis_dropdown, self.y_axis_dropdown]:
            current_value = dropdown.get()
            dropdown['values'] = active_cols
            
            # Preserve selection if possible
            if current_value in active_cols:
                dropdown.set(current_value)
            elif active_cols:
                dropdown.set(active_cols[0])
            else:
                dropdown.set('')
    
    def show_add_column_dialog(self):
        """Show the add column expression dialog"""
        if self.df is None:
            messagebox.showwarning("Warning", "Please load a CSV file first")
            return
        
        def on_column_created(column_name):
            self.column_manager.handle_new_column_added(column_name)
        
        dialog = ExpressionDialog(self.root, self.df, self.df_columns, on_column_created)
        dialog.show()
    
    def browse_output_dir(self):
        """Browse for output directory"""
        dir_path = filedialog.askdirectory(
            title="Select Directory to Save HTML",
            initialdir=self.output_directory
        )
        
        if dir_path:
            self.output_directory = dir_path
            self.output_dir_var.set(dir_path)
    
    def get_full_output_path(self):
        """Get the full output path for HTML file"""
        filename = self.filename_var.get().strip()
        
        if not filename.lower().endswith('.html'):
            filename += '.html'
        
        return os.path.join(self.output_directory, filename)
    
    def generate_html(self):
        """Generate visualization HTML based on selected library"""
        if not self.csv_file_path:
            messagebox.showwarning("Warning", "Please select a CSV file first")
            return
        
        # Check which library to use
        selected_library = self.viz_library_var.get()
        
        if selected_library == "plotly":
            self._generate_plotly_html()
        else:
            self._generate_hiplot_html()
    
    def _generate_hiplot_html(self):
        """Generate HiPlot HTML visualization"""
        output_path = self.get_full_output_path()
        
        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create output directory: {str(e)}")
                return
        
        try:
            # Show loading state
            self.root.config(cursor="wait")
            self.generate_btn.config(state=tk.DISABLED)
            self.root.update()
            
            # Get active columns data
            active_df = self.column_manager.get_active_columns_df()
            
            if active_df is None or active_df.empty:
                messagebox.showwarning("Warning", "No active columns selected for visualization")
                return
            
            # Create temporary CSV with active columns
            temp_csv_path = os.path.join(os.path.dirname(output_path), "_temp_hiplot.csv")
            active_df.to_csv(temp_csv_path, index=False)
            
            # Create HiPlot experiment
            experiment = hip.Experiment.from_csv(temp_csv_path)
            
            # Configure visualization
            self._configure_experiment(experiment, active_df)
            
            # Save HTML
            experiment.to_html(output_path)
            
            # Cleanup
            self._cleanup_temp_file(temp_csv_path)
            
            # Reset UI state
            self.root.config(cursor="")
            self.generate_btn.config(state=tk.NORMAL)
            
            messagebox.showinfo("Success", f"HiPlot visualization saved to:\n{output_path}")
            self.view_btn.config(state=tk.NORMAL)
            
        except Exception as e:
            self.root.config(cursor="")
            self.generate_btn.config(state=tk.NORMAL)
            
            import traceback
            error_details = traceback.format_exc()
            print(f"Error generating HTML: {str(e)}\n{error_details}")
            messagebox.showerror("Error", f"Failed to generate HTML: {str(e)}")
    
    def _generate_plotly_html(self):
        """Generate Plotly Parallel Coordinates HTML visualization"""
        output_path = self.get_full_output_path()
        
        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create output directory: {str(e)}")
                return
        
        try:
            # Check if plotly is installed
            try:
                import plotly.graph_objects as go
                import plotly.express as px
            except ImportError:
                response = messagebox.askyesno(
                    "Plotly Not Installed",
                    "Plotly is not installed. Would you like to install it now?\n\n"
                    "This will run: pip install plotly",
                    icon='question'
                )
                if response:
                    import subprocess
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "plotly"])
                    import plotly.graph_objects as go
                    import plotly.express as px
                    messagebox.showinfo("Success", "Plotly has been installed successfully!")
                else:
                    return
            
            # Show loading state
            self.root.config(cursor="wait")
            self.generate_btn.config(state=tk.DISABLED)
            self.root.update()
            
            # Get active columns data
            active_df = self.column_manager.get_active_columns_df()
            
            if active_df is None or active_df.empty:
                messagebox.showwarning("Warning", "No active columns selected for visualization")
                return
            
            # Get configuration
            color_by = self.color_by_var.get()
            
            # Prepare data for Plotly
            # Separate numeric and categorical columns
            numeric_cols = active_df.select_dtypes(include=['number']).columns.tolist()
            categorical_cols = active_df.select_dtypes(exclude=['number']).columns.tolist()
            
            # Create dimensions for parallel coordinates
            dimensions = []
            
            # Add numeric dimensions
            for col in numeric_cols:
                dimensions.append(dict(
                    label=col,
                    values=active_df[col]
                ))
            
            # Add categorical dimensions (encode them)
            for col in categorical_cols:
                # Convert categorical to numeric codes
                active_df[f'{col}_encoded'] = pd.Categorical(active_df[col]).codes
                dimensions.append(dict(
                    label=col,
                    values=active_df[f'{col}_encoded'],
                    tickvals=list(range(len(active_df[col].unique()))),
                    ticktext=list(active_df[col].unique())
                ))
            
            # Prepare color scale
            if color_by and color_by in active_df.columns:
                if color_by in numeric_cols:
                    color_values = active_df[color_by]
                    colorscale = 'Viridis'
                else:
                    color_values = active_df[f'{color_by}_encoded']
                    colorscale = 'Viridis'
            else:
                # Default to first numeric column
                if numeric_cols:
                    color_values = active_df[numeric_cols[0]]
                    colorscale = 'Viridis'
                else:
                    color_values = list(range(len(active_df)))
                    colorscale = 'Viridis'
            
            # Create parallel coordinates plot
            fig = go.Figure(data=
                go.Parcoords(
                    line=dict(
                        color=color_values,
                        colorscale=colorscale,
                        showscale=True,
                        cmin=min(color_values) if len(color_values) > 0 else 0,
                        cmax=max(color_values) if len(color_values) > 0 else 1
                    ),
                    dimensions=dimensions
                )
            )
            
            # Update layout
            fig.update_layout(
                title=f"Parallel Coordinates Plot - {os.path.basename(self.csv_file_path)}",
                font=dict(size=12),
                height=700,
                margin=dict(l=100, r=100, t=100, b=50)
            )
            
            # Save as HTML
            fig.write_html(output_path, include_plotlyjs='cdn')
            
            # Reset UI state
            self.root.config(cursor="")
            self.generate_btn.config(state=tk.NORMAL)
            
            messagebox.showinfo("Success", f"Plotly visualization saved to:\n{output_path}")
            self.view_btn.config(state=tk.NORMAL)
            
        except Exception as e:
            self.root.config(cursor="")
            self.generate_btn.config(state=tk.NORMAL)
            
            import traceback
            error_details = traceback.format_exc()
            print(f"Error generating Plotly HTML: {str(e)}\n{error_details}")
            messagebox.showerror("Error", f"Failed to generate Plotly HTML: {str(e)}")
    
    def _configure_experiment(self, experiment, active_df):
        """Configure the HiPlot experiment"""
        color_by = self.color_by_var.get()
        x_axis = self.x_axis_var.get()
        y_axis = self.y_axis_var.get()
        
        if color_by and color_by in active_df.columns:
            experiment.colorby = color_by
        
        # Configure parallel plot
        experiment.display_data(hip.Displays.PARALLEL_PLOT).update({
            'height': 700,
        })
        
        # Configure XY plot if both axes specified
        if x_axis and y_axis and x_axis in active_df.columns and y_axis in active_df.columns:
            experiment.display_data(hip.Displays.XY).update({
                'axis_x': x_axis,
                'axis_y': y_axis,
            })
    
    def _cleanup_temp_file(self, temp_csv_path):
        """Clean up temporary CSV file"""
        try:
            os.remove(temp_csv_path)
        except Exception as e:
            print(f"Warning: Could not remove temp file: {e}")
    
    def view_html(self):
        """Open generated HTML in browser"""
        output_path = self.get_full_output_path()
        
        if os.path.exists(output_path):
            webbrowser.open('file://' + os.path.realpath(output_path))
        else:
            messagebox.showwarning("Warning", "HTML file not found. Generate it first.")

