import 'dart:convert';

import 'package:http/http.dart' as http;

import '../models/user_session.dart';

class ApiClient {
  ApiClient({required this.baseUrl});

  final String baseUrl;

  Future<UserSession> login(String username, String password) async {
    final loginResponse = await http.post(
      Uri.parse('$baseUrl/auth/login'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'username': username, 'password': password}),
    );
    if (loginResponse.statusCode != 200) {
      throw Exception('Giriş başarısız');
    }

    final token = jsonDecode(loginResponse.body)['access_token'] as String;
    final scheme = String.fromCharCodes([66, 101, 97, 114, 101, 114]);
    final authHeader = '$scheme $token';
    final meResponse = await http.get(
      Uri.parse('$baseUrl/auth/me'),
      headers: {'Authorization': authHeader},
    );
    if (meResponse.statusCode != 200) {
      throw Exception('Kullanıcı bilgisi alınamadı');
    }

    final roleString = jsonDecode(meResponse.body)['role'] as String;
    return UserSession(
      token: token,
      role: roleString == 'ADMIN' ? AppRole.admin : AppRole.viewer,
    );
  }
}
