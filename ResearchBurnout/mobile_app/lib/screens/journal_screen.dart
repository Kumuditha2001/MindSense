import 'package:flutter/material.dart';
import '../services/api_service.dart';

class JournalScreen extends StatefulWidget {
  const JournalScreen({super.key});

  @override
  State<JournalScreen> createState() => _JournalScreenState();
}

class _JournalScreenState extends State<JournalScreen> {
  final _textController = TextEditingController();
  bool _isAnalyzing = false;
  Map<String, dynamic>? _analysisResult;
  String? _error;

  Future<void> _analyze() async {
    final text = _textController.text.trim();
    if (text.isEmpty) {
      setState(() {
        _error = 'Please write a reflection or journal entry first.';
      });
      return;
    }

    setState(() {
      _isAnalyzing = true;
      _error = null;
    });

    try {
      final res = await ApiService.analyzeJournalText(text);
      setState(() {
        _analysisResult = res;
      });
    } catch (e) {
      setState(() {
        _error = e.toString().replaceFirst('Exception: ', '');
      });
    } finally {
      setState(() {
        _isAnalyzing = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Reflective Journal'),
        backgroundColor: Colors.deepPurple,
        foregroundColor: Colors.white,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text(
              'Express Your Thoughts & Feelings',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 6),
            const Text(
              'Our fine-tuned NLP model analyzes emotional exhaustion, workload stress, and burnout markers in your reflection.',
              style: TextStyle(color: Colors.grey),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _textController,
              maxLines: 6,
              decoration: InputDecoration(
                hintText: 'Write freely about how your studies, work, and week are feeling...',
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                filled: true,
                fillColor: Colors.grey.shade50,
              ),
            ),
            const SizedBox(height: 14),
            ElevatedButton.icon(
              onPressed: _isAnalyzing ? null : _analyze,
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.deepPurple,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 14),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
              ),
              icon: _isAnalyzing
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                    )
                  : const Icon(Icons.psychology),
              label: Text(_isAnalyzing ? 'Analyzing with NLP...' : 'Analyze Reflection'),
            ),
            if (_error != null) ...[
              const SizedBox(height: 14),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.red.shade50,
                  border: Border.all(color: Colors.red.shade200),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(_error!, style: const TextStyle(color: Colors.red)),
              ),
            ],
            if (_analysisResult != null) ...[
              const SizedBox(height: 24),
              _buildResultCard(),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildResultCard() {
    final label = _analysisResult!['prediction_label'] ?? 0;
    final isHigh = label == 1;
    final prob = _analysisResult!['probability_high_burnout'] ?? 0.0;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: isHigh ? Colors.orange.shade50 : Colors.green.shade50,
        border: Border.all(color: isHigh ? Colors.orange : Colors.green),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                isHigh ? Icons.warning_amber_rounded : Icons.check_circle_outline,
                color: isHigh ? Colors.orange.shade800 : Colors.green.shade800,
                size: 28,
              ),
              const SizedBox(width: 10),
              Text(
                isHigh ? 'High Burnout Sentiment Detected' : 'Healthy Emotional Tone',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  color: isHigh ? Colors.orange.shade900 : Colors.green.shade900,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            isHigh
                ? 'Your journal reflection exhibits indicators of acute academic stress and mental fatigue (Exhaustion Probability: ${(prob * 100).toStringAsFixed(1)}%). Consider scheduling dedicated recovery downtime.'
                : 'Your reflection shows balanced coping language (Exhaustion Probability: ${(prob * 100).toStringAsFixed(1)}%). Continue maintaining your study-life balance.',
            style: const TextStyle(fontSize: 14),
          ),
        ],
      ),
    );
  }
}

