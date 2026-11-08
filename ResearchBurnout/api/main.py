"""
FastAPI backend for MindSense — ResearchBurnout

Handles:
  - Signup / Login (simple token-based auth stored in Firestore with SQLite offline fallback)
  - Saving daily student burnout & behavioral check-in metrics + reflective journal text
  - Predicting Burnout Risk combining:
      1. Behavioral / Lifestyle Model (Random Forest / Ensemble on Sleep, Work Hours, Stress, etc.)
      2. NLP Reflective Journal Classifier (Fine-Tuned Transformer)
      3. Burnout Questionnaire Pipeline (LightGBM Pipeline)
  - Serving holistic burnout insights, risk gauges, contributing factors, and recommendations for the Flutter mobile app

Run locally with:
    uvicorn api.main:app --reload

Then open http://127.0.0.1:8000/docs to test it in the browser.
"""

import os
import datetime
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel, Field, EmailStr
import numpy as np
import pandas as pd

from . import firestore_client as db
from . import auth_utils

# ---------------------------------------------------------------------------
# Directories & Model Artifact Paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))

def resolve_path(*candidates: str) -> Optional[str]:
    for cand in candidates:
        full = os.path.join(PROJECT_DIR, cand) if not os.path.isabs(cand) else cand
        if os.path.exists(full):
            return full
    return None

TEXT_MODEL_DIR = resolve_path("models/burnout_text_classifier_ft", "burnout_text_classifier_ft")
BEHAVIOR_MODEL_PATH = resolve_path("models/behavior_model/behavior_model_synthetic_labels.joblib", "Data/model_artifacts/behavior_model_synthetic_labels.joblib")
BURNOUT_PIPELINE_PATH = resolve_path("models/burnout_pipeline/pipeline_with_preproc.pkl", "saved_models_binary_high_v2_all/pipeline_with_preproc.pkl")
BURNOUT_THRESHOLD_PATH = resolve_path("models/burnout_pipeline/decision_threshold.pkl", "saved_models_binary_high_v2_all/decision_threshold.pkl")

app = FastAPI(title="MindSense ResearchBurnout API", version="1.0.0")

# Global model references
text_tokenizer = None
text_model = None
behavior_model = None
behavior_meta = {}
burnout_pipeline = None
burnout_threshold = 0.5


# ---------------------------------------------------------------------------
# Startup & Model Loading
# ---------------------------------------------------------------------------
@app.on_event("startup")
def startup():
    global text_tokenizer, text_model, behavior_model, behavior_meta, burnout_pipeline, burnout_threshold

    print("\n[MindSense Burnout] Initializing models and storage...")

    # 1. Behavior Model (Joblib)
    try:
        import joblib
        if BEHAVIOR_MODEL_PATH and os.path.exists(BEHAVIOR_MODEL_PATH):
            bundle = joblib.load(BEHAVIOR_MODEL_PATH)
            behavior_model = bundle.get("model", bundle) if isinstance(bundle, dict) else bundle
            behavior_meta = bundle.get("meta", {}) if isinstance(bundle, dict) else {}
            print(f"✔️ Behavior Model loaded successfully from: {BEHAVIOR_MODEL_PATH}")
        else:
            print(f"⚠️ Behavior Model path not found: {BEHAVIOR_MODEL_PATH}")
    except Exception as e:
        print(f"❌ Error loading behavior model: {e}")

    # 2. Burnout Pipeline (LightGBM Pipeline)
    try:
        import joblib
        if BURNOUT_PIPELINE_PATH and os.path.exists(BURNOUT_PIPELINE_PATH):
            burnout_pipeline = joblib.load(BURNOUT_PIPELINE_PATH)
            if BURNOUT_THRESHOLD_PATH and os.path.exists(BURNOUT_THRESHOLD_PATH):
                burnout_threshold = float(joblib.load(BURNOUT_THRESHOLD_PATH))
            print(f"✔️ Burnout Pipeline loaded successfully from: {BURNOUT_PIPELINE_PATH} (threshold: {burnout_threshold})")
        else:
            print(f"⚠️ Burnout Pipeline path not found: {BURNOUT_PIPELINE_PATH}")
    except Exception as e:
        print(f"❌ Error loading burnout pipeline: {e}")

    # 3. Text NLP Model (Transformers)
    try:
        if TEXT_MODEL_DIR and os.path.exists(TEXT_MODEL_DIR):
            from transformers import AutoTokenizer, AutoModelForSequenceClassification
            text_tokenizer = AutoTokenizer.from_pretrained(TEXT_MODEL_DIR, local_files_only=True)
            text_model = AutoModelForSequenceClassification.from_pretrained(TEXT_MODEL_DIR, local_files_only=True)
            print(f"✔️ NLP Text Classifier loaded successfully from: {TEXT_MODEL_DIR}")
        else:
            print(f"⚠️ NLP Text model directory not found: {TEXT_MODEL_DIR}")
    except Exception as e:
        print(f"ℹ️ NLP Text Classifier could not be loaded ({e}). Text endpoints will use fallback sentiment scoring if needed.")


