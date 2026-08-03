import 'dart:convert';
import 'package:http/http.dart' as http;
import 'auth_storage.dart';

/// All calls to your FastAPI backend go through this one class.
///
/// IMPORTANT: change [baseUrl] to match how you're running the backend.
///   - Android emulator talking to a server on your same laptop -> http://10.0.2.2:8000
///   - Real phone on the same WiFi as your laptop               -> http://<your-laptop-LAN-IP>:8000
///     (find it with `ipconfig` on Windows, look for "IPv4 Address")
///   - iOS simulator on the same laptop                          -> http://127.0.0.1:8000
class ApiService {
  static const String baseUrl = 'http://10.0.2.2:8000';// <-- CHANGE THIS, see note above

  static Future<Map<String, dynamic>> signup({
    required String name,
    required String email,
    required String password,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/patients/signup'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'name': name, 'email': email, 'password': password}),
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception(_extractError(response));
    }
  }

  static Future<Map<String, dynamic>> login({
    required String email,
    required String password,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/patients/login'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email, 'password': password}),
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception(_extractError(response));
    }
  }

  static Future<void> saveHealthMetric({
    required double heartRate,
    required double sleepHours,
    required double studyHours,
    required int academicStressors,
    required int mentalHealthScore,
  }) async {
    final token = await AuthStorage.getToken();
    if (token == null) throw Exception('Not logged in');

    final response = await http.post(
      Uri.parse('$baseUrl/api/health-metrics'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
      body: jsonEncode({
        'heart_rate': heartRate,
        'sleep_hours': sleepHours,
        'study_hours': studyHours,
        'academic_stressors': academicStressors,
        'mental_health_score': mentalHealthScore,
      }),
    );

    if (response.statusCode != 200) {
      throw Exception(_extractError(response));
    }
  }

  static Future<Map<String, dynamic>> getPrediction() async {
    final token = await AuthStorage.getToken();
    if (token == null) throw Exception('Not logged in');

    final response = await http.get(
      Uri.parse('$baseUrl/api/predict'),
      headers: {'Authorization': 'Bearer $token'},
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception(_extractError(response));
    }
  }

  static String _extractError(http.Response response) {
    try {
      final body = jsonDecode(response.body);
      if (body is Map && body.containsKey('detail')) {
        return body['detail'].toString();
      }
    } catch (_) {}
    return 'Request failed (${response.statusCode})';
  }
}
