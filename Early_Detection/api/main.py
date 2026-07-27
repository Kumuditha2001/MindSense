"""
FastAPI backend for MindSense — Early_Detection
Serves 90-day (3-month) mental health forecasts from the trained global LSTM model.

Run locally with:
    uvicorn api.main:app --reload

Then open http://127.0.0.1:8000/docs to test it in the browser.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List

import numpy as np
import joblib
from tensorflow.keras.models import load_model

# ---------------------------------------------------------------------------
# Config — must match notebook 3 exactly
# ---------------------------------------------------------------------------
LOOK_BACK = 30
HORIZON = 90
MH_ORDER = ['Normal', 'Mild Stress', 'Moderate Stress', 'Severe Stress', 'Anxiety', 'Depression']

MODEL_PATH = "models/model_lstm_global.keras"
SCALER_PATH = "models/scaler.save"

# ---------------------------------------------------------------------------
# Load model + scaler once, at startup (not per-request — that would be slow)
# ---------------------------------------------------------------------------
app = FastAPI(title="MindSense Early Detection API")

model = None
scaler = None


@app.on_event("startup")
def load_artifacts():
    global model, scaler
    model = load_model(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
    print("Model and scaler loaded successfully.")


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------
class PredictRequest(BaseModel):
    # The user's last 30 days of Mental_Health_Status_Score (floats, 0=Normal .. 5=Depression).
    # In a real app, you would compute this daily score from the user's logged
    # behavioral/physiological data using the same rules used to build the training set.
    recent_scores: List[float] = Field(
        ...,
        min_items=LOOK_BACK,
        description=f"At least {LOOK_BACK} most recent daily Mental_Health_Status_Score values, oldest first.",
    )


class PredictResponse(BaseModel):
    forecast_scores: List[float]
    day_30_category: str
    day_60_category: str
    day_90_category: str


# ---------------------------------------------------------------------------
# Core forecasting logic (same as notebook 3)
# ---------------------------------------------------------------------------
def score_to_category(score: float) -> str:
    idx = int(round(score))
    idx = max(0, min(idx, len(MH_ORDER) - 1))
    return MH_ORDER[idx]


def recursive_forecast(recent_scores: List[float], horizon: int = HORIZON, look_back: int = LOOK_BACK) -> np.ndarray:
    scaled = scaler.transform(np.array(recent_scores).reshape(-1, 1)).flatten()
    window = list(scaled[-look_back:])

    preds_scaled = []
    for _ in range(horizon):
        x_input = np.array(window[-look_back:]).reshape((1, look_back, 1))
        next_val = model.predict(x_input, verbose=0)[0, 0]
        preds_scaled.append(next_val)
        window.append(next_val)

    preds_scaled = np.array(preds_scaled).reshape(-1, 1)
    return scaler.inverse_transform(preds_scaled).flatten()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": model is not None}


@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    if len(req.recent_scores) < LOOK_BACK:
        raise HTTPException(status_code=400, detail=f"Need at least {LOOK_BACK} recent daily scores.")

    forecast = recursive_forecast(req.recent_scores)

    return PredictResponse(
        forecast_scores=forecast.tolist(),
        day_30_category=score_to_category(forecast[29]),
        day_60_category=score_to_category(forecast[59]),
        day_90_category=score_to_category(forecast[89]),
    )