# ---------------------------------------------------------------------------
# Auth Helper
# ---------------------------------------------------------------------------
def get_current_patient_id(authorization: Optional[str] = Header(None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = authorization.split(" ", 1)[1]
    token_doc = None
    try:
        token_doc = db.get_document(f"auth_tokens/{token}")
    except Exception:
        # Fallback to local SQLite if offline
        from . import database
        database.init_db()
        conn = database.get_connection()
        row = conn.execute("SELECT patient_id FROM auth_tokens WHERE token = ?", (token,)).fetchone()
        conn.close()
        if row:
            return str(row["patient_id"])

    if token_doc is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return str(token_doc["patient_id"])


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


class BurnoutMetricRequest(BaseModel):
    heart_rate: float = Field(..., description="Resting or current heart rate (BPM)")
    sleep_hours: float = Field(..., description="Hours of sleep last night")
    work_hours: float = Field(8.0, description="Hours spent working or studying")
    study_hours: Optional[float] = None
    stress_level: int = Field(5, ge=1, le=10, description="Self-reported stress level from 1 to 10")
    screen_time: float = Field(6.0, description="Screen time in hours")
    exercise_hours: float = Field(1.0, description="Exercise or physical activity in hours")
    sleep_quality: int = Field(3, ge=1, le=5, description="Sleep quality rating from 1 to 5")
    academic_stressors: Optional[int] = 0
    mental_health_score: Optional[int] = None
    journal_text: Optional[str] = Field(None, description="Optional reflective journal entry written by student")


class PredictResponse(BaseModel):
    overall_burnout_risk: str
    burnout_probability: float
    risk_level: str
    behavior_risk_score: Optional[float] = None
    text_sentiment_risk: Optional[float] = None
    key_contributing_factors: List[str]
    recommendations: List[str]
    metrics_summary: Dict[str, Any]


class TextRequest(BaseModel):
    user_id: Optional[str] = "student"
    text: str


class BehaviorRequest(BaseModel):
    user_id: Optional[str] = "student"
    features: Dict[str, Any]


class BurnoutRequest(BaseModel):
    user_id: Optional[str] = "student"
    features: Dict[str, Any]


# ---------------------------------------------------------------------------
# Auth Endpoints
# ---------------------------------------------------------------------------
@app.post("/api/patients/signup", response_model=AuthResponse)
def signup(req: SignupRequest):
    try:
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
    except HTTPException:
        raise
    except Exception as e:
        # SQLite offline fallback
        from . import database
        database.init_db()
        conn = database.get_connection()
        row = conn.execute("SELECT id FROM patients WHERE email = ?", (req.email,)).fetchone()
        if row:
            conn.close()
            raise HTTPException(status_code=400, detail="An account with this email already exists")

        pw_hash, salt = auth_utils.hash_password(req.password)
        member_since = datetime.date.today().isoformat()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO patients (name, email, password_hash, salt, member_since) VALUES (?, ?, ?, ?, ?)",
            (req.name, req.email, pw_hash, salt, member_since),
        )
        patient_id = str(cur.lastrowid)
        token = auth_utils.generate_token()
        cur.execute("INSERT INTO auth_tokens (token, patient_id) VALUES (?, ?)", (token, patient_id))
        conn.commit()
        conn.close()

        return AuthResponse(token=token, patient_id=patient_id, name=req.name, member_since=member_since)


@app.post("/api/patients/login", response_model=AuthResponse)
def login(req: LoginRequest):
    try:
        matches = db.query_collection("patients", field="email", value=req.email, limit=1)
        if not matches:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        patient = matches[0]
        if not auth_utils.verify_password(req.password, patient["salt"], patient["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        token = auth_utils.generate_token()
        db.create_document("auth_tokens", {"patient_id": patient["id"]}, doc_id=token)

        return AuthResponse(
            token=token,
            patient_id=patient["id"],
            name=patient.get("name", "Student"),
            member_since=patient.get("member_since", datetime.date.today().isoformat()),
        )
    except HTTPException:
        raise
    except Exception:
        # SQLite offline fallback
        from . import database
        database.init_db()
        conn = database.get_connection()
        row = conn.execute("SELECT * FROM patients WHERE email = ?", (req.email,)).fetchone()
        if not row:
            conn.close()
            raise HTTPException(status_code=401, detail="Invalid email or password")

        if not auth_utils.verify_password(req.password, row["salt"], row["password_hash"]):
            conn.close()
            raise HTTPException(status_code=401, detail="Invalid email or password")

        token = auth_utils.generate_token()
        conn.execute("INSERT OR REPLACE INTO auth_tokens (token, patient_id) VALUES (?, ?)", (token, row["id"]))
        conn.commit()
        conn.close()

        return AuthResponse(
            token=token,
            patient_id=str(row["id"]),
            name=row["name"],
            member_since=row["member_since"],
        )


# ---------------------------------------------------------------------------
# Daily Burnout Check-in Metrics Storage
# ---------------------------------------------------------------------------
@app.post("/api/health-metrics")
@app.post("/api/burnout-metrics")
def save_burnout_metric(req: BurnoutMetricRequest, authorization: Optional[str] = Header(None)):
    patient_id = get_current_patient_id(authorization)
    work_hrs = req.study_hours if req.study_hours is not None else req.work_hours

    data = {
        "date": datetime.date.today().isoformat(),
        "created_at": datetime.datetime.utcnow().isoformat(),
        "heart_rate": req.heart_rate,
        "sleep_hours": req.sleep_hours,
        "work_hours": work_hrs,
        "stress_level": req.stress_level,
        "screen_time": req.screen_time,
        "exercise_hours": req.exercise_hours,
        "sleep_quality": req.sleep_quality,
        "academic_stressors": req.academic_stressors or 0,
        "mental_health_score": req.mental_health_score or req.stress_level,
        "journal_text": req.journal_text or "",
    }

    try:
        db.create_document("health_metrics", data, parent=f"patients/{patient_id}")
    except Exception:
        from . import database
        database.init_db()
        conn = database.get_connection()
        conn.execute(
            """INSERT INTO burnout_metrics
               (patient_id, date, heart_rate, sleep_hours, work_hours, stress_level, screen_time, exercise_hours, sleep_quality, journal_text)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                int(patient_id) if patient_id.isdigit() else 1,
                data["date"],
                req.heart_rate,
                req.sleep_hours,
                work_hrs,
                req.stress_level,
                req.screen_time,
                req.exercise_hours,
                req.sleep_quality,
                req.journal_text or "",
            ),
        )
        conn.commit()
        conn.close()

    return {"status": "saved", "message": "Burnout check-in recorded successfully"}


@app.get("/api/health-metrics")
@app.get("/api/burnout-metrics")
def get_burnout_metrics(authorization: Optional[str] = Header(None)):
    patient_id = get_current_patient_id(authorization)
    try:
        rows = db.query_collection("health_metrics", parent=f"patients/{patient_id}", order_by="date")
        return {"metrics": rows}
    except Exception:
        from . import database
        database.init_db()
        conn = database.get_connection()
        p_id = int(patient_id) if patient_id.isdigit() else 1
        rows = conn.execute("SELECT * FROM burnout_metrics WHERE patient_id = ? ORDER BY date ASC", (p_id,)).fetchall()
        conn.close()
        return {"metrics": [dict(r) for r in rows]}


# ---------------------------------------------------------------------------
# Prediction Helpers
# ---------------------------------------------------------------------------
def run_behavior_inference(features: dict) -> float:
    """Returns probability of High Burnout (0.0 to 1.0) using behavior model or heuristic."""
    if behavior_model is not None:
        try:
            df = pd.DataFrame([features])
            if hasattr(behavior_model, "predict_proba"):
                probs = behavior_model.predict_proba(df)
                return float(probs[0][1] if probs.shape[1] > 1 else probs[0][0])
            pred = behavior_model.predict(df)
            return float(pred[0])
        except Exception as e:
            print(f"Behavior model inference fallback: {e}")

    # Robust evidence-based heuristic fallback if model artifact requires specific schema
    stress = float(features.get("Stress_Level", features.get("stress_level", 5)))
    sleep = float(features.get("Sleep_Hours", features.get("sleep_hours", 7)))
    work = float(features.get("Work_Hours", features.get("work_hours", 8)))
    screen = float(features.get("Screen_Time", features.get("screen_time", 6)))

    # Compute risk score (0 to 1)
    risk = (stress / 10.0) * 0.45 + max(0.0, (8.0 - sleep) / 8.0) * 0.25 + min(1.0, work / 12.0) * 0.20 + min(1.0, screen / 14.0) * 0.10
    return float(np.clip(risk, 0.05, 0.95))


def run_text_inference(text: str) -> Dict[str, Any]:
    """Returns classification and probability from fine-tuned transformer or lexical analyzer."""
    if not text or not text.strip():
        return {"prediction_label": 0, "probability": 0.0, "analyzed": False}

    if text_model is not None and text_tokenizer is not None:
        try:
            import torch
            inputs = text_tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
            outputs = text_model(**inputs)
            probs = torch.softmax(outputs.logits, dim=-1).detach().numpy()[0]
            label = int(probs.argmax())
            prob_high = float(probs[1]) if len(probs) > 1 else float(probs[0])
            return {
                "prediction_label": label,
                "probability": prob_high,
                "probabilities": probs.tolist(),
                "analyzed": True
            }
        except Exception as e:
            print(f"Transformers inference error: {e}")

    # Fallback sentiment indicator for text reflections
    burnout_keywords = [
        "exhausted", "drained", "overwhelmed", "hopeless", "can't focus", "tired",
        "giving up", "burnout", "burned out", "anxious", "insomnia", "stress",
        "pressure", "depressed", "headache", "panic", "no energy"
    ]
    positive_keywords = ["calm", "relaxed", "good", "happy", "accomplished", "energetic", "peaceful", "balanced"]
    text_lower = text.lower()
    matches_neg = sum(1 for kw in burnout_keywords if kw in text_lower)
    matches_pos = sum(1 for kw in positive_keywords if kw in text_lower)

    prob = min(0.95, max(0.05, (matches_neg * 0.25) - (matches_pos * 0.15) + 0.3))
    label = 1 if prob >= 0.5 else 0
    return {"prediction_label": label, "probability": prob, "probabilities": [1.0 - prob, prob], "analyzed": True}


# ---------------------------------------------------------------------------
# Comprehensive Burnout Prediction for the Mobile App
# ---------------------------------------------------------------------------
@app.get("/api/predict", response_model=PredictResponse)
def predict(authorization: Optional[str] = Header(None)):
    """Holistic burnout prediction for logged-in student based on recent check-in metrics and journal text."""
    patient_id = get_current_patient_id(authorization)

    # Fetch recent metrics
    records = []
    try:
        records = db.query_collection("health_metrics", parent=f"patients/{patient_id}", order_by="date")
    except Exception:
        from . import database
        database.init_db()
        conn = database.get_connection()
        p_id = int(patient_id) if patient_id.isdigit() else 1
        records = [dict(r) for r in conn.execute("SELECT * FROM burnout_metrics WHERE patient_id = ? ORDER BY date DESC", (p_id,)).fetchall()]
        conn.close()

    if not records:
        raise HTTPException(
            status_code=400,
            detail="No check-in entries logged yet. Please submit your daily check-in on the Check-in page first."
        )

    latest = records[-1]
    sleep_hours = float(latest.get("sleep_hours", 7.0))
    work_hours = float(latest.get("work_hours", latest.get("study_hours", 8.0)))
    stress_level = int(latest.get("stress_level", latest.get("mental_health_score", 5)))
    screen_time = float(latest.get("screen_time", 6.0))
    exercise_hours = float(latest.get("exercise_hours", 1.0))
    heart_rate = float(latest.get("heart_rate", 75.0))
    journal = latest.get("journal_text", "")

    # Feature dictionary formatted for behavior model
    behavior_features = {
        "Age": 22,
        "Sleep_Hours": sleep_hours,
        "Screen_Time": screen_time,
        "Stress_Level": stress_level,
        "Noise_Exposure": 5,
        "Social_Interaction": 4,
        "Work_Hours": work_hours,
        "Exercise_Hours": exercise_hours,
        "Caffeine_Intake": 2,
        "Multitasking_Habit": 1,
        "Anxiety_Score": stress_level,
        "Depression_Score": max(1, stress_level - 1),
        "Sensory_Sensitivity": 4,
        "Meditation_Habit": 0 if stress_level > 6 else 1,
        "Overthinking_Score": stress_level,
        "Irritability_Score": max(1, stress_level - 1),
        "Headache_Frequency": 3 if stress_level > 6 else 1,
        "Sleep_Quality": latest.get("sleep_quality", 3),
        "Tech_Usage_Hours": screen_time,
        "Overstimulated": 1 if screen_time > 8 or stress_level > 7 else 0,
        "Heart_Rate": heart_rate,
    }

    # 1. Behavior model prediction
    prob_behavior = run_behavior_inference(behavior_features)

    # 2. Text model prediction
    text_res = run_text_inference(journal)
    prob_text = text_res.get("probability", prob_behavior) if text_res.get("analyzed") else None

    # 3. Overall combined probability
    if prob_text is not None:
        combined_prob = 0.65 * prob_behavior + 0.35 * prob_text
    else:
        combined_prob = prob_behavior

    combined_prob = float(np.clip(combined_prob, 0.02, 0.98))

    # Determine risk category
    if combined_prob >= 0.65:
        risk_label = "High Burnout Risk"
        overall_risk = "High"
    elif combined_prob >= 0.40:
        risk_label = "Moderate Risk"
        overall_risk = "Moderate"
    else:
        risk_label = "Low Risk"
        overall_risk = "Low"

    # Identify contributing factors
    factors = []
    recs = []

    if sleep_hours < 6.0:
        factors.append(f"Insufficient sleep ({sleep_hours} hrs/day)")
        recs.append("Prioritize 7-8 hours of sleep tonight with a consistent bedtime routine.")
    if work_hours > 9.0:
        factors.append(f"Excessive work/study workload ({work_hours} hrs/day)")
        recs.append("Schedule structured study breaks using the Pomodoro technique (25 min study, 5 min break).")
    if stress_level >= 7:
        factors.append(f"High perceived stress rating ({stress_level}/10)")
        recs.append("Practice 10 minutes of box breathing or guided meditation to down-regulate nervous system.")
    if screen_time >= 8.0:
        factors.append(f"Elevated screen time ({screen_time} hrs)")
        recs.append("Implement screen-free windows 1 hour before sleeping to promote melatonin production.")
    if exercise_hours < 0.5:
        factors.append("Low physical activity (< 30 min/day)")
        recs.append("Take a 20-minute outdoor walk to relieve cortisol buildup.")
    if journal and text_res.get("prediction_label") == 1:
        factors.append("Reflective journal text exhibits notable emotional exhaustion cues")
        recs.append("Speak with a counselor or trusted mentor about workload overwhelm.")

    if not factors:
        factors.append("Healthy lifestyle balance maintained")
        recs.append("Keep up your balanced routine and healthy sleep patterns!")

    return PredictResponse(
        overall_burnout_risk=risk_label,
        burnout_probability=round(combined_prob, 3),
        risk_level=overall_risk,
        behavior_risk_score=round(prob_behavior, 3),
        text_sentiment_risk=round(prob_text, 3) if prob_text is not None else None,
        key_contributing_factors=factors,
        recommendations=recs,
        metrics_summary={
            "sleep_hours": sleep_hours,
            "work_hours": work_hours,
            "stress_level": stress_level,
            "screen_time": screen_time,
            "heart_rate": heart_rate,
            "date": latest.get("date", datetime.date.today().isoformat()),
        }
    )


# ---------------------------------------------------------------------------
# Standalone Model Endpoints (Compatible with existing research scripts)
# ---------------------------------------------------------------------------
@app.post("/predict/text")
@app.post("/api/predict/text")
def predict_text(req: TextRequest):
    result = run_text_inference(req.text)
    return {
        "user_id": req.user_id,
        "input_text": req.text,
        "prediction_label": result["prediction_label"],
        "probabilities": result.get("probabilities", [1.0 - result["probability"], result["probability"]]),
        "probability_high_burnout": result["probability"],
        "created_at": datetime.datetime.utcnow().isoformat(),
    }


@app.post("/predict/behavior")
@app.post("/api/predict/behavior")
def predict_behavior(req: BehaviorRequest):
    prob = run_behavior_inference(req.features)
    pred = 1 if prob >= 0.5 else 0
    return {
        "user_id": req.user_id,
        "features": req.features,
        "prediction": pred,
        "probability_high_burnout": round(prob, 4),
        "metadata": behavior_meta,
        "created_at": datetime.datetime.utcnow().isoformat(),
    }


@app.post("/predict/burnout")
@app.post("/api/predict/burnout")
def predict_burnout(req: BurnoutRequest):
    if burnout_pipeline is None:
        # Fallback to behavior inference if questionnaire pipeline is not loaded
        prob = run_behavior_inference(req.features)
        pred = 1 if prob >= burnout_threshold else 0
    else:
        df = pd.DataFrame([req.features])
        prob = float(burnout_pipeline.predict_proba(df)[:, 1][0])
        pred = int(prob >= burnout_threshold)

    return {
        "user_id": req.user_id,
        "features": req.features,
        "prediction": pred,
        "probability": round(prob, 4),
        "threshold_used": burnout_threshold,
        "created_at": datetime.datetime.utcnow().isoformat(),
    }


# ---------------------------------------------------------------------------
# Status and Diagnostics
# ---------------------------------------------------------------------------
@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "MindSense ResearchBurnout API",
        "text_model_loaded": text_model is not None,
        "behavior_model_loaded": behavior_model is not None,
        "burnout_pipeline_loaded": burnout_pipeline is not None,
        "burnout_threshold": burnout_threshold,
    }


@app.get("/debug/status")
def debug_status():
    return {
        "text_model_loaded": text_model is not None,
        "behavior_model_loaded": behavior_model is not None,
        "burnout_pipeline_loaded": burnout_pipeline is not None,
        "burnout_threshold": burnout_threshold,
        "behavior_metadata": behavior_meta,
    }


@app.get("/")
def root():
    return {
        "message": "MindSense ResearchBurnout API Running",
        "documentation": "/docs",
        "endpoints": ["/api/patients/signup", "/api/patients/login", "/api/health-metrics", "/api/predict", "/api/predict/text", "/api/predict/behavior", "/api/predict/burnout"]
    }
