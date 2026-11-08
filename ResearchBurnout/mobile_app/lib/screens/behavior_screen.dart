import 'package:flutter/material.dart';

class BehaviorScreen extends StatelessWidget {
  const BehaviorScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Behavioral Assessment'),
        backgroundColor: Colors.deepPurple,
        foregroundColor: Colors.white,
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: const [
          Text(
            'Burnout Behavioral Indicators',
            style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
          ),
          SizedBox(height: 6),
          Text(
            'The ResearchBurnout model monitors lifestyle and academic behaviors known to trigger severe student burnout:',
            style: TextStyle(color: Colors.grey),
          ),
          SizedBox(height: 16),
          _BehaviorPillarCard(
            title: '1. Sleep & Circadian Balance',
            icon: Icons.bedtime,
            color: Colors.indigo,
            points: [
              'Target: 7 to 9 hours of uninterrupted rest',
              'Less than 6 hours dramatically accelerates cognitive exhaustion and irritability',
              'Consistent bedtimes reinforce rapid restorative REM sleep',
            ],
          ),
          SizedBox(height: 14),
          _BehaviorPillarCard(
            title: '2. Study & Workload Intensity',
            icon: Icons.schedule,
            color: Colors.deepOrange,
            points: [
              'Target: Keep continuous study blocks below 90 minutes',
              'High workloads exceeding 9 hours daily elevate chronic cortisol',
              'Utilize the 25/5 Pomodoro method to avert attention fatigue',
            ],
          ),
          SizedBox(height: 14),
          _BehaviorPillarCard(
            title: '3. Digital & Sensory Stimulation',
            icon: Icons.smartphone,
            color: Colors.purple,
            points: [
              'Target: Keep non-essential screen time under 5-6 hours',
              'Evening screen exposure impairs sleep quality by 40%',
              'Take a 10-minute digital detox after intense lectures',
            ],
          ),
          SizedBox(height: 14),
          _BehaviorPillarCard(
            title: '4. Physical Reset & Movement',
            icon: Icons.directions_walk,
            color: Colors.teal,
            points: [
              'Target: Minimum 20-30 minutes daily moderate exercise',
              'Aerobic walking or cycling lowers perceived stress levels by up to 30%',
              'Breaks muscular tension accumulated during long study periods',
            ],
          ),
        ],
      ),
    );
  }
}

class _BehaviorPillarCard extends StatelessWidget {
  final String title;
  final IconData icon;
  final Color color;
  final List<String> points;

  const _BehaviorPillarCard({
    required this.title,
    required this.icon,
    required this.color,
    required this.points,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                CircleAvatar(
                  backgroundColor: color.withAlpha(38),
                  foregroundColor: color,
                  child: Icon(icon),
                ),
                const SizedBox(width: 12),
                Text(
                  title,
                  style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                ),
              ],
            ),
            const SizedBox(height: 12),
            ...points.map(
              (pt) => Padding(
                padding: const EdgeInsets.symmetric(vertical: 3),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('• ', style: TextStyle(fontWeight: FontWeight.bold)),
                    Expanded(child: Text(pt, style: const TextStyle(fontSize: 13.5))),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
