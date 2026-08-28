import 'package:flutter/material.dart';
import '../widgets/ratio_bar.dart';

class FormationsScreen extends StatefulWidget {
  const FormationsScreen({super.key});

  @override
  State<FormationsScreen> createState() => _FormationsScreenState();
}

class _FormationsScreenState extends State<FormationsScreen> {
  int _selectedPreset = 0;
  double _marchCapacity = 140000;

  final List<Map<String, dynamic>> _presets = [
    {
      'title': 'Standard PvP Field Battle',
      'icon': '⚔️',
      'inf': 50,
      'lan': 20,
      'mar': 30,
      'badge': '50 / 20 / 30',
      'doctrine': 'Infantry absorbs 100% of enemy front damage. If infantry falls below 40%, your marksmen will be eliminated immediately. 50/20/30 gives your marksmen the protection needed to deal maximum sustained damage over extended fights.',
      'heroes': '1 Frontline Tank (Bradley/Flint/Seigel) + 1 Lancer (Gordon/Ursar) + 1 Marksman (Edith/Aisling)',
    },
    {
      'title': 'Bear Trap (Max PvE Damage)',
      'icon': '🐻',
      'inf': 10,
      'lan': 10,
      'mar': 80,
      'badge': '10 / 10 / 80',
      'doctrine': 'The Bear Trap monster never kills or injures your troops! Defensive shields and heavy infantry are unnecessary. Pack 80% Marksmen to maximize total raw damage points.',
      'heroes': 'Joiner Lead: Jessie (+25% Damage). Deputies: Seo-yoon (+20% Atk) + Highest Stat Marksman',
    },
    {
      'title': 'Castle & Stronghold Defense',
      'icon': '🏰',
      'inf': 60,
      'lan': 20,
      'mar': 20,
      'badge': '60 / 20 / 20',
      'doctrine': 'When defending against multiple incoming enemy rallies during Sunfire Castle or SvS, your wall absorbs immense burst damage. 60% Infantry with Sergey or Bradley ensures your garrison never gets breached.',
      'heroes': 'Garrison Lead: Sergey / Bradley / Hector with high defender health buffs.',
    },
    {
      'title': 'High Burst 4-1-1 Attack',
      'icon': '🎯',
      'inf': 40,
      'lan': 10,
      'mar': 50,
      'badge': '40 / 10 / 50',
      'doctrine': 'An aggressive offensive lineup designed for quick wipeouts against weaker enemy cities and foundry nodes. Gives huge marksman burst while maintaining the 40% minimum infantry threshold.',
      'heroes': 'Lead: Flint / Jeronimo + Alonso / Lynn + Philly',
    },
  ];

