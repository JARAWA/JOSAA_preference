from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import gradio as gr
import pandas as pd
import plotly.express as px
import numpy as np
import math
from datetime import datetime
import requests
from io import StringIO

app = FastAPI(title="JOSAA Predictor API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class PredictionInput(BaseModel):
    jee_rank: int
    category: str
    college_type: str
    preferred_branch: str
    round_no: str
    min_probability: float = 0

class PredictionOutput(BaseModel):
    preferences: List[dict]
    plot_data: Optional[dict] = None

# Utility functions
def load_data():
    try:
        url = "https://raw.githubusercontent.com/JARAWA/JOSAA_preference/refs/heads/main/josaa2024_cutoff.csv"
        response = requests.get(url)
        response.raise_for_status()
        
        df = pd.read_csv(StringIO(response.text))
        df["Opening Rank"] = pd.to_numeric(df["Opening Rank"], errors="coerce").fillna(9999999)
        df["Closing Rank"] = pd.to_numeric(df["Closing Rank"], errors="coerce").fillna(9999999)
        df["Round"] = df["Round"].astype(str)
        return df
    except Exception as e:
        print(f"Error loading data: {e}")
        return None

def get_unique_branches():
    try:
        df = load_data()
        if df is not None:
            unique_branches = sorted(df["Academic Program Name"].dropna().unique().tolist())
            return ["All"] + unique_branches
        return ["All"]
    except Exception as e:
        print(f"Error getting branches: {e}")
        return ["All"]

def hybrid_probability_calculation(rank, opening_rank, closing_rank):
    try:
        M = (opening_rank + closing_rank) / 2
        S = (closing_rank - opening_rank) / 10
        if S == 0:
            S = 1
        logistic_prob = 1 / (1 + math.exp((rank - M) / S)) * 100

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
                piece_wise_prob = 80 - ((position - 0.2) / 0.3 * 20)
            elif position <= 0.8:
                piece_wise_prob = 60 - ((position - 0.5) / 0.3 * 20)
            else:
                piece_wise_prob = 40 - ((position - 0.8) / 0.2 * 20)
        elif rank == closing_rank:
            piece_wise_prob = 15.0
        elif rank <= closing_rank + 10:
            piece_wise_prob = 5.0
        else:
            piece_wise_prob = 0.0

        if rank < opening_rank:
            improvement = (opening_rank - rank) / opening_rank
            final_prob = max(logistic_prob, 95) if improvement > 0.5 else (logistic_prob * 0.4 + piece_wise_prob * 0.6)
        elif rank <= closing_rank:
            final_prob = (logistic_prob * 0.7 + piece_wise_prob * 0.3)
        else:
            final_prob = 0.0 if rank > closing_rank + 100 else min(logistic_prob, 5)

        return round(final_prob, 2)
    except Exception as e:
        print(f"Error in probability calculation: {str(e)}")
        return 0.0

def get_probability_interpretation(probability):
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

def predict_preferences(jee_rank, category, college_type, preferred_branch, round_no, min_prob):
    try:
        df = load_data()
        if df is None:
            return pd.DataFrame({"Error": ["Failed to load data"]}), None, None

        df["Category"] = df["Category"].str.lower()
        df["Academic Program Name"] = df["Academic Program Name"].str.lower()
        df["College Type"] = df["College Type"].str.upper()
        
        category = category.lower()
        preferred_branch = preferred_branch.lower()
        college_type = college_type.upper()

        if category != "all":
            df = df[df["Category"] == category]
        if college_type != "ALL":
            df = df[df["College Type"] == college_type]
        if preferred_branch != "all":
            df = df[df["Academic Program Name"] == preferred_branch]
        df = df[df["Round"] == str(round_no)]

        if df.empty:
            return pd.DataFrame({"Message": ["No colleges found matching your criteria"]}), None, None

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

        final_list = pd.concat([top_10, next_20, last_20]).drop_duplicates()
        
        final_list['Admission Probability (%)'] = final_list.apply(
            lambda x: hybrid_probability_calculation(jee_rank, x['Opening Rank'], x['Closing Rank']),
            axis=1
        )

        final_list['Admission Chances'] = final_list['Admission Probability (%)'].apply(get_probability_interpretation)
        
        final_list = final_list[final_list['Admission Probability (%)'] >= min_prob]
        final_list = final_list.sort_values('Admission Probability (%)', ascending=False)
        final_list['Preference_Order'] = range(1, len(final_list) + 1)

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

        fig = px.histogram(
            result,
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

        return result, None, fig
    except Exception as e:
        print(f"Error in predict_preferences: {str(e)}")
        return pd.DataFrame({"Error": [str(e)]}), None, None

def create_gradio_interface():
    with gr.Blocks() as iface:
        gr.Markdown("""
        # 🎓 JOSAA College Preference List Generator
        ### Get personalized college recommendations with admission probability predictions
        """)

        with gr.Row():
            with gr.Column(scale=1, min_width=300):
                college_type = gr.Dropdown(
                    choices=["ALL", "IIT", "NIT", "IIIT", "GFTI"],
                    label="Select College Type",
                    value="ALL"
                )
                
                jee_rank = gr.Number(
                    label="Enter your JEE Main Rank (OPEN-CRL, Others-Category Rank)",
                    minimum=1
                )
                
                category = gr.Dropdown(
                    choices=["All", "OPEN", "OBC-NCL", "OBC-NCL (PwD)", "EWS", "EWS (PwD)",
                            "SC", "SC (PwD)", "ST", "ST (PwD)"],
                    label="Select Category"
                )

            with gr.Column(scale=1, min_width=300):
                preferred_branch = gr.Dropdown(
                    choices=get_unique_branches(),
                    label="Select Preferred Branch"
                )
                round_no = gr.Dropdown(
                    choices=["1", "2", "3", "4", "5", "6"],
                    label="Select Round"
                )
                min_prob = gr.Slider(
                    minimum=0,
                    maximum=100,
                    value=30,
                    step=5,
                    label="Minimum Admission Probability (%)"
                )

        def update_rank_label(college_type_value):
            if college_type_value == "IIT":
                return gr.update(label="Enter your JEE Advanced Rank (OPEN-CRL, Others-Category Rank)")
            return gr.update(label="Enter your JEE Main Rank (OPEN-CRL, Others-Category Rank)")

        college_type.change(
            fn=update_rank_label,
            inputs=college_type,
            outputs=jee_rank
        )

        with gr.Row():
            submit_btn = gr.Button("🔍 Generate Preferences")
            download_btn = gr.Button("📥 Download Excel")

        output_table = gr.Dataframe(
            headers=[
                "Preference",
                "Institute",
                "College Type",
                "Location",
                "Branch",
                "Opening Rank",
                "Closing Rank",
                "Admission Probability (%)",
                "Admission Chances"
            ],
            label="College Preferences"
        )

        prob_plot = gr.Plot(label="Probability Distribution")
        excel_output = gr.File(label="Download Excel File")

        submit_btn.click(
            fn=predict_preferences,
            inputs=[jee_rank, category, college_type, preferred_branch, round_no, min_prob],
            outputs=[output_table, excel_output, prob_plot]
        )

        download_btn.click(
            fn=lambda x: x,
            inputs=[excel_output],
            outputs=[excel_output]
        )

        gr.Markdown("""
        ### 📚 How to use this tool:
        1. First, select the type of college (IIT/NIT/IIIT/GFTI)
        2. Enter your rank:
           - For IITs: Enter your JEE Advanced rank
           - For NITs/IIITs/GFTIs: Enter your JEE Main rank
           - For OPEN category: Enter CRL (Common Rank List) rank
           - For other categories: Enter your category rank
        3. Select your category (OPEN/OBC-NCL/SC/ST/EWS)
        4. Select your preferred branch (optional)
        5. Choose the counselling round
        6. Set minimum admission probability threshold
        7. Click on "Generate Preferences"
        8. Use the Download Excel button to save the results
        """)

        gr.Markdown("""
        ### ⚠️ Disclaimer:
        - This tool provides suggestions based on previous year's cutoff data
        - The admission probabilities are estimates based on historical data
        - The actual cutoffs and admission chances may vary in the current year
        - This is not an official JOSAA tool and should be used only for reference
        - Please verify all information from the official JOSAA website
        - The developers are not responsible for any decisions made based on this tool
        """)

        return iface

# Mount Gradio app
app = gr.mount_gradio_app(app, create_gradio_interface(), path="/")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
