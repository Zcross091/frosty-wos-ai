import 'package:flutter/material.dart';
import '../models/hero_profile.dart';
import '../services/knowledge_service.dart';
import '../widgets/hero_card.dart';
import '../widgets/spatial_background.dart';

class HeroCodexScreen extends StatefulWidget {
  const HeroCodexScreen({super.key});

  @override
  State<HeroCodexScreen> createState() => _HeroCodexScreenState();
}

class _HeroCodexScreenState extends State<HeroCodexScreen> {
  final TextEditingController _searchController = TextEditingController();
  int _selectedGen = 16;
  String _searchQuery = '';

  final List<int> _availableGens = [16, 7, 4, 2, 1, 0];

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    List<HeroProfile> displayedHeroes;

    if (_searchQuery.trim().isNotEmpty) {
      displayedHeroes = KnowledgeService.heroes.where((h) {
        final q = _searchQuery.toLowerCase();
        return h.name.toLowerCase().contains(q) ||
            h.troopTypeString.toLowerCase().contains(q) ||
            h.roleOverview.toLowerCase().contains(q) ||
            h.generationLabel.toLowerCase().contains(q);
      }).toList();
    } else {
      displayedHeroes = KnowledgeService.getHeroesByGeneration(_selectedGen);
    }

    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(
        backgroundColor: const Color(0xFF070D18).withOpacity(0.85),
        elevation: 0,
        title: const Row(
          children: [
            Text('📖 ', style: TextStyle(fontSize: 18)),
            Text(
              'Hero Codex (Gen 0 - 16+)',
              style: TextStyle(
                fontFamily: 'Outfit',
                fontWeight: FontWeight.bold,
                fontSize: 18,
                color: Colors.white,
                letterSpacing: 0.3,
              ),
            ),
          ],
        ),
      ),
      body: SpatialBackground(
        child: Column(
          children: [
            // Search Bar
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
              child: Container(
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(16),
                  boxShadow: [
                    BoxShadow(
                      color: const Color(0xFF00F0FF).withOpacity(0.06),
                      blurRadius: 12,
                    ),
                  ],
                ),
                child: TextField(
                  controller: _searchController,
                  style: const TextStyle(color: Colors.white, fontSize: 14),
                  decoration: InputDecoration(
                    hintText: 'Search hero by name, skill, or troop type...',
                    hintStyle: const TextStyle(color: Color(0xFF64748B), fontSize: 13),
                    filled: true,
                    fillColor: const Color(0xFF0F192C).withOpacity(0.85),
                    prefixIcon: const Icon(Icons.search, color: Color(0xFF00F0FF), size: 20),
                    suffixIcon: _searchQuery.isNotEmpty
                        ? IconButton(
                            icon: const Icon(Icons.clear, color: Color(0xFF94A3B8), size: 18),
                            onPressed: () {
                              _searchController.clear();
                              setState(() => _searchQuery = '');
                            },
                          )
                        : null,
                    contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(16),
                      borderSide: BorderSide(color: const Color(0xFF00F0FF).withOpacity(0.3)),
                    ),
                    enabledBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(16),
                      borderSide: BorderSide(color: const Color(0xFF00F0FF).withOpacity(0.25)),
                    ),
                    focusedBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(16),
                      borderSide: const BorderSide(color: Color(0xFF00F0FF), width: 1.5),
                    ),
                  ),
                  onChanged: (val) => setState(() => _searchQuery = val),
                ),
              ),
            ),

            // Generation Selector Chips (when not searching)
            if (_searchQuery.isEmpty)
              Container(
                height: 50,
                padding: const EdgeInsets.symmetric(vertical: 4),
                child: ListView.builder(
                  scrollDirection: Axis.horizontal,
                  physics: const BouncingScrollPhysics(),
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  itemCount: _availableGens.length,
                  itemBuilder: (context, index) {
                    final gen = _availableGens[index];
                    final isSelected = gen == _selectedGen;
                    final label = gen == 0 ? '⭐ Epic Core' : 'Gen $gen';

                    return Padding(
                      padding: const EdgeInsets.only(right: 8),
                      child: GestureDetector(
                        onTap: () => setState(() => _selectedGen = gen),
                        child: AnimatedContainer(
                          duration: const Duration(milliseconds: 200),
                          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                          decoration: BoxDecoration(
                            gradient: isSelected
                                ? const LinearGradient(
                                    colors: [Color(0xFF00F0FF), Color(0xFF0284C7)],
                                  )
                                : null,
                            color: isSelected ? null : const Color(0xFF0F192C).withOpacity(0.8),
                            borderRadius: BorderRadius.circular(14),
                            border: Border.all(
                              color: isSelected
                                  ? const Color(0xFF00F0FF)
                                  : const Color(0xFF38BDF8).withOpacity(0.2),
                            ),
                            boxShadow: isSelected
                                ? [
                                    BoxShadow(
                                      color: const Color(0xFF00F0FF).withOpacity(0.3),
                                      blurRadius: 10,
                                    ),
                                  ]
                                : null,
                          ),
                          child: Center(
                            child: Text(
                              label,
                              style: TextStyle(
                                color: isSelected ? const Color(0xFF040914) : const Color(0xFFE2E8F0),
                                fontSize: 12.5,
                                fontWeight: FontWeight.bold,
                                fontFamily: 'Outfit',
                              ),
                            ),
                          ),
                        ),
                      ),
                    );
                  },
                ),
              ),

            const SizedBox(height: 8),

            // Heroes 3D Cards Stream
            Expanded(
              child: displayedHeroes.isEmpty
                  ? const Center(
                      child: Text(
                        'No heroes found matching your search.',
                        style: TextStyle(color: Color(0xFF94A3B8)),
                      ),
                    )
                  : ListView.builder(
                      physics: const BouncingScrollPhysics(),
                      padding: const EdgeInsets.all(16),
                      itemCount: displayedHeroes.length,
                      itemBuilder: (context, index) {
                        return HeroCard(hero: displayedHeroes[index]);
                      },
                    ),
            ),
          ],
        ),
      ),
    );
  }
}
