import gradio as gr
import pandas as pd
import requests
import json
from .utils import get_unique_branches

API_URL = "https://your-render-app.onrender.com"  # Update this after deployment

def predict_preferences(jee_rank, category, college_type, preferred_branch, round_no, min_prob):
    try:
        response = requests.post(
            f"{API_URL}/predict",
            json={
                "jee_rank": jee_rank,
                "category": category,
                "college_type": college_type,
                "preferred_branch": preferred_branch,
                "round_no": round_no,
                "min_probability": min_prob
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            return (
                pd.DataFrame(data["preferences"]),
                None,  # Excel output
                data["plot_data"]
            )
        else:
            return pd.DataFrame({"Error": [f"API Error: {response.text}"]}), None, None
    except Exception as e:
        return pd.DataFrame({"Error": [str(e)]}), None, None

def update_rank_label(college_type_value):
    if college_type_value == "IIT":
        new_label = "Enter your JEE Advanced Rank (OPEN-CRL, Others-Category Rank)"
    else:
        new_label = "Enter your JEE Main Rank (OPEN-CRL, Others-Category Rank)"
    return {
        jee_rank: gr.update(label=new_label, value=None)
    }

# Define dropdown options
categories = ["All", "OPEN", "OBC-NCL", "OBC-NCL (PwD)", "EWS", "EWS (PwD)",
              "SC", "SC (PwD)", "ST", "ST (PwD)"]
college_types = ["ALL", "IIT", "NIT", "IIIT", "GFTI"]
rounds = ["1", "2", "3", "4", "5", "6"]
branches = get_unique_branches()

# Create the interface
with gr.Blocks() as iface:
    gr.Markdown("""
    # 🎓 JOSAA College Preference List Generator
    ### Get personalized college recommendations with admission probability predictions
    """)

    with gr.Row():
        with gr.Column(scale=1, min_width=300):
            college_type = gr.Dropdown(
                choices=college_types,
                label="Select College Type",
                value="ALL",
                interactive=True
            )
            
            jee_rank = gr.Number(
                label="Enter your JEE Main Rank (OPEN-CRL, Others-Category Rank)",
                minimum=1,
                interactive=True
            )
            
            category = gr.Dropdown(
                choices=categories,
                label="Select Category"
            )

        with gr.Column(scale=1, min_width=300):
            preferred_branch = gr.Dropdown(
                choices=branches,
                label="Select Preferred Branch"
            )
            round_no = gr.Dropdown(
                choices=rounds,
                label="Select Round"
            )
            min_prob = gr.Slider(
                minimum=0,
                maximum=100,
                value=30,
                step=5,
                label="Minimum Admission Probability (%)"
            )

    college_type.change(
        fn=update_rank_label,
        inputs=college_type,
        outputs=jee_rank
    )

    with gr.Row():
        submit_btn = gr.Button("🔍 Generate Preferences")
        download_btn = gr.Button("📥 Download Excel")

    with gr.Row():
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
            label="College Preferences",
            wrap=True,
            column_widths=["70px", "200px", "100px", "100px", "200px",
                          "100px", "100px", "100px", "150px"]
        )

    with gr.Row():
        prob_plot = gr.Plot(label="Probability Distribution")

    excel_output = gr.File(label="Download Excel File")

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

if __name__ == "__main__":
    iface.launch()
