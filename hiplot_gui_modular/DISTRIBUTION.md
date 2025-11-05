# HiPlot GUI - Distribution Guide

## 📦 Ready-to-Distribute Executable

Your standalone Windows application is ready at:
```
hiplot_gui_modular/dist/HiPlot_GUI.exe
```

**Size:** ~52 MB  
**Requirements:** None! (Works on any Windows PC without Python)

## 🚀 Quick Start for End Users

Simply **double-click** `HiPlot_GUI.exe` to start the application!

No installation needed. No Python required.

## 📋 Features Included

✅ Load and visualize CSV files  
✅ Interactive column selection (green/gray/yellow)  
✅ Filter data by unchecking unique values  
✅ Create calculated columns with expressions  
✅ Choose between HiPlot and Plotly visualizations  
✅ Generate standalone HTML visualizations  
✅ View and edit column data  
✅ Rename columns  
✅ Remove constant columns  

## 💾 Distributing to Users

### Option 1: Direct Copy
1. Copy `HiPlot_GUI.exe` to a USB drive or network folder
2. Users can run it directly - no setup needed!

### Option 2: Zip File
```bash
# Create a zip file for easy sharing
cd dist
powershell Compress-Archive -Path HiPlot_GUI.exe -DestinationPath HiPlot_GUI.zip
```

### Option 3: Installer (Advanced)
Use tools like Inno Setup or NSIS to create a professional installer.

## ⚠️ First Run Notes

1. **Windows SmartScreen Warning**
   - Windows may show "Unknown Publisher" warning
   - Click "More info" → "Run anyway"
   - This is normal for unsigned executables

2. **Antivirus Scanning**
   - Some antivirus software may scan the .exe
   - This is normal and will only happen on first run
   - The file is safe - it's your compiled Python code!

3. **Startup Time**
   - First launch may take 5-10 seconds (unpacking libraries)
   - Subsequent launches will be faster

## 🔧 System Requirements

- **OS:** Windows 7, 8, 10, or 11
- **RAM:** 512 MB minimum (2 GB recommended for large files)
- **Disk:** 100 MB free space
- **Other:** No dependencies required!

## 📝 Usage Instructions for End Users

### Basic Workflow:
1. **Load CSV**: Click "Load CSV File" button
2. **Select Columns**: Green = visible, Click to toggle
3. **Filter Data** (optional): Right-click column → View Data → Uncheck values
4. **Choose Library**: HiPlot (feature-rich) or Plotly (fast)
5. **Generate**: Click "Generate HTML"
6. **View**: Click "View in Browser"

### Advanced Features:
- **Yellow columns** = Filtered (some values excluded)
- **Add expressions**: Create calculated columns (e.g., `col1 + col2`)
- **Rename columns**: Right-click → Rename Column
- **Edit data**: Right-click → View/Edit Column Data

## 🐛 Troubleshooting

### "The application failed to start"
- Install Visual C++ Redistributable:
  - Download: https://aka.ms/vs/17/release/vc_redist.x64.exe

### Application crashes
- Check available memory (close other programs)
- For very large files (>500MB), use file splitting tools first

### "Access Denied" error
- Run as Administrator (right-click → Run as administrator)
- Or move .exe to a user-writable location (not Program Files)

## 🔄 Updating

To update the application:
1. Download new `HiPlot_GUI.exe`
2. Replace old file
3. Done! No uninstall needed

## 📧 Support

For issues or questions:
- Check that CSV file is properly formatted
- Ensure enough disk space for output HTML
- Verify Windows is up to date

---

**Enjoy your HiPlot GUI application!** 🎉

