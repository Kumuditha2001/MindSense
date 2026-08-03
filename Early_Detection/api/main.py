"""
FastAPI backend for MindSense — Early_Detection

Handles:
  - Signup / Login (simple token-based auth, stored in Firestore)
  - Saving a patient's daily health metrics (Heart Rate, Sleep, Study Hours, Academic Stressors)
  - Serving 90-day mental health forecasts from the trained global LSTM model

Data storage: Google Firestore, accessed via plain REST calls (see firestore_client.py) —
no service account key needed because the database is in "test mode". See the note
at the top of firestore_client.py before your final submission.

Run locally with:
    uvicorn api.main:app --reload

Then open http://127.0.0.1:8000/docs to test it in the browser.
"""

from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import datetime

import numpy as np
import joblib
from tensorflow.keras.models import load_model

from . import firestore_client as db
from . import auth_utils

# ---------------------------------------------------------------------------
# Config — must match notebook 3 exactly
# ---------------------------------------------------------------------------
LOOK_BACK = 30
HORIZON = 90
MH_ORDER = ['Normal', 'Mild Stress', 'Moderate Stress', 'Severe Stress', 'Anxiety', 'Depression']

MODEL_PATH = "models/model_lstm_global.keras"
SCALER_PATH = "models/scaler.save"

app = FastAPI(title="MindSense Early Detection API")

model = None
scaler = None


@app.on_event("startup")
def startup():
    global model, scaler
    model = load_model(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
    print("Model and scaler loaded successfully. Using Firestore for storage.")


# ---------------------------------------------------------------------------
# Auth helper — reads "Authorization: Bearer <token>" and returns patient_id
# ---------------------------------------------------------------------------
def get_current_patient_id(authorization: Optional[str] = Header(None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = authorization.split(" ", 1)[1]
    token_doc = db.get_document(f"auth_tokens/{token}")

    if token_doc is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return token_doc["patient_id"]


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(..., min_length=6)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    token: str
    patient_id: str
    name: str
    member_since: str


class HealthMetricRequest(BaseModel):
    heart_rate: float
    sleep_hours: float
    study_hours: float
    academic_stressors: int
    # Self-reported daily check-in (the "Quizzes" screen): which of the 6 states
    # best matches how the student feels today. This is what actually feeds the
    # forecasting model — the other fields above are stored for the app's own
    # display/insights but are not required to be numeric predictors of it.
    mental_health_score: int = Field(
        ..., ge=0, le=5,
        description="0=Normal, 1=Mild Stress, 2=Moderate Stress, 3=Severe Stress, 4=Anxiety, 5=Depression"
    )


class PredictResponse(BaseModel):
    forecast_scores: List[float]
    day_30_category: str
    day_60_category: str
    day_90_category: str


# ---------------------------------------------------------------------------
# Auth endpoints
# ---------------------------------------------------------------------------
@app.post("/api/patients/signup", response_model=AuthResponse)
def signup(req: SignupRequest):
    existing = db.query_collection("patients", field="email", value=req.email, limit=1)
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email already exists")

    pw_hash, salt = auth_utils.hash_password(req.password)
    member_since = datetime.date.today().isoformat()

    patient = db.create_document("patients", {
        "name": req.name,
        "email": req.email,
        "password_hash": pw_hash,
        "salt": salt,
        "member_since": member_since,
    })
    patient_id = patient["id"]

    token = auth_utils.generate_token()
    db.create_document("auth_tokens", {"patient_id": patient_id}, doc_id=token)

    return AuthResponse(token=token, patient_id=patient_id, name=req.name, member_since=member_since)


@app.post("/api/patients/login", response_model=AuthResponse)
def login(req: LoginRequest):
    matches = db.query_collection("patients", field="email", value=req.email, limit=1)

    if not matches:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    patient = matches[0]
    if not auth_utils.verify_password(req.password, patient["salt"], patient["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = auth_utils.generate_token()
    db.create_document("auth_tokens", {"patient_id": patient["id"]}, doc_id=token)

    return AuthResponse(
        token=token, patient_id=patient["id"], name=patient["name"], member_since=patient["member_since"]
    )


# ---------------------------------------------------------------------------
# Health metrics endpoint (the "data insert page" backend)
# Stored as a subcollection: patients/{patient_id}/health_metrics/{auto_id}
# ---------------------------------------------------------------------------
@app.post("/api/health-metrics")
def save_health_metric(req: HealthMetricRequest, authorization: Optional[str] = Header(None)):
    patient_id = get_current_patient_id(authorization)

    db.create_document(
        "health_metrics",
        {
            "date": datetime.date.today().isoformat(),
            "heart_rate": req.heart_rate,
            "sleep_hours": req.sleep_hours,
            "study_hours": req.study_hours,
            "academic_stressors": req.academic_stressors,
            "mental_health_score": req.mental_health_score,
        },
        parent=f"patients/{patient_id}",
    )
    return {"status": "saved"}


@app.get("/api/health-metrics")
def get_health_metrics(authorization: Optional[str] = Header(None)):
    patient_id = get_current_patient_id(authorization)
    rows = db.query_collection("health_metrics", parent=f"patients/{patient_id}", order_by="date")
    return {"metrics": rows}


# ---------------------------------------------------------------------------
# Prediction logic (same as before)
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


@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": model is not None}


@app.get("/api/predict", response_model=PredictResponse)
def predict(authorization: Optional[str] = Header(None)):
    """Predicts using the logged-in patient's own last 30 days of health_metrics."""
    patient_id = get_current_patient_id(authorization)

    rows = db.query_collection("health_metrics", parent=f"patients/{patient_id}", order_by="date")

    if len(rows) < LOOK_BACK:
        raise HTTPException(
            status_code=400,
            detail=f"Need at least {LOOK_BACK} days of logged health metrics before a forecast can be made. You have {len(rows)}.",
        )

    recent_scores = [r["mental_health_score"] for r in rows[-LOOK_BACK:]]
    forecast = recursive_forecast(recent_scores)

    return PredictResponse(
        forecast_scores=forecast.tolist(),
        day_30_category=score_to_category(forecast[29]),
        day_60_category=score_to_category(forecast[59]),
        day_90_category=score_to_category(forecast[89]),
    )
