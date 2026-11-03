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

from utils import (resource_path, configure_window_size, grab_when_visible, ToolTipHelper,
                   add_type_ahead, is_text_input, is_search_key)
from file_loader import (
    FILE_NAME_COLUMN, EXCEL_EXTENSIONS, COLUMN_MISMATCH_THRESHOLD, LoadCancelled,
    read_data_file, make_display_names, find_column_mismatches,
    find_type_conflicts, merge_frames
)
from column_manager import ColumnManager
from expression_dialog import ExpressionDialog
from optimized_params import OptimizedParamsWindow

# Fix HiPlot paths for PyInstaller bundle - make it work offline
try:
    if getattr(sys, 'frozen', False):
        # Running in PyInstaller bundle - HiPlot can't find its template/static files
        # We need to monkey-patch it to use the correct bundled paths
        import hiplot.render
        
        bundled_hiplot_dir = Path(sys._MEIPASS) / 'hiplot'
        
        # Patch get_index_html_template to use bundled templates
        _original_get_index_html_template = hiplot.render.get_index_html_template
        
        def _patched_get_index_html_template():
            return hiplot.render.render_jinja_html(str(bundled_hiplot_dir / "templates"), "index.html")
        
        hiplot.render.get_index_html_template = _patched_get_index_html_template
        
        # JS/CSS need no patch: html_inlinize() reads them from hiplot/static next to
        # hiplot/render.py, which PyInstaller places under sys._MEIPASS (see build_exe.py)
        print("HiPlot patched for offline use in PyInstaller bundle")
except Exception as e:
    print(f"Warning: Could not patch HiPlot for offline use: {e}")


