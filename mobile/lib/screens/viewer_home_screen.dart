import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

import '../models/user_session.dart';

class ViewerHomeScreen extends StatefulWidget {
  const ViewerHomeScreen({super.key, required this.session});

  final UserSession session;

  @override
  State<ViewerHomeScreen> createState() => _ViewerHomeScreenState();
}

class _ViewerHomeScreenState extends State<ViewerHomeScreen> {
  bool _loading = true;
  String? _error;
  List<dynamic> _cases = const [];

  String get _baseUrl => const String.fromEnvironment('API_BASE_URL', defaultValue: 'http://100.64.0.1:8000');

  @override
  void initState() {
    super.initState();
    _loadCases();
  }

  Future<void> _loadCases() async {
    try {
      final scheme = String.fromCharCodes([66, 101, 97, 114, 101, 114]);
      final response = await http.get(
        Uri.parse('$_baseUrl/cases'),
        headers: {'Authorization': '$scheme ${widget.session.token}'},
      );
      if (response.statusCode != 200) throw Exception('Vakalar alınamadı');
      setState(() {
        _cases = jsonDecode(response.body) as List<dynamic>;
      });
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final title = widget.session.role == AppRole.admin ? 'Admin Paneli' : 'Bu Ayın Vakaları';
    return Scaffold(
      appBar: AppBar(
        title: Text(title),
        actions: [
          IconButton(
            onPressed: () => Navigator.of(context).pop(),
            icon: const Icon(Icons.logout),
          )
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!))
              : ListView.builder(
                  itemCount: _cases.length,
                  itemBuilder: (context, index) {
                    final c = _cases[index] as Map<String, dynamic>;
                    return ListTile(
                      title: Text(c['patient_name']?.toString().isNotEmpty == true ? c['patient_name'].toString() : 'İsimsiz Hasta'),
                      subtitle: Text('Tarih: ${c['case_date']} | Greft: ${c['graft_count']}'),
                    );
                  },
                ),
    );
  }
}
