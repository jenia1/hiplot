# HiPlot GUI - Modular Version

A modular, user-friendly GUI application for creating HiPlot visualizations from CSV data.

## Project Structure

```
hiplot_gui_modular/
├── __init__.py              # Package initialization
├── app.py                   # Main entry point
├── main_gui.py              # Main GUI class
├── column_manager.py        # Column selection and management
├── data_viewer.py           # Data viewing and editing
├── expression_dialog.py     # Column expression dialog
├── file_loader.py           # Reading CSV/Excel and merging several files
├── utils.py                 # Utility functions
└── README.md               # This file
```

## Module Descriptions

### `main_gui.py`
- **HiPlotGUI**: Main application window and coordination
- Handles file loading, output settings, and visualization generation
- Coordinates between different modules

### `column_manager.py`
- **ColumnManager**: Manages column selection grid and operations
- Handles column toggling, renaming, and filtering
- Context menu operations (remove constants, deselect all)

### `data_viewer.py`
- **DataViewer**: Popup window for viewing and editing column data
- Supports pagination for large datasets
- Toggle between all values and unique values view
- Bulk editing capabilities

### `expression_dialog.py`
- **ExpressionDialog**: Dialog for creating computed columns
- Mathematical expression evaluation
- Column reference assistance
- Built-in operation examples

### `file_loader.py`
- Reads CSV/Excel files (header spaces stripped) and merges several into one table
- Unique `File Name` values (adds the folder when two files share a name)
- Checks for mismatched columns and number/text conflicts before merging

### `utils.py`
- **ToolTipHelper**: Tooltip creation utilities
- **resource_path()**: Resource path resolution for PyInstaller
- Various helper functions for UI sizing and configuration

## Running the Application

To run the modular version:

```bash
cd hiplot_gui_modular
python app.py
```

## Features

### Original Features Preserved
- ✅ CSV and Excel (.xlsx/.xlsm/.xls, with sheet picker) file loading
- ✅ Load several files at once (or "Add More Files" later): merged into one table with a
  `File Name` column; columns missing from a file are empty (NaN) for its rows. Warns when more
  than 30% of a file's columns differ from the first file, or when a column is numbers in one
  file and text in another
- ✅ Type-to-search: on the main screen just start typing (outside text fields) and matching
  column names turn blue bold (Backspace deletes, Esc clears). In lists and dropdowns
  (Optimized Parameters, expression window, Color by / X / Y) typing jumps to the first match
- ✅ Export the edited data (visible columns, renames, filters, added columns) to CSV
- ✅ Interactive column selection with visual feedback
- ✅ Mathematical expression columns
- ✅ Data viewing and editing with pagination
- ✅ Column renaming and management
- ✅ HiPlot visualization generation
- ✅ Output directory and filename customization
- ✅ Browser integration for viewing results

### Improvements Through Modularization
- 🔧 **Better Code Organization**: Each feature in its own module
- 🔧 **Easier Maintenance**: Isolated functionality for easier debugging
- 🔧 **Enhanced Testability**: Individual modules can be tested separately
- 🔧 **Improved Reusability**: Components can be reused in other projects
- 🔧 **Cleaner Dependencies**: Clear separation of concerns

## Dependencies

- tkinter (built-in with Python)
- pandas
- numpy
- hiplot
- webbrowser (built-in)
- pathlib (built-in)

## File Size Comparison

- **Original**: ~1,332 lines in single file
- **Modular**: ~6 focused modules, easier to navigate and maintain

## Migration Notes

The modular version maintains 100% functional compatibility with the original `hiplot_gui.py`. All features work identically, but the code is now organized for better maintainability and future development.

