# MindSense — ResearchBurnout Mobile App

Flutter mobile application for student burnout early detection, behavioral telemetry tracking, and NLP reflective journaling.

## Screens Included
- **Login / Signup**: Token-based authentication saved securely on-device with `shared_preferences`.
- **Home / Burnout Insights**: Displays comprehensive burnout risk status, probability gauge, top contributing factors, and AI recovery recommendations from `/api/predict`.
- **Reflective Journal**: Interactive screen where students write text reflections and receive instant NLP burnout and fatigue classification from the fine-tuned transformer.
- **Behavioral Indicators**: Educational and visual breakdown of the key behavioral pillars (sleep, work hours, sensory stimulation, movement).
- **Daily Check-in (Data Insert)**: Logs daily telemetry (heart rate, sleep hours, study/work hours, stress slider 1-10, screen time, exercise, sleep quality, and journal text) to `/api/health-metrics`.

## Before Running
1. Open `lib/services/api_service.dart`.
2. Ensure `baseUrl` matches your development environment:
   - Android Emulator: `http://10.0.2.2:8000` (default)
   - iOS Simulator / Windows Desktop / Web: `http://127.0.0.1:8000`
   - Physical Phone: `http://<your-laptop-LAN-IP>:8000` (run `ipconfig` on Windows to check)

## Setup & Run
```bash
flutter pub get
flutter run
```
Make sure the FastAPI backend (`uvicorn api.main:app --reload`) is running first.
