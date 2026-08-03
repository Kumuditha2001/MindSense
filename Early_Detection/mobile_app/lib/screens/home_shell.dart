import 'package:flutter/material.dart';
import 'home_screen.dart';
import 'data_insert_screen.dart';

/// The main app shell after login — bottom navigation bar matching your
/// original design. Home and the Check-in (data insert) page are fully
/// built; the rest are placeholders to be filled in next.
class HomeShell extends StatefulWidget {
  const HomeShell({super.key});

  @override
  State<HomeShell> createState() => _HomeShellState();
}

class _HomeShellState extends State<HomeShell> {
  int _selectedIndex = 0;

  final List<Widget> _screens = const [
    HomeScreen(),
    _ComingSoonScreen(title: 'Schedule'),
    _ComingSoonScreen(title: 'Academic'),
    _ComingSoonScreen(title: 'Behavior'),
    DataInsertScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _selectedIndex,
        children: _screens,
      ),
      bottomNavigationBar: BottomNavigationBar(
        type: BottomNavigationBarType.fixed,
        currentIndex: _selectedIndex,
        selectedItemColor: Colors.deepPurple,
        onTap: (index) {
          setState(() {
            _selectedIndex = index;
          });
        },
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.home), label: 'Home'),
          BottomNavigationBarItem(icon: Icon(Icons.calendar_today), label: 'Schedule'),
          BottomNavigationBarItem(icon: Icon(Icons.menu_book), label: 'Academic'),
          BottomNavigationBarItem(icon: Icon(Icons.directions_run), label: 'Behavior'),
          BottomNavigationBarItem(icon: Icon(Icons.bar_chart), label: 'Check-in'),
        ],
      ),
    );
  }
}

class _ComingSoonScreen extends StatelessWidget {
  final String title;
  const _ComingSoonScreen({required this.title});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(title)),
      body: Center(
        child: Text('$title screen — coming soon', style: const TextStyle(color: Colors.grey)),
      ),
    );
  }
}
