import 'package:shared_preferences/shared_preferences.dart';

/// Stores the logged-in patient's token and basic info on the device,
/// so they don't have to log in again every time they open the app.
class AuthStorage {
  static const _tokenKey = 'auth_token';
  static const _patientIdKey = 'patient_id';
  static const _nameKey = 'patient_name';
  static const _memberSinceKey = 'member_since';

  static Future<void> saveSession({
    required String token,
    required String patientId,
    required String name,
    required String memberSince,
  }) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_tokenKey, token);
    await prefs.setString(_patientIdKey, patientId);
    await prefs.setString(_nameKey, name);
    await prefs.setString(_memberSinceKey, memberSince);
  }

  static Future<String?> getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_tokenKey);
  }

  static Future<String?> getName() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_nameKey);
  }

  static Future<String?> getMemberSince() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_memberSinceKey);
  }

  static Future<bool> isLoggedIn() async {
    final token = await getToken();
    return token != null && token.isNotEmpty;
  }

  static Future<void> clearSession() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.clear();
  }
}
