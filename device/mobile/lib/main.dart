import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'screens/chat_screen.dart';
import 'screens/state_age_screen.dart';
import 'screens/hero_codex_screen.dart';
import 'screens/formations_screen.dart';
import 'screens/settings_screen.dart';
import 'services/ai_service.dart';
import 'services/update_service.dart';
import 'services/knowledge_service.dart';

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
        scaffoldBackgroundColor: const Color(0xFF040812),
        primaryColor: const Color(0xFF00F0FF),
        colorScheme: const ColorScheme.dark(
          primary: Color(0xFF00F0FF),
          secondary: Color(0xFF0284C7),
          tertiary: Color(0xFFF59E0B),
          surface: Color(0xFF0F192C),
          background: Color(0xFF040812),
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

  @override
  void initState() {
    super.initState();
    // Synchronize latest hero roster from website repository
    KnowledgeService.syncWithWebsite();

    // Check for new releases on GitHub automatically on startup
    WidgetsBinding.instance.addPostFrameCallback((_) {
      UpdateService.checkForUpdates(context);
    });
  }

  final List<Widget> _screens = const [
    ChatScreen(),
    StateAgeScreen(),
    HeroCodexScreen(),
    FormationsScreen(),
    SettingsScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final isDesktop = constraints.maxWidth >= 720;

        if (isDesktop) {
          return Scaffold(
            backgroundColor: const Color(0xFF040812),
            body: Row(
              children: [
                NavigationRail(
                  selectedIndex: _currentIndex,
                  backgroundColor: const Color(0xFF070D18),
                  indicatorColor: const Color(0xFF00F0FF).withOpacity(0.2),
                  extended: constraints.maxWidth >= 1000,
                  minWidth: 72,
                  onDestinationSelected: (index) {
                    setState(() => _currentIndex = index);
                  },
                  leading: Padding(
                    padding: const EdgeInsets.symmetric(vertical: 20),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Container(
                          width: 40,
                          height: 40,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            gradient: const RadialGradient(
                              colors: [Color(0xFF00F0FF), Color(0xFF0284C7)],
                            ),
                            boxShadow: [
                              BoxShadow(
                                color: const Color(0xFF00F0FF).withOpacity(0.4),
                                blurRadius: 12,
                              ),
                            ],
                          ),
                          child: const Center(child: Text('❄️', style: TextStyle(fontSize: 20))),
                        ),
                        if (constraints.maxWidth >= 1000) ...[
                          const SizedBox(width: 12),
                          const Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Text(
                                'Frosty AI',
                                style: TextStyle(
                                  fontFamily: 'Outfit',
                                  fontWeight: FontWeight.bold,
                                  fontSize: 17,
                                  color: Colors.white,
                                ),
                              ),
                              Text(
                                'Tactical Command',
                                style: TextStyle(fontSize: 11, color: Color(0xFF00F0FF)),
                              ),
                            ],
                          ),
                        ],
                      ],
                    ),
                  ),
                  destinations: const [
                    NavigationRailDestination(
                      icon: Icon(Icons.chat_bubble_outline_rounded, color: Color(0xFF94A3B8)),
                      selectedIcon: Icon(Icons.chat_bubble_rounded, color: Color(0xFF00F0FF)),
                      label: Text('AI Oracle'),
                    ),
                    NavigationRailDestination(
                      icon: Icon(Icons.timer_outlined, color: Color(0xFF94A3B8)),
                      selectedIcon: Icon(Icons.timer_rounded, color: Color(0xFF00F0FF)),
                      label: Text('State Age'),
                    ),
                    NavigationRailDestination(
                      icon: Icon(Icons.menu_book_outlined, color: Color(0xFF94A3B8)),
                      selectedIcon: Icon(Icons.menu_book_rounded, color: Color(0xFF00F0FF)),
                      label: Text('Hero Codex'),
                    ),
                    NavigationRailDestination(
                      icon: Icon(Icons.shield_outlined, color: Color(0xFF94A3B8)),
                      selectedIcon: Icon(Icons.shield_rounded, color: Color(0xFF00F0FF)),
                      label: Text('Formations'),
                    ),
                    NavigationRailDestination(
                      icon: Icon(Icons.settings_outlined, color: Color(0xFF94A3B8)),
                      selectedIcon: Icon(Icons.settings_rounded, color: Color(0xFF00F0FF)),
                      label: Text('Settings'),
                    ),
                  ],
                ),
                const VerticalDivider(thickness: 1, width: 1, color: Colors.white10),
                Expanded(
                  child: IndexedStack(
                    index: _currentIndex,
                    children: _screens,
                  ),
                ),
              ],
            ),
          );
        }

        // Mobile Screen Layout with Floating Glassmorphic Dock
        return Scaffold(
          backgroundColor: const Color(0xFF040812),
          body: IndexedStack(
            index: _currentIndex,
            children: _screens,
          ),
          bottomNavigationBar: Container(
            decoration: BoxDecoration(
              color: const Color(0xFF070D18).withOpacity(0.95),
              border: Border(
                top: BorderSide(color: const Color(0xFF00F0FF).withOpacity(0.2), width: 1.2),
              ),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.5),
                  blurRadius: 20,
                  offset: const Offset(0, -6),
                ),
                BoxShadow(
                  color: const Color(0xFF00F0FF).withOpacity(0.08),
                  blurRadius: 15,
                ),
              ],
            ),
            child: NavigationBar(
              selectedIndex: _currentIndex,
              backgroundColor: Colors.transparent,
              indicatorColor: const Color(0xFF00F0FF).withOpacity(0.2),
              surfaceTintColor: Colors.transparent,
              elevation: 0,
              height: 65,
              onDestinationSelected: (index) {
                setState(() => _currentIndex = index);
              },
              destinations: const [
                NavigationDestination(
                  icon: Icon(Icons.chat_bubble_outline_rounded, color: Color(0xFF94A3B8), size: 22),
                  selectedIcon: Icon(Icons.chat_bubble_rounded, color: Color(0xFF00F0FF), size: 24),
                  label: 'AI Oracle',
                ),
                NavigationDestination(
                  icon: Icon(Icons.timer_outlined, color: Color(0xFF94A3B8), size: 22),
                  selectedIcon: Icon(Icons.timer_rounded, color: Color(0xFF00F0FF), size: 24),
                  label: 'State Age',
                ),
                NavigationDestination(
                  icon: Icon(Icons.menu_book_outlined, color: Color(0xFF94A3B8), size: 22),
                  selectedIcon: Icon(Icons.menu_book_rounded, color: Color(0xFF00F0FF), size: 24),
                  label: 'Codex',
                ),
                NavigationDestination(
                  icon: Icon(Icons.shield_outlined, color: Color(0xFF94A3B8), size: 22),
                  selectedIcon: Icon(Icons.shield_rounded, color: Color(0xFF00F0FF), size: 24),
                  label: 'Formations',
                ),
                NavigationDestination(
                  icon: Icon(Icons.settings_outlined, color: Color(0xFF94A3B8), size: 22),
                  selectedIcon: Icon(Icons.settings_rounded, color: Color(0xFF00F0FF), size: 24),
                  label: 'Settings',
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}
