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
                      icon: const Icon(Icons.logout, color: Colors.white, size: 18),
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
                      Text(_greeting(), style: const TextStyle(color: Colors.white70, fontSize: 16)),
                      const SizedBox(height: 4),
                      Text(
                        _name.isEmpty ? 'Student' : _name,
                        style: const TextStyle(color: Colors.white, fontSize: 26, fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 8),
                      const Text(
                        'MindSense • Burnout Early Warning System',
                        style: TextStyle(color: Colors.white60, fontSize: 13),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
                Row(
                  children: [
                    Expanded(
                      child: _InfoCard(title: 'Member Since', value: _memberSince.isEmpty ? '-' : _memberSince),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: _InfoCard(
                        title: 'Burnout Risk',
                        value: _prediction?['overall_burnout_risk'] ?? 'Pending',
                        highlight: _prediction?['overall_burnout_risk'] == 'High Burnout Risk',
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 24),
                const Text(
                  'Your Burnout Insights',
                  style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 4),
                const Text(
                  'Synthesized from behavioral telemetry and reflective NLP analysis',
                  style: TextStyle(color: Colors.grey),
                ),
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
      return const Center(
        child: Padding(
          padding: EdgeInsets.all(32),
          child: CircularProgressIndicator(),
        ),
      );
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
              'Log your daily check-in on the Check-in page to generate your real-time burnout analysis.',
              style: TextStyle(color: Colors.grey),
            ),
          ],
        ),
      );
    }

    final riskLabel = _prediction?['overall_burnout_risk'] ?? 'Low Risk';
    final prob = ((_prediction?['burnout_probability'] ?? 0.0) as num).toDouble();
    final factors = List<String>.from(_prediction?['key_contributing_factors'] ?? []);
    final recommendations = List<String>.from(_prediction?['recommendations'] ?? []);

    Color riskColor;
    if (prob >= 0.65) {
      riskColor = Colors.red.shade700;
    } else if (prob >= 0.40) {
      riskColor = Colors.orange.shade800;
    } else {
      riskColor = Colors.green.shade700;
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Main Risk Status Card
        Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: riskColor.withAlpha(20),
            border: Border.all(color: riskColor.withAlpha(100)),
            borderRadius: BorderRadius.circular(16),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    riskLabel,
                    style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: riskColor),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(
                      color: riskColor,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Text(
                      '${(prob * 100).toStringAsFixed(1)}% Risk',
                      style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 13),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              ClipRRect(
                borderRadius: BorderRadius.circular(6),
                child: LinearProgressIndicator(
                  value: prob,
                  backgroundColor: Colors.grey.shade200,
                  valueColor: AlwaysStoppedAnimation<Color>(riskColor),
                  minHeight: 10,
                ),
              ),
              const SizedBox(height: 12),
              Text(
                prob >= 0.65
                    ? '⚠️ High risk of acute student burnout. Immediate recovery interventions recommended.'
                    : prob >= 0.40
                        ? '⚡ Moderate fatigue detected. Watch study workload and prioritize sleep.'
                        : '🌱 Excellent mental and behavioral balance. Maintain your current habits.',
                style: const TextStyle(fontSize: 13.5),
              ),
            ],
          ),
        ),
        const SizedBox(height: 20),

        // Contributing Factors
        const Text('Key Contributing Factors', style: TextStyle(fontSize: 17, fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        ...factors.map(
          (f) => Padding(
            padding: const EdgeInsets.symmetric(vertical: 4),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(Icons.arrow_right, color: riskColor),
                Expanded(child: Text(f, style: const TextStyle(fontSize: 14))),
              ],
            ),
          ),
        ),
        const SizedBox(height: 20),

        // Recommendations
        const Text('AI Recovery Recommendations', style: TextStyle(fontSize: 17, fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        ...recommendations.map(
          (r) => Container(
            margin: const EdgeInsets.only(bottom: 8),
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.purple.shade50,
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: Colors.purple.shade100),
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Icon(Icons.lightbulb_outline, color: Colors.deepPurple, size: 20),
                const SizedBox(width: 8),
                Expanded(child: Text(r, style: const TextStyle(fontSize: 13.5))),
              ],
            ),
          ),
        ),
      ],
    );
  }
}

class _InfoCard extends StatelessWidget {
  final String title;
  final String value;
  final bool highlight;

  const _InfoCard({required this.title, required this.value, this.highlight = false});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: highlight ? Colors.red.shade50 : Colors.white,
        border: Border.all(color: highlight ? Colors.red.shade300 : Colors.grey.shade300),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: const TextStyle(color: Colors.grey, fontSize: 13, fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          Text(
            value,
            style: TextStyle(
              fontSize: 17,
              fontWeight: FontWeight.bold,
              color: highlight ? Colors.red.shade800 : Colors.black87,
            ),
          ),
        ],
      ),
    );
  }
}
