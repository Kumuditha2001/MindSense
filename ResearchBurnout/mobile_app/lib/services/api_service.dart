import 'dart:convert';
import 'package:http/http.dart' as http;
import 'auth_storage.dart';

/// All API calls for MindSense — ResearchBurnout.
///
/// Change [baseUrl] to match how you're running the backend:
///   - Android emulator on same machine: http://10.0.2.2:8000
///   - Physical phone on same Wi-Fi:    http://<your-laptop-ip>:8000
///   - Web / Windows desktop / iOS:     http://127.0.0.1:8000
class ApiService {
  static const String baseUrl = 'http://10.0.2.2:8000'; // Change if testing on desktop/phone

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

  static Future<void> saveBurnoutMetric({
    required double heartRate,
    required double sleepHours,
    required double workHours,
    required int stressLevel,
    required double screenTime,
    required double exerciseHours,
    required int sleepQuality,
    String? journalText,
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
        'work_hours': workHours,
        'study_hours': workHours,
        'stress_level': stressLevel,
        'screen_time': screenTime,
        'exercise_hours': exerciseHours,
        'sleep_quality': sleepQuality,
        'journal_text': journalText ?? '',
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

  static Future<Map<String, dynamic>> analyzeJournalText(String text) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/predict/text'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'text': text}),
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
    return 'Server returned status ${response.statusCode}';
  }
}
