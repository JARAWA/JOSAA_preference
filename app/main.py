from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from .models import PredictionInput, PredictionOutput
from .utils import generate_preference_list
import uvicorn

app = FastAPI(title="JOSAA Predictor API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html>
        <head>
            <title>JOSAA Predictor API</title>
        </head>
        <body>
            <h1>Welcome to JOSAA Predictor API</h1>
            <p>Available endpoints:</p>
            <ul>
                <li><a href="/docs">/docs</a> - API documentation</li>
                <li><a href="/redoc">/redoc</a> - Alternative API documentation</li>
                <li>/predict - POST endpoint for predictions</li>
            </ul>
        </body>
    </html>
    """

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Service is running"}

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
    uvicorn.run("app.main:app", host="0.0.0.0", port=10000)
