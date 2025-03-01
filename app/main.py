from fastapi import FastAPI, HTTPException
from .models import PredictionInput, PredictionOutput
from .utils import generate_preference_list
import uvicorn

app = FastAPI(title="JOSAA Predictor API")

@app.get("/")
async def root():
    return {"message": "Welcome to JOSAA Predictor API"}

@app.post("/predict", response_model=PredictionOutput)
async def predict(input_data: PredictionInput):
    try:
        preferences, _, plot = generate_preference_list(
            input_data.jee_rank,
            input_data.category,
            input_data.college_type,
            input_data.preferred_branch,
            input_data.round_no,
            input_data.min_probability
        )
        
        return PredictionOutput(
            preferences=preferences.to_dict('records'),
            plot_data=plot.to_dict() if plot else None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)
