# MindSense — Early_Detection

Time-series forecasting component for early identification of student mental health
(Naive / ARIMA / LSTM, 90-day / 3-month forecast horizon), plus a working backend
and Flutter mobile app.

## Folder structure
```
Early_Detection/
├── data/               raw + cleaned dataset
├── notebooks/          01 (EDA), 02 (model comparison), 03 (train final model)
├── models/             saved model_lstm_global.keras + scaler.save (put here after running notebook 3)
├── api/                FastAPI backend (auth, health metrics, predictions)
├── mobile_app/         Flutter app (Login, Signup, Home/Insights, Daily Check-in)
└── requirements.txt    Python dependencies
```

## Backend setup
```
python -m venv venv
venv\Scripts\activate          (Windows)
pip install -r requirements.txt
uvicorn api.main:app --reload
```
Test at http://127.0.0.1:8000/docs

Data storage: Google Firestore, accessed via plain REST calls (see `api/firestore_client.py`)
— no service account key needed, since the database is currently in Firestore's
"test mode" (open security rules). Project ID is set inside `firestore_client.py`.

**Before final submission:** test-mode rules expire ~30 days after the database
was created. If requests start failing with a permission error after that,
go to Firebase Console -> Firestore Database -> Rules and update them to allow
read/write (see the comment at the top of `firestore_client.py` for the exact rule).

## Mobile app setup
See `mobile_app/README.md`.

## Run order (if starting fresh)
1. `notebooks/01_data_preprocessing_eda.ipynb` → cleans data
2. `notebooks/02_model_training.ipynb` → compares Naive/ARIMA/LSTM
3. `notebooks/03_train_final_model.ipynb` → trains and saves the final deployable model
4. Move `model_lstm_global.keras` and `scaler.save` into `models/`
5. Start the backend (`uvicorn api.main:app --reload`)
6. Run the Flutter app (`flutter run`)
