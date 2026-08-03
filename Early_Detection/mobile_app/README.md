# MindSense — Flutter App

## Screens included
- Login
- Signup
- Home / Insights (calls the FastAPI /api/predict endpoint)
- Daily Check-in / data insert page (calls /api/health-metrics)
- Schedule, Academic, Behavior — placeholders ("coming soon"), to be built next

## Before running
1. Open `lib/services/api_service.dart`
2. Change `baseUrl` to match how you're running the backend:
   - Android emulator + backend on the same laptop -> `http://10.0.2.2:8000` (already set)
   - Real Android phone on the same WiFi as your laptop -> `http://<your-laptop-LAN-IP>:8000`
     (find your IP with `ipconfig` on Windows, look for "IPv4 Address")

## Run
```
flutter pub get
flutter run
```
Make sure the backend (`uvicorn api.main:app --reload`) is running first.
