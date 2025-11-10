"""Test if HiPlot can generate offline HTML"""
import hiplot as hip
import pandas as pd
import os
import sys

print("=" * 60)
print("HiPlot Offline Test")
print("=" * 60)

# Check HiPlot location
print(f"\n1. HiPlot module location:")
print(f"   {hip.__file__}")

# Check if templates and static exist
hiplot_dir = os.path.dirname(hip.__file__)
templates_dir = os.path.join(hiplot_dir, 'templates')
static_dir = os.path.join(hiplot_dir, 'static')

print(f"\n2. Looking for templates at:")
print(f"   {templates_dir}")
print(f"   Exists: {os.path.exists(templates_dir)}")
if os.path.exists(templates_dir):
    print(f"   Contents: {os.listdir(templates_dir)}")

print(f"\n3. Looking for static at:")
print(f"   {static_dir}")
print(f"   Exists: {os.path.exists(static_dir)}")
if os.path.exists(static_dir):
    print(f"   Contents: {os.listdir(static_dir)}")

# Try to generate HTML
print(f"\n4. Generating test HTML...")
try:
    df = pd.DataFrame({
        'x': [1, 2, 3, 4, 5],
        'y': [2, 4, 6, 8, 10],
        'z': [1, 4, 9, 16, 25]
    })
    
    exp = hip.Experiment.from_dataframe(df)
    html_content = exp.to_html()
    
    print(f"   HTML generated successfully!")
    print(f"   Length: {len(html_content)} bytes")
    print(f"   Contains 'hiplot.bundle.js': {'hiplot.bundle.js' in html_content}")
    print(f"   Is likely embedded (>1MB): {len(html_content) > 1000000}")
    
    # Save to file
    output_file = "test_hiplot_output.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"   Saved to: {os.path.abspath(output_file)}")
    
except Exception as e:
    print(f"   ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Test completed. Check the output above.")
print("=" * 60)

input("\nPress Enter to exit...")

