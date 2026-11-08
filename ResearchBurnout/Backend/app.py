# ---------------------------------------------------------------
# app.py - Corrected with proper parent directory model paths
# ---------------------------------------------------------------

import os
import joblib
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import pandas as pd
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from pymongo import MongoClient
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")

try:
    client = MongoClient(MONGO_URL)
    db = client["HealthDB"]
except Exception as e:
    print("MongoDB failed:", e)
    client = None
    db = None

text_collection = db["text_predictions"]
behavior_collection = db["behavior_predictions"]
burnout_collection = db["burnout_predictions"]

# ---------------------------------------------------------------
# Correct Paths (models are one level above Backend/)
# ---------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))

TEXT_MODEL_DIR = os.path.join(PARENT_DIR, "burnout_text_classifier_ft")

BEHAVIOR_MODEL_PATH = os.path.join(PARENT_DIR, "Data", "model_artifacts", "behavior_model_synthetic_labels.joblib")
BEHAVIOR_METADATA_PATH = os.path.join(PARENT_DIR, "Data", "model_artifacts", "labeling_metadata.json")

BURNOUT_PIPELINE_PATH = os.path.join(PARENT_DIR, "saved_models_binary_high_v2_all", "pipeline_with_preproc.pkl")
BURNOUT_THRESHOLD_PATH = os.path.join(PARENT_DIR, "saved_models_binary_high_v2_all", "decision_threshold.pkl")

# ---------------------------------------------------------------
# Global model objects
# ---------------------------------------------------------------
text_tokenizer = None
text_model = None

behavior_model = None
behavior_meta = None

burnout_pipeline = None
burnout_threshold = None

# ---------------------------------------------------------------
# Load Text Model
# ---------------------------------------------------------------
def load_text_model():
    global text_model, text_tokenizer
    try:
        text_tokenizer = AutoTokenizer.from_pretrained(TEXT_MODEL_DIR)
        text_model = AutoModelForSequenceClassification.from_pretrained(TEXT_MODEL_DIR)
        return True
    except Exception as e:
        print(" ERROR loading text model:", e)
        return False

# ---------------------------------------------------------------
# Load Behavior Model
# ---------------------------------------------------------------
def load_behavior_model():
    global behavior_model, behavior_meta
    try:
        bundle = joblib.load(BEHAVIOR_MODEL_PATH)
        behavior_model = bundle["model"]
        behavior_meta = bundle.get("meta", {})
        return True
    except Exception as e:
        print(" ERROR loading behavior model:", e)
        return False

# ---------------------------------------------------------------
# Load Burnout2Classes Pipeline
# ---------------------------------------------------------------
def load_burnout_pipeline():
    global burnout_pipeline, burnout_threshold
    try:
        burnout_pipeline = joblib.load(BURNOUT_PIPELINE_PATH)
        if os.path.exists(BURNOUT_THRESHOLD_PATH):
            burnout_threshold = joblib.load(BURNOUT_THRESHOLD_PATH)
        else:
            burnout_threshold = 0.5
        return True
    except Exception as e:
        print(" ERROR loading burnout pipeline:", e)
        return False

# ---------------------------------------------------------------
# FastAPI App
# ---------------------------------------------------------------
app = FastAPI(title="AI Mental Health Prediction API")

@app.on_event("startup")
def startup_load_models():
    print("\n========== MODEL LOADING STARTED ==========")
    print("Loading NLP model:", load_text_model())
    print("Loading Behavior model:", load_behavior_model())
    print("Loading Burnout2 pipeline:", load_burnout_pipeline())
    print("===========================================\n")

# ---------------------------------------------------------------
# Request Schemas
# ---------------------------------------------------------------
class TextRequest(BaseModel):
    user_id: str
    text: str

class BehaviorRequest(BaseModel):
    user_id: str
    features: Dict[str, Any]

class BurnoutRequest(BaseModel):
    user_id: str
    features: Dict[str, Any]

