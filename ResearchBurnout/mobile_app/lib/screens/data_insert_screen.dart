import 'package:flutter/material.dart';
import '../services/api_service.dart';

/// The Daily Check-in / Data Insert Page for MindSense — ResearchBurnout.
/// Captures daily behavioral parameters and an optional reflective journal text.
class DataInsertScreen extends StatefulWidget {
  const DataInsertScreen({super.key});

  @override
  State<DataInsertScreen> createState() => _DataInsertScreenState();
}

class _DataInsertScreenState extends State<DataInsertScreen> {
  final _heartRateController = TextEditingController(text: '75');
  final _sleepHoursController = TextEditingController(text: '7.0');
  final _workHoursController = TextEditingController(text: '6.5');
  final _screenTimeController = TextEditingController(text: '5.0');
  final _exerciseHoursController = TextEditingController(text: '0.5');
  final _journalController = TextEditingController();

  double _stressLevel = 4;
  int _sleepQuality = 3;

  bool _isSaving = false;
  String? _message;
  bool _messageIsError = false;

  Future<void> _save() async {
    final heartRate = double.tryParse(_heartRateController.text);
    final sleepHours = double.tryParse(_sleepHoursController.text);
    final workHours = double.tryParse(_workHoursController.text);
    final screenTime = double.tryParse(_screenTimeController.text);
    final exerciseHours = double.tryParse(_exerciseHoursController.text);

    if (heartRate == null || sleepHours == null || workHours == null || screenTime == null || exerciseHours == null) {
      setState(() {
        _message = 'Please fill in all numerical fields with valid numbers.';
        _messageIsError = true;
      });
      return;
    }

    setState(() {
      _isSaving = true;
      _message = null;
    });

    try {
      await ApiService.saveBurnoutMetric(
        heartRate: heartRate,
        sleepHours: sleepHours,
        workHours: workHours,
        stressLevel: _stressLevel.round(),
        screenTime: screenTime,
        exerciseHours: exerciseHours,
        sleepQuality: _sleepQuality,
        journalText: _journalController.text.trim(),
      );
      setState(() {
        _message = 'Saved! Today\'s burnout check-in has been recorded.';
        _messageIsError = false;
        _journalController.clear();
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
        title: const Text('Daily Burnout Check-in'),
        backgroundColor: Colors.deepPurple,
        foregroundColor: Colors.white,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Record Today\'s Metrics',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 6),
            const Text(
              'These behavioral values feed the predictive burnout pipeline and NLP text model.',
              style: TextStyle(color: Colors.grey, fontSize: 13),
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _heartRateController,
                    keyboardType: const TextInputType.numberWithOptions(decimal: true),
                    decoration: const InputDecoration(
                      labelText: 'Heart Rate (BPM)',
                      prefixIcon: Icon(Icons.favorite, color: Colors.red),
                      border: OutlineInputBorder(),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: TextField(
                    controller: _sleepHoursController,
                    keyboardType: const TextInputType.numberWithOptions(decimal: true),
                    decoration: const InputDecoration(
                      labelText: 'Sleep (Hours)',
                      prefixIcon: Icon(Icons.bedtime, color: Colors.indigo),
                      border: OutlineInputBorder(),
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _workHoursController,
                    keyboardType: const TextInputType.numberWithOptions(decimal: true),
                    decoration: const InputDecoration(
                      labelText: 'Study/Work (Hrs)',
                      prefixIcon: Icon(Icons.school, color: Colors.deepOrange),
                      border: OutlineInputBorder(),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: TextField(
                    controller: _screenTimeController,
                    keyboardType: const TextInputType.numberWithOptions(decimal: true),
                    decoration: const InputDecoration(
                      labelText: 'Screen Time (Hrs)',
                      prefixIcon: Icon(Icons.smartphone, color: Colors.blue),
                      border: OutlineInputBorder(),
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _exerciseHoursController,
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
              decoration: const InputDecoration(
                labelText: 'Exercise / Physical Activity (Hours)',
                prefixIcon: Icon(Icons.directions_run, color: Colors.green),
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 20),
            Text(
              'Perceived Stress Level: ${_stressLevel.round()} / 10',
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),
            Slider(
              value: _stressLevel,
              min: 1,
              max: 10,
              divisions: 9,
              activeColor: Colors.deepPurple,
              label: '${_stressLevel.round()}',
              onChanged: (val) => setState(() => _stressLevel = val),
            ),
            const SizedBox(height: 8),
            const Text('Sleep Quality', style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 6),
            Wrap(
              spacing: 8,
              children: List.generate(5, (idx) {
                final star = idx + 1;
                return ChoiceChip(
                  label: Text('$star ★'),
                  selected: _sleepQuality == star,
                  selectedColor: Colors.deepPurple.shade100,
                  onSelected: (_) => setState(() => _sleepQuality = star),
                );
              }),
            ),
            const SizedBox(height: 20),
            const Text(
              'Reflective Journal (NLP Sentiment Analysis)',
              style: TextStyle(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 6),
            TextField(
              controller: _journalController,
              maxLines: 4,
              decoration: const InputDecoration(
                hintText: 'How did today go? Write about stress, workload, or fatigue...',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 24),
            SizedBox(
              width: double.infinity,
              height: 48,
              child: ElevatedButton.icon(
                onPressed: _isSaving ? null : _save,
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.deepPurple,
                  foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                ),
                icon: _isSaving
                    ? const SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                      )
                    : const Icon(Icons.save),
                label: Text(_isSaving ? 'Saving...' : 'Save Today\'s Check-in'),
              ),
            ),
            if (_message != null) ...[
              const SizedBox(height: 16),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: _messageIsError ? Colors.red.shade50 : Colors.green.shade50,
                  border: Border.all(color: _messageIsError ? Colors.red : Colors.green),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  _message!,
                  style: TextStyle(color: _messageIsError ? Colors.red.shade900 : Colors.green.shade900),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
