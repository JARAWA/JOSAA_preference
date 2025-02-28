import pandas as pd
import gradio as gr
import numpy as np
from datetime import datetime
import os
import plotly.express as px
import math
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# File path configuration
FILE_PATH = os.path.join(os.path.dirname(__file__), "josaa2024_cutoff.csv")

class ProbabilityCalculator:
    def calculate_probability(self, rank, opening_rank, closing_rank):
        try:
            # Logistic calculation
            M = (opening_rank + closing_rank) / 2
            S = max((closing_rank - opening_rank) / 10, 1)
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
                    piece_wise_prob = 80 - (position * 20)
                elif position <= 0.8:
                    piece_wise_prob = 60 - (position * 20)
                else:
                    piece_wise_prob = 40 - (position * 20)
            elif rank == closing_rank:
                piece_wise_prob = 15.0
            elif rank <= closing_rank + 10:
                piece_wise_prob = 5.0
            else:
                piece_wise_prob = 0.0

            # Final probability
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
            logger.error(f"Probability calculation error: {str(e)}")
            return 0.0

    def get_interpretation(self, probability):
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
        return "No Chance"

def load_data():
    """Load and preprocess the JOSAA data"""
    try:
        df = pd.read_csv(FILE_PATH)
        df["Opening Rank"] = pd.to_numeric(df["Opening Rank"], errors="coerce").fillna(9999999)
        df["Closing Rank"] = pd.to_numeric(df["Closing Rank"], errors="coerce").fillna(9999999)
        df["Round"] = df["Round"].astype(str)
        return df
    except Exception as e:
        logger.error(f"Error loading data: {str(e)}")
        return None

def get_unique_branches():
    df = load_data()
    if df is not None:
        branches = sorted(df["Academic Program Name"].dropna().unique().tolist())
        return ["All"] + branches
    return ["All"]

def generate_preference_list(jee_rank, category, college_type, preferred_branch, round_no, min_probability=0):
    try:
        # Load and filter data
        df = load_data()
        if df is None:
            return pd.DataFrame(columns=["Error"], data=[["Failed to load data"]]), None, None

        # Apply filters
        df["Category"] = df["Category"].str.lower()
        df["Academic Program Name"] = df["Academic Program Name"].str.lower()
        df["College Type"] = df["College Type"].str.upper()
        
        if category.lower() != "all":
            df = df[df["Category"] == category.lower()]
        if college_type.upper() != "ALL":
            df = df[df["College Type"] == college_type.upper()]
        if preferred_branch.lower() != "all":
            df = df[df["Academic Program Name"] == preferred_branch.lower()]
        df = df[df["Round"] == str(round_no)]

        # Calculate probabilities
        calculator = ProbabilityCalculator()
        df['Admission Probability (%)'] = df.apply(
            lambda x: calculator.calculate_probability(jee_rank, x['Opening Rank'], x['Closing Rank']),
            axis=1
        )
        df['Admission Chances'] = df['Admission Probability (%)'].apply(calculator.get_interpretation)

        # Filter and sort
        df = df[df['Admission Probability (%)'] >= min_probability]
        df = df.sort_values('Admission Probability (%)', ascending=False)
        df['Preference'] = range(1, len(df) + 1)

        # Create visualization
        fig = px.histogram(
            df,
            x='Admission Probability (%)',
            title='Distribution of Admission Probabilities',
            nbins=20
        )

        # Prepare final result
        result = df[[
            'Preference',
            'Institute',
            'College Type',
            'Location',
            'Academic Program Name',
            'Opening Rank',
            'Closing Rank',
            'Admission Probability (%)',
            'Admission Chances'
        ]].rename(columns={'Academic Program Name': 'Branch'})

        return result, None, fig

    except Exception as e:
        logger.error(f"Error generating preferences: {str(e)}")
        return pd.DataFrame(columns=["Error"], data=[[f"Error: {str(e)}"]]), None, None

# Define interface options
categories = ["All", "OPEN", "OBC-NCL", "OBC-NCL (PwD)", "EWS", "EWS (PwD)",
              "SC", "SC (PwD)", "ST", "ST (PwD)"]
college_types = ["ALL", "IIT", "NIT", "IIIT", "GFTI"]
rounds = ["1", "2", "3", "4", "5", "6"]
branches = get_unique_branches()

# Create the interface
def create_interface():
    with gr.Blocks(css="static/styles.css") as iface:
        gr.Markdown("""
        # 🎓 JOSAA College Preference List Generator
        ### Get personalized college recommendations with admission probability predictions
        """)

        with gr.Row():
            with gr.Column(scale=1, min_width=300):
                jee_rank = gr.Number(label="Enter your JEE Rank", minimum=1)
                category = gr.Dropdown(choices=categories, label="Select Category")
                college_type = gr.Dropdown(choices=college_types, label="Select College Type")

            with gr.Column(scale=1, min_width=300):
                preferred_branch = gr.Dropdown(choices=branches, label="Select Preferred Branch")
                round_no = gr.Dropdown(choices=rounds, label="Select Round")
                min_prob = gr.Slider(minimum=0, maximum=100, value=30, step=5,
                                   label="Minimum Admission Probability (%)")

        with gr.Row():
            submit_btn = gr.Button("🔍 Generate Preferences")

        with gr.Row():
            output_table = gr.Dataframe(
                headers=["Preference", "Institute", "College Type", "Location", "Branch",
                        "Opening Rank", "Closing Rank", "Admission Probability (%)",
                        "Admission Chances"],
                label="College Preferences"
            )

        with gr.Row():
            prob_plot = gr.Plot(label="Probability Distribution")

        # Handle button click
        submit_btn.click(
            generate_preference_list,
            inputs=[jee_rank, category, college_type, preferred_branch, round_no, min_prob],
            outputs=[output_table, None, prob_plot]
        )

        return iface

if __name__ == "__main__":
    iface = create_interface()
    iface.launch(
        server_name="0.0.0.0",
        server_port=int(os.environ.get("PORT", 7860)),
        share=False
    )
