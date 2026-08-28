import 'package:flutter/material.dart';
import '../models/hero_profile.dart';
import '../services/knowledge_service.dart';
import '../widgets/hero_card.dart';

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
      backgroundColor: const Color(0xFF060B13),
      appBar: AppBar(
        backgroundColor: const Color(0xFF0A111F).withOpacity(0.9),
        elevation: 0,
        title: const Row(
          children: [
            Text('📖 ', style: TextStyle(fontSize: 18)),
            Text(
              'Hero Codex (Gen 0 - 16+)',
              style: TextStyle(
                fontFamily: 'Outfit',
                fontWeight: FontWeight.bold,
                fontSize: 17,
                color: Colors.white,
              ),
            ),
          ],
        ),
      ),
      body: Column(
        children: [
          // Search Bar
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
            child: TextField(
              controller: _searchController,
              style: const TextStyle(color: Colors.white, fontSize: 14),
              decoration: InputDecoration(
                hintText: 'Search hero by name, skill, or troop type...',
                hintStyle: const TextStyle(color: Color(0xFF64748B), fontSize: 13),
                filled: true,
                fillColor: const Color(0xFF0F192C),
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
                  borderRadius: BorderRadius.circular(14),
                  borderSide: BorderSide(color: const Color(0xFF00F0FF).withOpacity(0.3)),
                ),
                focusedBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(14),
                  borderSide: const BorderSide(color: Color(0xFF00F0FF), width: 1.5),
                ),
              ),
              onChanged: (val) => setState(() => _searchQuery = val),
            ),
          ),

          // Generation Selector Chips (when not searching)
          if (_searchQuery.isEmpty)
            Container(
              height: 48,
              padding: const EdgeInsets.symmetric(vertical: 4),
              child: ListView.builder(
                scrollDirection: Axis.horizontal,
                padding: const EdgeInsets.symmetric(horizontal: 16),
                itemCount: _availableGens.length,
                itemBuilder: (context, index) {
                  final gen = _availableGens[index];
                  final isSelected = gen == _selectedGen;
                  final label = gen == 0 ? 'Epic (F2P Core)' : 'Gen $gen';

                  return Padding(
                    padding: const EdgeInsets.only(right: 8),
                    child: ChoiceChip(
                      selected: isSelected,
                      backgroundColor: const Color(0xFF0F192C),
                      selectedColor: const Color(0xFF00F0FF),
                      side: BorderSide(
                        color: isSelected
                            ? const Color(0xFF00F0FF)
                            : const Color(0xFF38BDF8).withOpacity(0.25),
                      ),
                      label: Text(
                        label,
                        style: TextStyle(
                          color: isSelected ? const Color(0xFF040914) : Colors.white,
                          fontSize: 12,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      onSelected: (_) => setState(() => _selectedGen = gen),
                    ),
                  );
                },
              ),
            ),

          const SizedBox(height: 6),

          // Heroes List
          Expanded(
            child: displayedHeroes.isEmpty
                ? const Center(
                    child: Text(
                      'No heroes found matching your search.',
                      style: TextStyle(color: Color(0xFF94A3B8)),
                    ),
                  )
                : ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: displayedHeroes.length,
                    itemBuilder: (context, index) {
                      return HeroCard(hero: displayedHeroes[index]);
                    },
                  ),
          ),
        ],
      ),
    );
  }
}