class HiPlotGUI:
    """Main GUI application for HiPlot visualization"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Mr.Spaghetti 🤌")
        
        # Set window icon
        self._set_window_icon()
        
        self.root.geometry("750x650")
        
        # Initialize data attributes
        self.csv_file_path = None  # first loaded file
        self.source_names = []     # display name of every loaded file ("File Name" values)
        self.reference_name = None     # first file: others are compared with it
        self.reference_columns = []
        self.output_directory = os.getcwd()
        self.html_filename = "hiplot_visualization.html"
        self.df_columns = []
        self.df = None
        
        # Initialize components
        self.column_manager = None
        self.column_search = ""  # typed on the main screen (no search box)
        
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
        
        self._bind_column_search()
    
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
        self.canvas.bind_all("<MouseWheel>", lambda event: self._on_mouse_wheel(event, -1 if event.delta > 0 else 1))
        # Linux/X11 sends wheel events as Button-4/5 instead of <MouseWheel>
        self.canvas.bind_all("<Button-4>", lambda event: self._on_mouse_wheel(event, -1))
        self.canvas.bind_all("<Button-5>", lambda event: self._on_mouse_wheel(event, 1))
        
        # Content frame
        self.content_frame = tk.Frame(self.canvas)
        self.canvas_frame = self.canvas.create_window((0, 0), window=self.content_frame, anchor="nw")
        
        # Configure frame bindings
        self.content_frame.bind("<Configure>", self.on_frame_configure)
        self.canvas.bind("<Configure>", self.on_canvas_configure)
    
    def _on_mouse_wheel(self, event, direction):
        """Scroll the main window, ignoring wheel events from popup windows"""
        try:
            if event.widget.winfo_toplevel() is not self.root:
                return
        except (AttributeError, KeyError, tk.TclError):
            return
        if event.delta == 0 and event.num not in (4, 5):
            return
        self.canvas.yview_scroll(direction, "units")
    
    def _create_file_section(self):
        """Create the file selection section"""
        file_frame = tk.LabelFrame(self.content_frame, text="Input File", padx=15, pady=15)
        file_frame.pack(fill=tk.X, padx=10, pady=10)
        
        load_buttons = tk.Frame(file_frame)
        load_buttons.pack(pady=5)

        self.load_btn = tk.Button(load_buttons, text="Load CSV / Excel File(s)",
                                  command=self.load_csv, width=22, height=2)
        self.load_btn.pack(side=tk.LEFT, padx=5)

        self.add_files_btn = tk.Button(load_buttons, text="Add More Files",
                                       command=lambda: self.load_csv(append=True),
                                       width=16, height=2, state=tk.DISABLED)
        self.add_files_btn.pack(side=tk.LEFT, padx=5)
        ToolTipHelper.create_tooltip(
            self.add_files_btn,
            "Append more files to the loaded data, keeping your edits,\n"
            "selections, renames and filters. Rows are tagged in the\n"
            f"'{FILE_NAME_COLUMN}' column."
        )
        
        self.file_label = tk.Label(file_frame, text="No file selected", wraplength=550)
        self.file_label.pack(pady=5)
    
    def _create_column_section(self):
        """Create the column selection section"""
        self.columns_frame = tk.LabelFrame(
            self.content_frame,
            text=self.COLUMNS_TITLE,
            padx=15, pady=15
        )
        self.columns_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.columns_grid_frame = tk.Frame(self.columns_frame)
        self.columns_grid_frame.pack(fill=tk.BOTH, expand=True)
    
    COLUMNS_TITLE = "Column Selection (green = visible, gray = hidden, right-click for options)"
    
    def _bind_column_search(self):
        """Typing anywhere on the main screen (outside text fields) searches column names"""
        self.root.bind("<Key>", self._on_main_key, add="+")
    
    def _on_main_key(self, event):
        if self.column_manager is None or is_text_input(event.widget):
            return
        if event.keysym == "Escape":
            if not self.column_search:
                return
            query = ""
        elif event.keysym == "BackSpace":
            if not self.column_search:
                return
            query = self.column_search[:-1]
        elif is_search_key(event):
            query = self.column_search + event.char
        else:
            return
        self._set_column_search(query)
        return "break"
    
    def _set_column_search(self, query, scroll=True):
        """Highlight matching columns and show the typed text in the section title"""
        self.column_search = query
        matches = self.column_manager.set_search(query) if self.column_manager else []
        if query:
            count = f"{len(matches)} match" + ("" if len(matches) == 1 else "es")
            self.columns_frame.config(
                text=f"Search: {query}  -  {count}  (Backspace deletes, Esc clears)",
                fg="blue")
            if matches and scroll:
                self._scroll_into_view(self.column_manager.column_buttons.get(matches[0]))
        else:
            self.columns_frame.config(text=self.COLUMNS_TITLE, fg="black")
    
    def _scroll_into_view(self, widget):
        """Scroll the main window so widget is visible (only if it is not)"""
        if widget is None:
            return
        self.root.update_idletasks()
        content_height = self.content_frame.winfo_height()
        if content_height <= 0:
            return
        top = widget.winfo_rooty() - self.content_frame.winfo_rooty()
        bottom = top + widget.winfo_height()
        view_top = self.canvas.canvasy(0)
        view_bottom = view_top + self.canvas.winfo_height()
        if top < view_top or bottom > view_bottom:
            self.canvas.yview_moveto(max(0, top - 40) / content_height)
    
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
        
        self.optimized_params_btn = tk.Button(
            add_column_frame,
            text="Optimized Parameters",
            command=self.show_optimized_params,
            width=20,
            state=tk.DISABLED,
            bg="light blue"
        )
        self.optimized_params_btn.pack(side=tk.LEFT, padx=10)
        
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
        
        # Type a name in a dropdown to jump to the first match
        add_type_ahead(self.color_by_dropdown, self.x_axis_dropdown, self.y_axis_dropdown)
    
    def _create_buttons_section(self):
        """Create the action buttons section"""
        button_frame = tk.Frame(self.content_frame, padx=20, pady=20)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.generate_btn = tk.Button(button_frame, text="Generate HTML", command=self.generate_html, width=15, height=2)
        self.generate_btn.pack(side=tk.LEFT, padx=10)
        
        self.view_btn = tk.Button(button_frame, text="View in Browser", command=self.view_html, width=15, height=2, state=tk.DISABLED)
        self.view_btn.pack(side=tk.LEFT, padx=10)

        self.export_csv_btn = tk.Button(button_frame, text="Export to CSV", command=self.export_csv, width=15, height=2, state=tk.DISABLED)
        self.export_csv_btn.pack(side=tk.LEFT, padx=10)
    
    def on_frame_configure(self, event=None):
        """Handle frame configuration changes"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def on_canvas_configure(self, event=None):
        """Handle canvas configuration changes"""
        if event:
            canvas_width = event.width
            self.canvas.itemconfig(self.canvas_frame, width=canvas_width)
    
    def load_csv(self, append=False):
        """Load one or more CSV/Excel files. Several files are merged into one table
        with a "File Name" column; append=True adds them to the loaded data."""
        file_paths = filedialog.askopenfilenames(
            title="Add CSV or Excel Files" if append else "Select CSV or Excel File(s)",
            filetypes=[
                ("Data files", "*.csv *.xlsx *.xlsm *.xls"),
                ("CSV files", "*.csv"),
                ("Excel files", "*.xlsx *.xlsm *.xls"),
                ("All files", "*.*")
            ]
        )
        file_paths = list(file_paths) if file_paths else []
        if not file_paths:
            return
        if self.df is None:
            append = False

        # Save previous column selection state before loading new files
        previous_selection = None
        if self.column_manager and not append:
            previous_selection = self.column_manager.get_column_selection_state()

        previous_label = self.file_label.cget("text")
        try:
            loaded = self._read_files(file_paths)
        except LoadCancelled:
            self.file_label.config(text=previous_label)
            return
        except ImportError as e:
            self.file_label.config(text=previous_label)
            messagebox.showerror(
                "Excel Support Missing",
                f"Reading this Excel file needs an extra library:\n{str(e)}\n\n"
                "Install it with: pip install openpyxl (for .xlsx/.xlsm) or pip install xlrd (for .xls)"
            )
            return
        except Exception as e:
            self.file_label.config(text=previous_label)
            messagebox.showerror("Error", str(e))
            return

        names = make_display_names(file_paths, self.source_names if append else ())
        new_frames = [(name, df) for name, (df, _sheet) in zip(names, loaded)]

        # Checks: columns that differ a lot from the first file, mixed number/text columns
        if append:
            reference_name, reference_columns = self.reference_name, self.reference_columns
            to_compare = new_frames
            all_frames = [("loaded data", self.df)] + new_frames
        else:
            reference_name, reference_columns = new_frames[0][0], new_frames[0][1].columns.tolist()
            to_compare = new_frames[1:]
            all_frames = new_frames

        if len(all_frames) > 1:
            mismatches = find_column_mismatches(
                reference_name, reference_columns,
                [(name, df.columns.tolist()) for name, df in to_compare]
            )
            conflicts = find_type_conflicts(all_frames)
            if (mismatches or conflicts) and not self._confirm_load_warnings(mismatches, conflicts):
                self.file_label.config(text=previous_label)
                return

        try:
            # Merge (a single fresh file is used as is, without a "File Name" column)
            if append:
                merged = merge_frames([(self.source_names[0], self.df)] + new_frames)
            elif len(new_frames) == 1:
                merged = new_frames[0][1]
            else:
                merged = merge_frames(new_frames)
        except Exception as e:
            self.file_label.config(text=previous_label)
            messagebox.showerror("Error", f"Could not merge the files: {str(e)}")
            return

        had_file_name_column = append and FILE_NAME_COLUMN in self.df.columns

        if append:
            self.source_names = self.source_names + names
        else:
            self.source_names = names
            self.csv_file_path = file_paths[0]
            self.reference_name, self.reference_columns = reference_name, reference_columns

        self.df = merged
        columns = self.df.columns.tolist()
        self.filename_var.set(f"{self._data_base_name()}_hiplot.html")
        self._update_file_label(loaded, names, append)

        if append:
            # Keep selections, renames and filters; new columns start visible
            self.df_columns = columns
            self.column_manager.replace_data(self.df, self.df_columns)
            self.update_dropdown_lists()
            if not had_file_name_column and FILE_NAME_COLUMN in columns:
                self.color_by_var.set(FILE_NAME_COLUMN)
            self.root.update_idletasks()
            self.on_frame_configure()
        else:
            self._initialize_data(columns, previous_selection)

        configure_window_size(self.root, len(columns))

        for button in (self.add_column_btn, self.optimized_params_btn,
                       self.export_csv_btn, self.add_files_btn):
            button.config(state=tk.NORMAL)

    def _read_files(self, file_paths):
        """Read every file; returns [(DataFrame, sheet name or None)].
        Raises LoadCancelled if the user cancels a sheet choice."""
        excel_count = sum(1 for p in file_paths if p.lower().endswith(EXCEL_EXTENSIONS))
        remembered = {'sheet': None}

        def choose_sheet(file_path, sheet_names):
            # "Use this sheet for the other workbooks too" - when they have it
            if remembered['sheet'] in sheet_names:
                return remembered['sheet']
            sheet, use_for_all = self._ask_sheet_name(
                os.path.basename(file_path), sheet_names, offer_use_for_all=excel_count > 1)
            if use_for_all:
                remembered['sheet'] = sheet
            return sheet

        loaded = []
        for i, file_path in enumerate(file_paths, 1):
            file_name = os.path.basename(file_path)
            progress = f" ({i}/{len(file_paths)})" if len(file_paths) > 1 else ""
            self.file_label.config(text=f"Loading {file_name}{progress}... This may take a moment.")
            self.root.update()
            try:
                loaded.append(read_data_file(file_path, choose_sheet))
            except (LoadCancelled, ImportError):
                raise
            except Exception as e:
                raise RuntimeError(f"Could not read '{file_name}':\n{str(e)}") from e
        return loaded

    def _confirm_load_warnings(self, mismatches, conflicts):
        """Show what looks wrong with the files; True = load anyway"""
        def short_list(items, limit=8):
            text = ", ".join(str(item) for item in items[:limit])
            return text + (f" ... (+{len(items) - limit} more)" if len(items) > limit else "")

        sections = []
        if mismatches:
            lines = [f"More than {COLUMN_MISMATCH_THRESHOLD:.0%} of the columns differ from "
                     f"'{mismatches[0]['reference']}' - this may be the wrong file:"]
            for m in mismatches[:5]:
                lines.append(f"\n• {m['file']}: {m['share']:.0%} different")
                if m['missing']:
                    lines.append(f"    missing: {short_list(m['missing'])}")
                if m['extra']:
                    lines.append(f"    extra: {short_list(m['extra'])}")
            if len(mismatches) > 5:
                lines.append(f"\n... and {len(mismatches) - 5} more file(s)")
            sections.append("\n".join(lines))

        if conflicts:
            lines = ["These columns hold numbers in some files and text in others. "
                     "After merging they become text (shown as categories):"]
            for c in conflicts[:6]:
                samples = f" (text values: {', '.join(repr(s) for s in c['samples'])})" if c['samples'] else ""
                lines.append(f"• {c['column']}: text in {short_list(c['text_files'], 3)}{samples}")
            if len(conflicts) > 6:
                lines.append(f"... and {len(conflicts) - 6} more column(s)")
            sections.append("\n".join(lines))

        return messagebox.askyesno(
            "Check Files Before Merging",
            "\n\n".join(sections) + "\n\nLoad anyway?",
            icon='warning',
            default=messagebox.NO
        )

    def _update_file_label(self, loaded, names, append):
        """Describe the loaded data under the load buttons"""
        rows, cols = len(self.df), len(self.df.columns)
        if len(self.source_names) == 1:
            _df, sheet_name = loaded[0]
            source = self.source_names[0] + (f" [sheet: {sheet_name}]" if sheet_name is not None else "")
            self.file_label.config(text=f"Selected: {source} ({rows} rows, {cols} columns)")
            return

        counts = self.df[FILE_NAME_COLUMN].value_counts()
        shown = [f"{name} ({counts.get(name, 0)})" for name in self.source_names[:6]]
        if len(self.source_names) > 6:
            shown.append(f"... +{len(self.source_names) - 6} more")
        action = f"Added {len(names)} file(s)" if append else f"Merged {len(self.source_names)} files"
        self.file_label.config(
            text=f"{action} - {len(self.source_names)} files, {rows} rows, {cols} columns "
                 f"(incl. '{FILE_NAME_COLUMN}'):\n" + ", ".join(shown)
        )

    def _data_base_name(self):
        """Base name for output files: first file's name, plus _merged for several files"""
        if not self.csv_file_path:
            return "data"
        base = os.path.splitext(os.path.basename(self.csv_file_path))[0]
        return f"{base}_merged" if len(self.source_names) > 1 else base

    def _plot_source_title(self):
        """File name(s) shown in the Plotly title"""
        if len(self.source_names) > 1:
            return f"{len(self.source_names)} merged files"
        return os.path.basename(self.csv_file_path)
    
    def _ask_sheet_name(self, file_name, sheet_names, offer_use_for_all=False):
        """Let the user pick a sheet from a workbook.
        Returns (sheet name or None if cancelled, use the same sheet for the other workbooks)"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Sheet")
        dialog.transient(self.root)
        dialog.resizable(False, False)

        result = {'sheet': None}

        frame = tk.Frame(dialog, padx=15, pady=15)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, text=f"'{file_name}' has {len(sheet_names)} sheets.\nWhich one do you want to load?",
                 justify='left').pack(anchor='w', pady=(0, 10))

        sheet_var = tk.StringVar(value=sheet_names[0])
        combo = ttk.Combobox(frame, textvariable=sheet_var, values=sheet_names, state="readonly", width=35)
        combo.pack(fill=tk.X, pady=(0, 10))
        combo.focus_set()
        add_type_ahead(combo)

        use_for_all_var = tk.BooleanVar(value=True)
        if offer_use_for_all:
            tk.Checkbutton(frame, text="Use this sheet for the other workbooks too\n(asks again if one doesn't have it)",
                           variable=use_for_all_var, justify='left').pack(anchor='w', pady=(0, 10))

        def on_ok(event=None):
            result['sheet'] = sheet_var.get()
            dialog.destroy()

        button_frame = tk.Frame(frame)
        button_frame.pack(fill=tk.X)
        tk.Button(button_frame, text="Cancel", command=dialog.destroy, width=10).pack(side=tk.RIGHT, padx=5)
        tk.Button(button_frame, text="Load", command=on_ok, width=10).pack(side=tk.RIGHT, padx=5)

        dialog.bind("<Return>", on_ok)
        dialog.bind("<Escape>", lambda e: dialog.destroy())

        grab_when_visible(dialog)
        self.root.wait_window(dialog)
        return result['sheet'], offer_use_for_all and use_for_all_var.get()
    
    def _initialize_data(self, columns, previous_selection=None):
        """Initialize data and create column manager"""
        self.df_columns = columns
        self.column_manager = None
        self._set_column_search("")
        
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
            
            # Several files: coloring by file is usually the first thing to look at
            if FILE_NAME_COLUMN in columns and len(self.source_names) > 1:
                self.color_by_var.set(FILE_NAME_COLUMN)
                if numeric_cols:
                    self.x_axis_var.set(numeric_cols[0])
                    self.y_axis_var.set(numeric_cols[-1])
                return
            
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
        
        # Renames / added columns can change the search matches
        if self.column_search:
            self._set_column_search(self.column_search, scroll=False)
        
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
    
    def show_optimized_params(self):
        """Show the optimized parameters window"""
        if self.df is None:
            messagebox.showwarning("Warning", "Please load a CSV file first")
            return
        
        optimized_params_window = OptimizedParamsWindow(
            self.root, self.df, self.df_columns,
            get_source_df=self.column_manager.get_filtered_df,
            get_filter_summary=self.column_manager.get_filter_summary
        )
        optimized_params_window.show()
    
    def get_output_directory(self):
        """Get the output directory from the entry (typed, pasted or browsed)"""
        dir_path = self.output_dir_var.get().strip().strip('"\'')
        if not dir_path:
            return self.output_directory
        return os.path.abspath(os.path.expanduser(dir_path))
    
    def browse_output_dir(self):
        """Browse for output directory"""
        initial_dir = self.get_output_directory()
        if not os.path.isdir(initial_dir):
            initial_dir = self.output_directory
        
        dir_path = filedialog.askdirectory(
            title="Select Directory to Save HTML",
            initialdir=initial_dir
        )
        
        if dir_path:
            self.output_directory = dir_path
            self.output_dir_var.set(dir_path)
    
    def get_full_output_path(self):
        """Get the full output path for HTML file"""
        filename = self.filename_var.get().strip()
        
        if not filename.lower().endswith('.html'):
            filename += '.html'
        
        return os.path.join(self.get_output_directory(), filename)
    
    def generate_html(self):
        """Generate visualization HTML based on selected library"""
        if not self.csv_file_path:
            messagebox.showwarning("Warning", "Please load a CSV or Excel file first")
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
        
        temp_csv_path = None
        try:
            # Show loading state
            self.root.config(cursor="watch")
            self.generate_btn.config(state=tk.DISABLED)
            self.root.update()
            
            # Get active columns data
            active_df = self.column_manager.get_active_columns_df()
            
            if active_df is None or active_df.empty:
                messagebox.showwarning("Warning", "No active columns selected for visualization")
                return
            
            # Create temporary CSV with active columns
            temp_csv_path = os.path.join(os.path.dirname(output_path), "_temp_hiplot.csv")
            active_df.to_csv(temp_csv_path, index=False, encoding='utf-8')
            
            # Create HiPlot experiment
            experiment = hip.Experiment.from_csv(temp_csv_path)
            
            # Configure visualization
            self._configure_experiment(experiment, active_df)
            
            # Save HTML (will use bundled static files via monkey-patch)
            experiment.to_html(output_path)
            
            messagebox.showinfo("Success", f"HiPlot visualization saved to:\n{output_path}")
            self.view_btn.config(state=tk.NORMAL)
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Error generating HTML: {str(e)}\n{error_details}")
            messagebox.showerror("Error", f"Failed to generate HTML: {str(e)}")
        
        finally:
            # Cleanup and reset UI state
            if temp_csv_path:
                self._cleanup_temp_file(temp_csv_path)
            self.root.config(cursor="")
            self.generate_btn.config(state=tk.NORMAL)
    
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
                messagebox.showerror(
                    "Plotly Not Available",
                    "Plotly library is not available.\n\n"
                    "Please use the HiPlot visualization option instead, or reinstall the application.",
                    icon='error'
                )
                return
            
            # Show loading state
            self.root.config(cursor="watch")
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
                # Convert categorical to numeric codes (codes follow categories order)
                categorical = pd.Categorical(active_df[col].astype(str))
                active_df[f'{col}_encoded'] = categorical.codes
                dimensions.append(dict(
                    label=col,
                    values=active_df[f'{col}_encoded'],
                    tickvals=list(range(len(categorical.categories))),
                    ticktext=list(categorical.categories)
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
                        cmin=pd.Series(color_values).min() if len(color_values) > 0 else 0,
                        cmax=pd.Series(color_values).max() if len(color_values) > 0 else 1
                    ),
                    dimensions=dimensions
                )
            )
            
            # Update layout
            fig.update_layout(
                title=f"Parallel Coordinates Plot - {self._plot_source_title()}",
                font=dict(size=12),
                height=700,
                margin=dict(l=100, r=100, t=100, b=50)
            )
            
            # Save as HTML with embedded Plotly (no CDN - works offline)
            fig.write_html(output_path, include_plotlyjs=True)
            
            messagebox.showinfo("Success", f"Plotly visualization saved to:\n{output_path}")
            self.view_btn.config(state=tk.NORMAL)
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Error generating Plotly HTML: {str(e)}\n{error_details}")
            messagebox.showerror("Error", f"Failed to generate Plotly HTML: {str(e)}")
        
        finally:
            # Reset UI state
            self.root.config(cursor="")
            self.generate_btn.config(state=tk.NORMAL)
    
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
    
    def export_csv(self):
        """Export the data as it will be plotted: edited values, added columns,
        visible columns only, renamed, with value filters applied"""
        if self.df is None or not self.column_manager:
            messagebox.showwarning("Warning", "Please load a CSV or Excel file first")
            return

        export_df = self.column_manager.get_active_columns_df()
        if export_df is None or export_df.empty:
            messagebox.showwarning("Warning", "Nothing to export: no visible columns or all rows are filtered out")
            return

        initial_dir = self.get_output_directory()
        if not os.path.isdir(initial_dir):
            initial_dir = self.output_directory
        base_name = self._data_base_name()

        file_path = filedialog.asksaveasfilename(
            title="Export Data to CSV",
            initialdir=initial_dir,
            initialfile=f"{base_name}_edited.csv",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not file_path:
            return

        try:
            # utf-8-sig so Excel opens non-ASCII text correctly
            export_df.to_csv(file_path, index=False, encoding='utf-8-sig')
        except PermissionError:
            messagebox.showerror("Error", f"Could not write the file - is it open in another program?\n{file_path}")
            return
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export CSV: {str(e)}")
            return

        details = f"{len(export_df)} rows, {len(export_df.columns)} columns"
        excluded_rows = len(self.df) - len(export_df)
        if excluded_rows > 0:
            details += f"\n({excluded_rows} row(s) left out by value filters)"
        messagebox.showinfo("Export Complete", f"Data exported to:\n{file_path}\n\n{details}")

    def view_html(self):
        """Open generated HTML in browser"""
        output_path = self.get_full_output_path()
        
        if os.path.exists(output_path):
            webbrowser.open(Path(os.path.realpath(output_path)).as_uri())
        else:
            messagebox.showwarning("Warning", "HTML file not found. Generate it first.")

