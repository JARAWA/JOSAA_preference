import gradio as gr
import requests
import json

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

# Define your categories, college_types, etc.
categories = ["All", "OPEN", "OBC-NCL", "OBC-NCL (PwD)", "EWS", "EWS (PwD)",
              "SC", "SC (PwD)", "ST", "ST (PwD)"]
college_types = ["ALL", "IIT", "NIT", "IIIT", "GFTI"]
rounds = ["1", "2", "3", "4", "5", "6"]

# Create the Gradio interface
with gr.Blocks() as iface:
    # Your existing Gradio interface code here
    # (Copy your existing Gradio interface code, but use the new predict_preferences function)

if __name__ == "__main__":
    iface.launch()
