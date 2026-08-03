import 'package:flutter/material.dart';
import '../services/api_service.dart';

/// This is the "data insert page" — a daily check-in.
/// Heart Rate / Sleep Hours / Study Hours / Academic Stressors are stored for
/// the app's own display, and the "How are you feeling today?" selector is
/// what actually feeds the 90-day forecast model (see backend note in main.py).
class DataInsertScreen extends StatefulWidget {
  const DataInsertScreen({super.key});

  @override
  State<DataInsertScreen> createState() => _DataInsertScreenState();
}

class _DataInsertScreenState extends State<DataInsertScreen> {
  final _heartRateController = TextEditingController();
  final _sleepHoursController = TextEditingController();
  final _studyHoursController = TextEditingController();
  final _academicStressorsController = TextEditingController(text: '0');

  final List<String> _feelingOptions = [
    'Normal',
    'Mild Stress',
    'Moderate Stress',
    'Severe Stress',
    'Anxiety',
    'Depression',
  ];
  int _selectedFeeling = 0;

  bool _isSaving = false;
  String? _message;
  bool _messageIsError = false;

  Future<void> _save() async {
    final heartRate = double.tryParse(_heartRateController.text);
    final sleepHours = double.tryParse(_sleepHoursController.text);
    final studyHours = double.tryParse(_studyHoursController.text);
    final academicStressors = int.tryParse(_academicStressorsController.text);

    if (heartRate == null || sleepHours == null || studyHours == null || academicStressors == null) {
      setState(() {
        _message = 'Please fill in all fields with valid numbers';
        _messageIsError = true;
      });
      return;
    }

    setState(() {
      _isSaving = true;
      _message = null;
    });

    try {
      await ApiService.saveHealthMetric(
        heartRate: heartRate,
        sleepHours: sleepHours,
        studyHours: studyHours,
        academicStressors: academicStressors,
        mentalHealthScore: _selectedFeeling,
      );
      setState(() {
        _message = 'Saved! Today\'s check-in has been recorded.';
        _messageIsError = false;
      });
    } catch (e) {
      setState(() {
        _message = 'Failed to save: ${e.toString().replaceFirst('Exception: ', '')}';
        _messageIsError = true;
      });
    } finally {
      setState(() {
        _isSaving = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Daily Check-in'),
        backgroundColor: Colors.deepPurple,
        foregroundColor: Colors.white,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Current Health Metrics', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 16),
            TextField(
              controller: _heartRateController,
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
              decoration: const InputDecoration(
                labelText: 'Heart Rate (BPM)',
                prefixIcon: Icon(Icons.favorite, color: Colors.red),
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _sleepHoursController,
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
              decoration: const InputDecoration(
                labelText: 'Sleep Hours',
                prefixIcon: Icon(Icons.bedtime, color: Colors.blue),
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _studyHoursController,
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
              decoration: const InputDecoration(
                labelText: 'Study Hours today',
                prefixIcon: Icon(Icons.menu_book),
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _academicStressorsController,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(
                labelText: 'Upcoming deadlines / exams this week',
                prefixIcon: Icon(Icons.warning_amber),
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 24),
            const Text('How are you feeling today?', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            ...List.generate(_feelingOptions.length, (index) {
              return RadioListTile<int>(
                title: Text(_feelingOptions[index]),
                value: index,
                groupValue: _selectedFeeling,
                onChanged: (value) {
                  setState(() {
                    _selectedFeeling = value ?? 0;
                  });
                },
              );
            }),
            const SizedBox(height: 16),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.deepPurple,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                ),
                onPressed: _isSaving ? null : _save,
                child: _isSaving
                    ? const SizedBox(
                        height: 20,
                        width: 20,
                        child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                    : const Text('Save Health Metrics'),
              ),
            ),
            if (_message != null) ...[
              const SizedBox(height: 16),
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: _messageIsError ? Colors.red : Colors.green,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(_message!, style: const TextStyle(color: Colors.white)),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
