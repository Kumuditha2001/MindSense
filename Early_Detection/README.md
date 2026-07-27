# MindSense — Early_Detection

Time-series forecasting component for early identification of student mental health
(Naive / ARIMA / LSTM, 90-day / 3-month forecast horizon).

## Setup
```
python -m venv venv
venv\Scripts\activate          (Windows)
pip install -r requirements.txt
```
Then open this folder in VS Code and select the `venv` interpreter as your Jupyter kernel.

## Run order
1. `notebooks/01_data_preprocessing_eda.ipynb`
   - Loads `data/raw/student_data.csv`
   - Cleans it, explores it, encodes Stress_Level / Mental_Health_Status as ordered scores
   - Saves `data/processed/student_data_clean.csv`
2. `notebooks/02_model_training.ipynb`
   - Loads `data/processed/student_data_clean.csv`
   - Builds per-student train/test split (last 90 days held out)
   - Trains Naive, ARIMA, and LSTM forecasters
   - Compares RMSE/MAE across models and students
   - Saves `notebooks/model_comparison_results.csv`

Run each notebook top to bottom ("Run All").
