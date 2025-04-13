import hiplot as hip
import pandas as pd
from pathlib import Path

# Step 1: Create a sample CSV file if you don't have one
# This is just for demo purposes - you would typically use your own CSV file
def create_sample_csv(file_path: str):
    """Create a sample CSV file with hyperparameter tuning results."""
    data = [
        {'dropout': 0.1, 'lr': 0.001, 'loss': 10.0, 'optimizer': 'SGD', 'accuracy': 0.65},
        {'dropout': 0.15, 'lr': 0.01, 'loss': 3.5, 'optimizer': 'Adam', 'accuracy': 0.75},
        {'dropout': 0.3, 'lr': 0.1, 'loss': 4.5, 'optimizer': 'Adam', 'accuracy': 0.70},
        {'dropout': 0.2, 'lr': 0.05, 'loss': 5.2, 'optimizer': 'SGD', 'accuracy': 0.68},
        {'dropout': 0.25, 'lr': 0.005, 'loss': 8.1, 'optimizer': 'SGD', 'accuracy': 0.67},
        {'dropout': 0.4, 'lr': 0.001, 'loss': 9.5, 'optimizer': 'AdamW', 'accuracy': 0.62},
        {'dropout': 0.1, 'lr': 0.1, 'loss': 3.2, 'optimizer': 'AdamW', 'accuracy': 0.78},
        {'dropout': 0.5, 'lr': 0.01, 'loss': 5.5, 'optimizer': 'Adam', 'accuracy': 0.69}
    ]
    df = pd.DataFrame(data)
    df.to_csv(file_path, index=False)
    print(f"Sample CSV file created at: {file_path}")

# File paths
csv_file_path = "experiment_results.csv"
html_output_path = "hiplot_visualization.html"

# Create sample CSV file (remove this if you have your own CSV)
create_sample_csv(csv_file_path)

# Step 2: Load data from CSV file into a HiPlot experiment
experiment = hip.Experiment.from_csv(csv_file_path)

# Step 3: Configure the experiment (optional)
# Set color by accuracy
experiment.colorby = "accuracy"

# Configure parallel plot display
experiment.display_data(hip.Displays.PARALLEL_PLOT).update({
    'height': 500,  # Height of the parallel plot
    'order': ["optimizer", "lr", "dropout", "loss", "accuracy"]  # Order of the columns
})

# Configure XY plot display
experiment.display_data(hip.Displays.XY).update({
    'axis_x': 'lr',  # Parameter for X axis
    'axis_y': 'accuracy',  # Parameter for Y axis
})

# Step 4: Save experiment as HTML
experiment.to_html(html_output_path)
print(f"HiPlot visualization saved to: {html_output_path}")

# Step 5: Display the experiment (works in Jupyter notebooks)
# If you're running this in a Jupyter notebook, you can also display it directly:
# experiment.display()

print(f"You can open {html_output_path} in a web browser to view the visualization")