# MindSense — ResearchBurnout

Multi-modal burnout detection component for early identification of student burnout and mental exhaustion, combining:
1. **Behavioral Telemetry Model**: Random Forest / Ensemble model predicting burnout risk from lifestyle metrics (Sleep, Study/Work Hours, Stress, Screen Time, Activity, Heart Rate).
2. **Reflective Journal NLP Classifier**: Fine-tuned Transformer evaluating emotional fatigue and burnout cues in student reflection entries.
3. **Burnout Questionnaire Pipeline**: LightGBM pipeline assessing academic, psychological, and lifestyle dimensions.
4. **FastAPI Backend**: Secure authentication, metrics logging, and predictive endpoints.
5. **Flutter Mobile App**: Complete cross-platform client with daily check-in, real-time risk gauges, AI recovery advice, and reflective journal analysis.

## Folder structure
```
ResearchBurnout/
├── data/
│   ├── raw/                 Raw datasets (academic, reflective journals, mental health)
│   └── processed/           Cleaned dataset (data_with_burnout.csv)
├── notebooks/               01 (Academic/Behavior), 02 (Burnout binary classification), 03 (Burnout NLP)
├── models/
│   ├── behavior_model/      behavior_model_synthetic_labels.joblib + metadata
│   ├── burnout_pipeline/    pipeline_with_preproc.pkl + decision_threshold.pkl
│   └── burnout_text_classifier_ft/  Fine-tuned transformer text classifier (weights & tokenizer)
├── api/                     FastAPI backend (auth, metrics logging, predictions)
├── mobile_app/              Flutter app (Login, Signup, Home/Risk Insights, Journal, Behavior, Daily Check-in)
├── requirements.txt         Python dependencies
└── README.md
```

## Backend setup
```bash
python -m venv venv
venv\Scripts\activate          # (Windows)
# source venv/bin/activate     # (macOS/Linux)
pip install -r requirements.txt
uvicorn api.main:app --reload
```
Test the interactive API docs at http://127.0.0.1:8000/docs

Data storage: Google Firestore, accessed via REST calls (see `api/firestore_client.py`) with automatic offline SQLite fallback (`burnout.db`). Project ID: `mindsense-1f132`.

## Mobile app setup
See `mobile_app/README.md`.

```bash
cd mobile_app
flutter pub get
flutter run
```

## Run order (if training or modifying models)
1. `notebooks/01_academic_behavior_analysis.ipynb` → Analyzes behavior and generates `behavior_model_synthetic_labels.joblib`
2. `notebooks/02_burnout_binary_classification.ipynb` → Evaluates binary burnout classification and outputs `pipeline_with_preproc.pkl`
3. `notebooks/03_burnout_nlp_transformer.ipynb` → Fine-tunes transformer model on reflective journals and saves into `burnout_text_classifier_ft`
4. Start the backend (`uvicorn api.main:app --reload`)
5. Run the Flutter app (`flutter run`)

