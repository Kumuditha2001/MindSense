import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../services/auth_storage.dart';
import 'login_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  String _name = '';
  String _memberSince = '';

  bool _isLoading = true;
  String? _errorMessage;
  Map<String, dynamic>? _prediction;

  @override
  void initState() {
    super.initState();
    _loadEverything();
  }

  Future<void> _loadEverything() async {
    final name = await AuthStorage.getName();
    final memberSince = await AuthStorage.getMemberSince();

    setState(() {
      _name = name ?? '';
      _memberSince = memberSince ?? '';
    });

    await _loadPrediction();
  }

  Future<void> _loadPrediction() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final result = await ApiService.getPrediction();
      setState(() {
        _prediction = result;
      });
    } catch (e) {
      setState(() {
        _errorMessage = e.toString().replaceFirst('Exception: ', '');
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _logout() async {
    await AuthStorage.clearSession();
    if (!mounted) return;
    Navigator.of(context).pushAndRemoveUntil(
      MaterialPageRoute(builder: (_) => const LoginScreen()),
      (route) => false,
    );
  }

  String _greeting() {
    final hour = DateTime.now().hour;
    if (hour < 12) return 'Good Morning';
    if (hour < 18) return 'Good Afternoon';
    return 'Good Night';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: _loadPrediction,
          child: SingleChildScrollView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.end,
                  children: [
                    TextButton.icon(
                      onPressed: _logout,
                      icon: const Icon(Icons.logout, color: Colors.white),
                      label: const Text('Logout', style: TextStyle(color: Colors.white)),
                      style: TextButton.styleFrom(backgroundColor: Colors.redAccent),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Container(
                  padding: const EdgeInsets.all(20),
                  decoration: BoxDecoration(
                    color: Colors.deepPurple,
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(_greeting(), style: const TextStyle(color: Colors.white, fontSize: 18)),
                      Text(_name,
                          style: const TextStyle(
                              color: Colors.white, fontSize: 28, fontWeight: FontWeight.bold)),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
                Row(
                  children: [
                    Expanded(
                      child: _InfoCard(title: 'Member Since', value: _memberSince),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: _InfoCard(title: 'Sessions Pending', value: '0'),
                    ),
                  ],
                ),
                const SizedBox(height: 24),
                const Text('Your Mental Health Insights',
                    style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
                const SizedBox(height: 8),
                const Text('Predicted 3 months ahead, based on your recent check-ins',
                    style: TextStyle(color: Colors.grey)),
                const SizedBox(height: 16),
                _buildInsightsBody(),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildInsightsBody() {
    if (_isLoading) {
      return const Center(child: Padding(
        padding: EdgeInsets.all(32),
        child: CircularProgressIndicator(),
      ));
    }

    if (_errorMessage != null) {
      return Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.orange.shade50,
          border: Border.all(color: Colors.orange),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('No prediction yet', style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Text(_errorMessage!),
            const SizedBox(height: 8),
            const Text(
              'Log your daily check-in on the Quizzes/Status page — once you have 30 days of entries, your 3-month forecast will appear here.',
              style: TextStyle(color: Colors.grey),
            ),
          ],
        ),
      );
    }

    final today = DateTime.now();
    final day30 = today.add(const Duration(days: 30));
    final day60 = today.add(const Duration(days: 60));
    final day90 = today.add(const Duration(days: 90));

    return SizedBox(
      height: 180,
      child: ListView(
        scrollDirection: Axis.horizontal,
        children: [
          _PredictionCard(
            label: 'In 30 days (${_formatDate(day30)})',
            category: _prediction?['day_30_category'] ?? '-',
            color: Colors.orange.shade100,
          ),
          _PredictionCard(
            label: 'In 60 days (${_formatDate(day60)})',
            category: _prediction?['day_60_category'] ?? '-',
            color: Colors.blue.shade100,
          ),
          _PredictionCard(
            label: 'In 90 days (${_formatDate(day90)})',
            category: _prediction?['day_90_category'] ?? '-',
            color: Colors.purple.shade100,
          ),
        ],
      ),
    );
  }

  String _formatDate(DateTime d) => '${d.day}/${d.month}/${d.year}';
}

class _InfoCard extends StatelessWidget {
  final String title;
  final String value;

  const _InfoCard({required this.title, required this.value});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        border: Border.all(color: Colors.grey.shade300),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: const TextStyle(fontWeight: FontWeight.bold)),
          const SizedBox(height: 24),
          Text(value, style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }
}

class _PredictionCard extends StatelessWidget {
  final String label;
  final String category;
  final Color color;

  const _PredictionCard({required this.label, required this.category, required this.color});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 220,
      margin: const EdgeInsets.only(right: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: color,
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: const TextStyle(fontWeight: FontWeight.bold)),
          const Spacer(),
          const Text('Predicted Mental State', style: TextStyle(color: Colors.black54)),
          Text(category,
              style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Colors.deepPurple)),
        ],
      ),
    );
  }
}
