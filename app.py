from flask import Flask, request, jsonify, send_file
import pandas as pd
import numpy as np
import os
import plotly.express as px
import math
from datetime import datetime

app = Flask(__name__)

# File path
FILE_PATH = "josaa2024_cutoff.csv"

def load_data():
    """Load and preprocess the JOSAA data"""
    try:
        if not os.path.exists(FILE_PATH):
            return None

        df = pd.read_csv(FILE_PATH)
        df["Opening Rank"] = pd.to_numeric(df["Opening Rank"], errors="coerce").fillna(9999999)
        df["Closing Rank"] = pd.to_numeric(df["Closing Rank"], errors="coerce").fillna(9999999)
        df["Round"] = df["Round"].astype(str)
        return df
    except Exception as e:
        print(f"Error loading file: {str(e)}")
        return None

@app.route("/")
def index():
    return send_file("index.html")

@app.route("/static/<path:path>")
def send_static(path):
    return send_file(f"static/{path}")

@app.route("/generate_preferences", methods=["POST"])
def generate_preferences():
    data = request.get_json()
    jee_rank = data.get("jee_rank")
    category = data.get("category")
    college_type = data.get("college_type")
    preferred_branch = data.get("preferred_branch")
    round_no = data.get("round_no")
    min_prob = data.get("min_prob")

    # Validate inputs
    if not jee_rank or jee_rank <= 0:
        return jsonify({"error": "Please enter a valid JEE rank (greater than 0)"}), 400

    df = load_data()
    if df is None:
        return jsonify({"error": "Failed to load data"}), 500

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
        return jsonify({"error": "No colleges found matching your criteria"}), 404

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

    df["Admission Probability (%)"] = df.apply(
        lambda x: hybrid_probability_calculation(jee_rank, x["Opening Rank"], x["Closing Rank"]),
        axis=1
    )
    df["Admission Chances"] = df["Admission Probability (%)"].apply(get_probability_interpretation)

    df = df[df["Admission Probability (%)"] >= min_prob]
    df = df.sort_values("Admission Probability (%)", ascending=False)
    df["Preference_Order"] = range(1, len(df) + 1)

    result = df[[
        "Preference_Order",
        "Institute",
        "College Type",
        "Location",
        "Academic Program Name",
        "Opening Rank",
        "Closing Rank",
        "Admission Probability (%)",
        "Admission Chances"
    ]].rename(columns={
        "Preference_Order": "Preference",
        "Academic Program Name": "Branch"
    })

    fig = px.histogram(
        result,
        x="Admission Probability (%)",
        title="Distribution of Admission Probabilities",
        nbins=20,
        color_discrete_sequence=["#3366cc"]
    )
    fig.update_layout(
        xaxis_title="Admission Probability (%)",
        yaxis_title="Number of Colleges",
        showlegend=False,
        title_x=0.5
    )
    plot_url = f"static/plot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    fig.write_image(plot_url)

    return jsonify({
        "preferences": result.to_dict(orient="records"),
        "plot": plot_url
    })

@app.route("/download_excel")
def download_excel():
    df = load_data()
    if df is None:
        return "Failed to load data", 500

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    excel_file = f"college_preferences_{timestamp}.xlsx"

    writer = pd.ExcelWriter(excel_file, engine="openpyxl")
    df.to_excel(writer, index=False)
    writer.save()

    return send_file(excel_file, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)