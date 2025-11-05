"""
Script to build HiPlot GUI as a standalone executable using PyInstaller.

Run this script to create a .exe file:
    python build_exe.py
"""
import subprocess
import sys
import os

def build_exe():
    """Build the executable using PyInstaller"""
    
    # Get the directory containing this script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Check if icon file exists
    icon_path = os.path.join(current_dir, '..', 'examples', 'spaghetti.ico')
    if not os.path.exists(icon_path):
        icon_path = None
        print("Warning: Icon file not found. Building without custom icon.")
    else:
        print(f"Using icon: {icon_path}")
    
    # Find hiplot templates directory
    try:
        import hiplot
        hiplot_dir = os.path.dirname(hiplot.__file__)
        templates_dir = os.path.join(hiplot_dir, 'templates')
        static_dir = os.path.join(hiplot_dir, 'static')
        print(f"Found hiplot templates at: {templates_dir}")
        print(f"Found hiplot static at: {static_dir}")
    except Exception as e:
        print(f"Warning: Could not locate hiplot directories: {e}")
        templates_dir = None
        static_dir = None
    
    # PyInstaller command
    cmd = [
        'pyinstaller',
        '--name=HiPlot_GUI',  # Name of the executable
        '--onedir',  # Create a directory with exe and dependencies (FASTER!)
        '--windowed',  # No console window (GUI app)
        '--clean',  # Clean cache before building
        '--noconfirm',  # Replace output directory without confirmation
        
        # Add all Python files as hidden imports
        '--hidden-import=tkinter',
        '--hidden-import=tkinter.ttk',
        '--hidden-import=pandas',
        '--hidden-import=numpy',
        '--hidden-import=hiplot',
        '--hidden-import=plotly',
        '--hidden-import=plotly.graph_objects',
        '--hidden-import=plotly.express',
        
        # Add our modules
        '--hidden-import=main_gui',
        '--hidden-import=column_manager',
        '--hidden-import=data_viewer',
        '--hidden-import=expression_dialog',
        '--hidden-import=utils',
        
        # Add data files (add current directory to search path)
        '--paths=.',
    ]
    
    # Add hiplot data files (templates and static files)
    if templates_dir and os.path.exists(templates_dir):
        cmd.append(f'--add-data={templates_dir};hiplot/templates')
        print(f"Adding templates: {templates_dir}")
    
    if static_dir and os.path.exists(static_dir):
        cmd.append(f'--add-data={static_dir};hiplot/static')
        print(f"Adding static files: {static_dir}")
    
    # Add icon if available
    if icon_path:
        cmd.append(f'--icon={icon_path}')
    
    # Add the main script
    cmd.append('app.py')
    
    print("Building executable...")
    print(f"Command: {' '.join(cmd)}\n")
    
    # Run PyInstaller
    result = subprocess.run(cmd, cwd=current_dir)
    
    if result.returncode == 0:
        dist_folder = os.path.join(current_dir, 'dist', 'HiPlot_GUI')
        exe_path = os.path.join(dist_folder, 'HiPlot_GUI.exe')
        
        print(f"\n✓ Success! Application created at:")
        print(f"  Folder: {dist_folder}")
        print(f"  Executable: {exe_path}")
        
        # Calculate total folder size
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(dist_folder):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                total_size += os.path.getsize(filepath)
        
        exe_size = os.path.getsize(exe_path) / (1024*1024)
        total_size_mb = total_size / (1024*1024)
        
        print(f"\n  📊 Size Details:")
        print(f"     EXE file: {exe_size:.1f} MB (lightweight!)")
        print(f"     Total folder: {total_size_mb:.1f} MB (includes all libraries)")
        print(f"\n  🚀 Fast startup - no unpacking needed!")
    else:
        print("\n✗ Build failed!")
        sys.exit(1)

if __name__ == "__main__":
    build_exe()

