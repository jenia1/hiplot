# Building HiPlot GUI Executable

## Quick Build

To create a standalone `.exe` file, simply run:

```bash
python build_exe.py
```

## Output

The executable will be created at:
```
hiplot_gui_modular/dist/HiPlot_GUI.exe
```

**File size:** ~51 MB (includes all dependencies)

## Distribution

The generated `HiPlot_GUI.exe` is a **standalone executable** that can run on any Windows machine **without requiring Python** to be installed.

### To distribute:
1. Copy `HiPlot_GUI.exe` from the `dist` folder
2. Share it with users
3. Users can double-click to run - no installation needed!

## Manual Build (Advanced)

If you want to customize the build, you can run PyInstaller directly:

```bash
pyinstaller --name=HiPlot_GUI ^
            --onefile ^
            --windowed ^
            --icon=..\examples\spaghetti.ico ^
            app.py
```

### Build Options:

- `--onefile`: Creates a single .exe file (recommended)
- `--onedir`: Creates a folder with .exe and dependencies (faster startup)
- `--windowed`: No console window (GUI only)
- `--console`: Show console window (useful for debugging)
- `--icon`: Custom icon for the executable

## Reducing File Size

If you want a smaller executable, you can:

1. Use `--onedir` instead of `--onefile` (~100 MB folder, but faster)
2. Remove unused imports from the code
3. Use UPX compression (add `--upx-dir` option)

## Troubleshooting

### Missing Dependencies
If the .exe crashes on another computer, it might be missing Visual C++ Redistributables:
- Download: https://aka.ms/vs/17/release/vc_redist.x64.exe

### Icon Not Found
If the icon is missing, the build will succeed but without a custom icon.

### Build Errors
- Make sure all dependencies are installed: `pip install -r requirements.txt`
- Delete `build` and `dist` folders and try again
- Check `build/HiPlot_GUI/warn-HiPlot_GUI.txt` for warnings

## What's Included

The executable bundles:
- Python interpreter
- All Python libraries (pandas, numpy, hiplot, plotly, tkinter)
- Application code
- Icon

## Testing

After building, test the executable:
1. Navigate to `dist` folder
2. Double-click `HiPlot_GUI.exe`
3. The application should start without requiring Python

## Notes

- First run may be slow due to unpacking
- Antivirus might scan the .exe (this is normal)
- Windows might show "Unknown publisher" warning (can be solved with code signing)