# ---------------------------------------------------------------
# /predict/text
# ---------------------------------------------------------------
@app.post("/predict/text")
def predict_text(req: TextRequest):

    if text_model is None:
        raise HTTPException(500, "Text model is not loaded.")

    inputs = text_tokenizer(req.text, return_tensors="pt", truncation=True)
    outputs = text_model(**inputs)
    probs = torch.softmax(outputs.logits, dim=-1).detach().numpy()[0]

    result = {
        "user_id": req.user_id,
        "input_text": req.text,
        "prediction_label": int(probs.argmax()),
        "probabilities": probs.tolist(),
        "created_at": datetime.utcnow()
    }

    inserted = text_collection.insert_one(result)

    saved_doc = text_collection.find_one(
        {"_id": inserted.inserted_id}
    )

    saved_doc["_id"] = str(saved_doc["_id"])

    return {
        "message": "Saved successfully",
        "data": saved_doc
    }



# ---------------------------------------------------------------
# /predict/behavior
# ---------------------------------------------------------------
@app.post("/predict/behavior")
def predict_behavior(req: BehaviorRequest):

    if behavior_model is None:
        raise HTTPException(500, "Behavior model is not loaded.")

    df = pd.DataFrame([req.features])
    pred = behavior_model.predict(df)
    prob = None

    if hasattr(behavior_model, "predict_proba"):
        prob = float(behavior_model.predict_proba(df)[:, 1][0])

    result = {
        "user_id": req.user_id,
        "features": req.features,
        "prediction": int(pred[0]),
        "probability_high_burnout": prob,
        "metadata": behavior_meta,
        "created_at": datetime.utcnow()
    }

    inserted = behavior_collection.insert_one(result)

    saved_doc = behavior_collection.find_one(
        {"_id": inserted.inserted_id}
    )

    saved_doc["_id"] = str(saved_doc["_id"])

    return {
        "message": "Saved successfully",
        "data": saved_doc
    }




# ---------------------------------------------------------------
# /predict/burnout
# ---------------------------------------------------------------
@app.post("/predict/burnout")
def predict_burnout(req: BurnoutRequest):

    if burnout_pipeline is None:
        raise HTTPException(500, "Burnout model is not loaded.")

    df = pd.DataFrame([req.features])

    proba = float(burnout_pipeline.predict_proba(df)[:, 1][0])
    pred = int(proba >= burnout_threshold)

    result = {
        "user_id": req.user_id,
        "features": req.features,
        "prediction": pred,
        "probability": proba,
        "threshold_used": burnout_threshold,
        "created_at": datetime.utcnow()
    }

    inserted = burnout_collection.insert_one(result)

    saved_doc = burnout_collection.find_one(
        {"_id": inserted.inserted_id}
    )

    saved_doc["_id"] = str(saved_doc["_id"])

    return {
        "message": "Saved successfully",
        "data": saved_doc
    }





@app.get("/results/text/{user_id}")
def get_text_results(user_id: str):

    results = list(text_collection.find(
        {"user_id": user_id},
        {"_id": 0}
    ))

    return {"count": len(results), "results": results}


@app.get("/results/behavior/{user_id}")
def get_behavior_results(user_id: str):

    results = list(behavior_collection.find(
        {"user_id": user_id},
        {"_id": 0}
    ))

    return {"count": len(results), "results": results}


@app.get("/results/burnout/{user_id}")
def get_burnout_results(user_id: str):

    results = list(burnout_collection.find(
        {"user_id": user_id},
        {"_id": 0}
    ))

    return {"count": len(results), "results": results}

# ---------------------------------------------------------------
# Debug status
# ---------------------------------------------------------------
@app.get("/debug/status")
def debug_status():
    return {
        "text_model_loaded": text_model is not None,
        "behavior_model_loaded": behavior_model is not None,
        "burnout_pipeline_loaded": burnout_pipeline is not None,
        "burnout_threshold": burnout_threshold,
        "behavior_metadata": behavior_meta
    }

# ---------------------------------------------------------------
@app.get("/")
def home():
    return {"message": "AI Mental Health API Running!"}
