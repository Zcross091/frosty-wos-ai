import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'screens/chat_screen.dart';
import 'screens/state_age_screen.dart';
import 'screens/hero_codex_screen.dart';
import 'screens/formations_screen.dart';
import 'screens/settings_screen.dart';
import 'services/ai_service.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AIService()),
      ],
      child: const FrostyApp(),
    ),
  );
}

class FrostyApp extends StatelessWidget {
  const FrostyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Frosty WOS AI',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.dark,
        scaffoldBackgroundColor: const Color(0xFF060B13),
        primaryColor: const Color(0xFF00F0FF),
        colorScheme: const ColorScheme.dark(
          primary: Color(0xFF00F0FF),
          secondary: Color(0xFF0088FF),
          surface: Color(0xFF0F192C),
          background: Color(0xFF060B13),
        ),
        fontFamily: 'Outfit',
        useMaterial3: true,
      ),
      home: const MainNavigationShell(),
    );
  }
}

class MainNavigationShell extends StatefulWidget {
  const MainNavigationShell({super.key});

  @override
  State<MainNavigationShell> createState() => _MainNavigationShellState();
}

class _MainNavigationShellState extends State<MainNavigationShell> {
  int _currentIndex = 0;

  final List<Widget> _screens = const [
    ChatScreen(),
    StateAgeScreen(),
    HeroCodexScreen(),
    FormationsScreen(),
    SettingsScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _currentIndex,
        children: _screens,
      ),
      bottomNavigationBar: Container(
        decoration: BoxDecoration(
          color: const Color(0xFF0A111F),
          border: Border(
            top: BorderSide(color: const Color(0xFF00F0FF).withOpacity(0.18)),
          ),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.4),
              blurRadius: 16,
              offset: const Offset(0, -4),
            ),
          ],
        ),
        child: NavigationBar(
          selectedIndex: _currentIndex,
          backgroundColor: Colors.transparent,
          indicatorColor: const Color(0xFF00F0FF).withOpacity(0.2),
          surfaceTintColor: Colors.transparent,
          elevation: 0,
          onDestinationSelected: (index) {
            setState(() => _currentIndex = index);
          },
          destinations: const [
            NavigationDestination(
              icon: Icon(Icons.chat_bubble_outline_rounded, color: Color(0xFF94A3B8)),
              selectedIcon: Icon(Icons.chat_bubble_rounded, color: Color(0xFF00F0FF)),
              label: 'AI Oracle',
            ),
            NavigationDestination(
              icon: Icon(Icons.timer_outlined, color: Color(0xFF94A3B8)),
              selectedIcon: Icon(Icons.timer_rounded, color: Color(0xFF00F0FF)),
              label: 'State Age',
            ),
            NavigationDestination(
              icon: Icon(Icons.menu_book_outlined, color: Color(0xFF94A3B8)),
              selectedIcon: Icon(Icons.menu_book_rounded, color: Color(0xFF00F0FF)),
              label: 'Codex',
            ),
            NavigationDestination(
              icon: Icon(Icons.shield_outlined, color: Color(0xFF94A3B8)),
              selectedIcon: Icon(Icons.shield_rounded, color: Color(0xFF00F0FF)),
              label: 'Formations',
            ),
            NavigationDestination(
              icon: Icon(Icons.settings_outlined, color: Color(0xFF94A3B8)),
              selectedIcon: Icon(Icons.settings_rounded, color: Color(0xFF00F0FF)),
              label: 'Community',
            ),
          ],
        ),
      ),
    );
  }
}
