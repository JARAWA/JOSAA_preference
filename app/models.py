from pydantic import BaseModel
from typing import List, Optional

class PredictionInput(BaseModel):
    jee_rank: int
    category: str
    college_type: str
    preferred_branch: str
    round_no: str
    min_probability: float

class PredictionOutput(BaseModel):
    preferences: List[dict]
    plot_data: Optional[dict]
