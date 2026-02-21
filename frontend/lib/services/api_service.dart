import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  // Use localhost for iOS simulator
  // Use 10.0.2.2 for Android emulator
  static const String baseUrl = 'http://localhost:8000';

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
}
