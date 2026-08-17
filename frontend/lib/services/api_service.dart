import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  // Override for a deployed API with:
  // flutter run --dart-define=API_BASE_URL=https://your-api.example.com
  // Use localhost for the iOS simulator and 10.0.2.2 for Android emulators.
  static const String baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://localhost:8000',
  );

  Future<Map<String, dynamic>> healthCheck() async {
    final response = await http.get(Uri.parse('$baseUrl/health'));
    if (response.statusCode == 200) {
      return json.decode(response.body);
    } else {
      throw Exception('API health check failed');
    }
  }

  Future<List<Map<String, dynamic>>> fetchLanguages() async {
    final response = await http.get(Uri.parse('$baseUrl/languages/'));
    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      return List<Map<String, dynamic>>.from(data['languages']);
    } else {
      throw Exception('Failed to load languages');
    }
  }

  Future<List<Map<String, dynamic>>> fetchWords(String language) async {
    final response = await http.get(
      Uri.parse('$baseUrl/words/?language=$language'),
    );
    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      return (data['words'] as List<dynamic>)
          .map((word) => Map<String, dynamic>.from(word as Map))
          .toList();
    } else {
      throw Exception('Failed to load words');
    }
  }
}
