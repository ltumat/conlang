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

  /// Search words with pagination. Returns [{words}, total, offset, limit].
  Future<Map<String, dynamic>> searchWords(
    String language, {
    String query = '',
    int limit = 10,
    int offset = 0,
  }) async {
    final params = {'language': language};
    if (query.isNotEmpty) params['q'] = query;
    params['limit'] = limit.toString();
    params['offset'] = offset.toString();

    final uri = Uri.parse('$baseUrl/words/').replace(queryParameters: params);
    final response = await http.get(uri);
    if (response.statusCode == 200) {
      return json.decode(response.body) as Map<String, dynamic>;
    } else {
      throw Exception('Failed to search words');
    }
  }

  /// Fetch a single word by its exact name.
  Future<Map<String, dynamic>> fetchWord(
    String word,
    String language,
  ) async {
    final uri = Uri.parse('$baseUrl/words/${Uri.encodeComponent(word)}')
        .replace(queryParameters: {'language': language});
    final response = await http.get(uri);
    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      return Map<String, dynamic>.from(data['word'] as Map);
    } else {
      throw Exception('Word not found');
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
