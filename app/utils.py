import pandas as pd
import numpy as np
import plotly.express as px
import math
from pathlib import Path

# Move all your helper functions here
def load_data():
    """Load and preprocess the JOSAA data"""
    try:
        file_path = Path(__file__).parent.parent / "data" / "josaa2024_cutoff.csv"
        if not file_path.exists():
            raise FileNotFoundError(f"Data file not found at {file_path}")

        df = pd.read_csv(file_path)
        df["Opening Rank"] = pd.to_numeric(df["Opening Rank"], errors="coerce").fillna(9999999)
        df["Closing Rank"] = pd.to_numeric(df["Closing Rank"], errors="coerce").fillna(9999999)
        df["Round"] = df["Round"].astype(str)
        return df
    except Exception as e:
        print(f"Error loading file: {str(e)}")
        return None

# Add all your other utility functions here:
# - hybrid_probability_calculation
# - get_probability_interpretation
# - plot_probability_distribution
# - generate_preference_list
# (Copy these from your original code, making necessary adjustments)
