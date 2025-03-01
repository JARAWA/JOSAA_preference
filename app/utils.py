import pandas as pd
import numpy as np
import plotly.express as px
import math
from pathlib import Path
from datetime import datetime

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

def get_unique_branches():
    """Get list of unique branches from the dataset"""
    df = load_data()
    if df is not None:
        unique_branches = sorted(df["Academic Program Name"].dropna().unique().tolist())
        return ["All"] + unique_branches
    return ["All"]

def validate_inputs(jee_rank, category, college_type, preferred_branch, round_no):
    """Validate user inputs"""
    if not jee_rank or jee_rank <= 0:
        rank_type = "JEE Advanced" if college_type == "IIT" else "JEE Main"
        return False, f"Please enter a valid {rank_type} rank (greater than 0)"
    if not category:
        return False, "Please select a category"
    if not college_type:
        return False, "Please select a college type"
    if not preferred_branch:
        return False, "Please select a branch"
    if not round_no:
        return False, "Please select a round"
    return True, ""

def hybrid_probability_calculation(rank, opening_rank, closing_rank):
    """Hybrid approach combining logistic and piece-wise probability calculations"""
    try:
        # Logistic function calculation
        M = (opening_rank + closing_rank) / 2
        S = (closing_rank - opening_rank) / 10
        if S == 0:
            S = 1
        logistic_prob = 1 / (1 + math.exp((rank - M) / S)) * 100

        # Piece-wise calculation
        if rank < opening_rank:
            improvement = (opening_rank - rank) / opening_rank
            if improvement >= 0.5:
                piece_wise_prob = 99.0
            else:
                piece_wise_prob = 96 + (improvement * 6)
        elif rank == opening_rank:
            piece_wise_prob = 95.0
        elif rank < closing_rank:
            range_width = closing_rank - opening_rank
            position = (rank - opening_rank) / range_width
            if position <= 0.2:
                piece_wise_prob = 94 - (position * 70)
            elif position <= 0.5:
                normalized_pos = (position - 0.2) / 0.3
                piece_wise_prob = 80 - (normalized_pos * 20)
            elif position <= 0.8:
                normalized_pos = (position - 0.5) / 0.3
                piece_wise_prob = 60 - (normalized_pos * 20)
            else:
                normalized_pos = (position - 0.8) / 0.2
                piece_wise_prob = 40 - (normalized_pos * 20)
        elif rank == closing_rank:
            piece_wise_prob = 15.0
        elif rank <= closing_rank + 10:
            piece_wise_prob = 5.0
        else:
            piece_wise_prob = 0.0

        # Combine probabilities
        if rank < opening_rank:
            improvement = (opening_rank - rank) / opening_rank
            if improvement > 0.5:
                final_prob = max(logistic_prob, 95)
            else:
                final_prob = (logistic_prob * 0.4 + piece_wise_prob * 0.6)
        elif rank <= closing_rank:
            final_prob = (logistic_prob * 0.7 + piece_wise_prob * 0.3)
        else:
            if rank > closing_rank + 100:
                final_prob = 0.0
            else:
                final_prob = min(logistic_prob, 5)

        return round(final_prob, 2)

    except Exception as e:
        print(f"Error in probability calculation: {str(e)}")
        return 0.0

def get_probability_interpretation(probability):
    """Convert probability percentage to text interpretation"""
    if probability >= 95:
        return "Very High Chance"
    elif probability >= 80:
        return "High Chance"
    elif probability >= 60:
        return "Moderate Chance"
    elif probability >= 40:
        return "Low Chance"
    elif probability > 0:
        return "Very Low Chance"
    else:
        return "No Chance"

def plot_probability_distribution(df):
    """Create probability distribution visualization"""
    try:
        fig = px.histogram(
            df,
            x='Admission Probability (%)',
            title='Distribution of Admission Probabilities',
            nbins=20,
            color_discrete_sequence=['#3366cc']
        )
        fig.update_layout(
            xaxis_title="Admission Probability (%)",
            yaxis_title="Number of Colleges",
            showlegend=False,
            title_x=0.5
        )
        return fig
    except Exception as e:
        print(f"Error in plotting: {str(e)}")
        return None

def generate_preference_list(jee_rank, category, college_type, preferred_branch, round_no, min_probability=0):
    """Generate college preference list with admission probabilities"""
    # Validate inputs
    is_valid, error_message = validate_inputs(jee_rank, category, college_type, preferred_branch, round_no)
    if not is_valid:
        return pd.DataFrame(columns=["Error"], data=[[error_message]]), None, None

    # Load data
    df = load_data()
    if df is None:
        return pd.DataFrame(columns=["Error"], data=[["Failed to load data"]]), None, None

    # Preprocess data
    df["Category"] = df["Category"].str.lower()
    df["Academic Program Name"] = df["Academic Program Name"].str.lower()
    df["College Type"] = df["College Type"].str.upper()
    category = category.lower()
    preferred_branch = preferred_branch.lower()
    college_type = college_type.upper()

    # Apply filters
    if category != "all":
        df = df[df["Category"] == category]
    if college_type != "ALL":
        df = df[df["College Type"] == college_type]
    if preferred_branch != "all":
        df = df[df["Academic Program Name"] == preferred_branch]
    df = df[df["Round"] == str(round_no)]

    if df.empty:
        return pd.DataFrame(columns=["Message"], data=[["No colleges found matching your criteria"]]), None, None

    try:
        # Generate college lists
        top_10 = df[
            (df["Opening Rank"] >= jee_rank - 200) &
            (df["Opening Rank"] <= jee_rank)
        ].head(10)

        next_20 = df[
            (df["Opening Rank"] <= jee_rank) &
            (df["Closing Rank"] >= jee_rank)
        ].head(20)

        last_20 = df[
            (df["Closing Rank"] >= jee_rank) &
            (df["Closing Rank"] <= jee_rank + 200)
        ].head(20)

        # Combine results
        final_list = pd.concat([top_10, next_20, last_20]).drop_duplicates()

        # Calculate probabilities
        final_list['Admission Probability (%)'] = final_list.apply(
            lambda x: hybrid_probability_calculation(jee_rank, x['Opening Rank'], x['Closing Rank']),
            axis=1
        )

        final_list['Admission Chances'] = final_list['Admission Probability (%)'].apply(get_probability_interpretation)

        # Filter and sort
        final_list = final_list[final_list['Admission Probability (%)'] >= min_probability]
        final_list = final_list.sort_values('Admission Probability (%)', ascending=False)
        final_list['Preference_Order'] = range(1, len(final_list) + 1)

        # Prepare final result
        result = final_list[[
            'Preference_Order',
            'Institute',
            'College Type',
            'Location',
            'Academic Program Name',
            'Opening Rank',
            'Closing Rank',
            'Admission Probability (%)',
            'Admission Chances'
        ]].rename(columns={
            'Preference_Order': 'Preference',
            'Academic Program Name': 'Branch'
        })

        # Generate visualization
        prob_plot = plot_probability_distribution(result)

        return result, None, prob_plot

    except Exception as e:
        return pd.DataFrame(columns=["Error"], data=[[f"Error: {str(e)}"]]), None, None