  @override
  Widget build(BuildContext context) {
    final active = _presets[_selectedPreset];
    final infCount = ((_marchCapacity * (active['inf'] as int)) / 100).round();
    final lanCount = ((_marchCapacity * (active['lan'] as int)) / 100).round();
    final marCount = ((_marchCapacity * (active['mar'] as int)) / 100).round();

    return Scaffold(
      backgroundColor: const Color(0xFF060B13),
      appBar: AppBar(
        backgroundColor: const Color(0xFF0A111F).withOpacity(0.9),
        elevation: 0,
        title: const Row(
          children: [
            Text('📊 ', style: TextStyle(fontSize: 18)),
            Text(
              'Troop Formations & Lineups',
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
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Presets Selector Grid
            GridView.builder(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: 2,
                crossAxisSpacing: 10,
                mainAxisSpacing: 10,
                childAspectRatio: 1.8,
              ),
              itemCount: _presets.length,
              itemBuilder: (context, index) {
                final item = _presets[index];
                final isSelected = index == _selectedPreset;

                return GestureDetector(
                  onTap: () => setState(() => _selectedPreset = index),
                  child: Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: isSelected
                          ? const Color(0xFF00F0FF).withOpacity(0.15)
                          : const Color(0xFF0F192C),
                      borderRadius: BorderRadius.circular(14),
                      border: Border.all(
                        color: isSelected
                            ? const Color(0xFF00F0FF)
                            : const Color(0xFF38BDF8).withOpacity(0.2),
                        width: isSelected ? 1.5 : 1,
                      ),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Row(
                          children: [
                            Text(item['icon'], style: const TextStyle(fontSize: 18)),
                            const SizedBox(width: 6),
                            Expanded(
                              child: Text(
                                item['title'],
                                style: const TextStyle(
                                  color: Colors.white,
                                  fontSize: 12,
                                  fontWeight: FontWeight.bold,
                                ),
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 4),
                        Text(
                          item['badge'],
                          style: TextStyle(
                            color: isSelected ? const Color(0xFF00F0FF) : const Color(0xFF94A3B8),
                            fontSize: 12,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
            const SizedBox(height: 20),

            // Active Formation Display Card
            Container(
              decoration: BoxDecoration(
                color: const Color(0xFF0F192C),
                borderRadius: BorderRadius.circular(20),
                border: Border.all(color: const Color(0xFF00F0FF).withOpacity(0.35)),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.4),
                    blurRadius: 16,
                  ),
                ],
              ),
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Expanded(
                          child: Text(
                            active['title'],
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 18,
                              fontWeight: FontWeight.bold,
                              fontFamily: 'Outfit',
                            ),
                          ),
                        ),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                          decoration: BoxDecoration(
                            color: const Color(0xFF00F0FF).withOpacity(0.15),
                            borderRadius: BorderRadius.circular(20),
                            border: Border.all(color: const Color(0xFF00F0FF)),
                          ),
                          child: Text(
                            active['badge'],
                            style: const TextStyle(
                              color: Color(0xFF00F0FF),
                              fontSize: 13,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),

                    // Ratio Bar
                    RatioBar(
                      infantry: active['inf'],
                      lancer: active['lan'],
                      marksman: active['mar'],
                    ),
                    const SizedBox(height: 20),

                    // March Capacity Slider
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text(
                          'Your March Capacity:',
                          style: TextStyle(color: Color(0xFF94A3B8), fontSize: 13),
                        ),
                        Text(
                          '${_marchCapacity.round().toString()} Troops',
                          style: const TextStyle(
                            color: Color(0xFF00F0FF),
                            fontSize: 14,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ],
                    ),
                    Slider(
                      value: _marchCapacity,
                      min: 50000,
                      max: 250000,
                      divisions: 40,
                      activeColor: const Color(0xFF00F0FF),
                      inactiveColor: const Color(0xFF1E293B),
                      onChanged: (val) => setState(() => _marchCapacity = val),
                    ),
                    const SizedBox(height: 10),

                    // Exact Troop Counts
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: Colors.black.withOpacity(0.3),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceAround,
                        children: [
                          _buildTroopCount('🛡️ Infantry', infCount, const Color(0xFF60A5FA)),
                          _buildTroopCount('🐎 Lancers', lanCount, const Color(0xFFF87171)),
                          _buildTroopCount('🏹 Marksmen', marCount, const Color(0xFF4ADE80)),
                        ],
                      ),
                    ),
                    const SizedBox(height: 18),

                    // Recommended Heroes
                    const Text(
                      'Recommended 3-Hero Positions:',
                      style: TextStyle(
                        color: Color(0xFF38BDF8),
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      active['heroes'],
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 13,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                    const SizedBox(height: 16),

                    // Doctrine Box
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: const Color(0xFF00F0FF).withOpacity(0.06),
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(color: const Color(0xFF00F0FF).withOpacity(0.2)),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            '💡 Grandmaster Tactical Doctrine',
                            style: TextStyle(
                              color: Color(0xFF00F0FF),
                              fontSize: 12,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            active['doctrine'],
                            style: const TextStyle(
                              color: Color(0xFFCBD5E1),
                              fontSize: 12.5,
                              height: 1.4,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTroopCount(String label, int count, Color color) {
    return Column(
      children: [
        Text(
          label,
          style: const TextStyle(color: Color(0xFF94A3B8), fontSize: 11),
        ),
        const SizedBox(height: 2),
        Text(
          count.toString(),
          style: TextStyle(
            color: color,
            fontSize: 14,
            fontWeight: FontWeight.bold,
          ),
        ),
      ],
    );
  }
}
