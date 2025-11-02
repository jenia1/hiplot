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
- ✅ CSV file loading and validation
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

