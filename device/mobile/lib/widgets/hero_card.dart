import 'package:flutter/material.dart';
import '../models/hero_profile.dart';

/// 3D Interactive Hero Card with Perspective Tilt Physics & Holographic Glow
class HeroCard extends StatefulWidget {
  final HeroProfile hero;

  const HeroCard({super.key, required this.hero});

  @override
  State<HeroCard> createState() => _HeroCardState();
}

class _HeroCardState extends State<HeroCard> with SingleTickerProviderStateMixin {
  double _rotateX = 0.0;
  double _rotateY = 0.0;
  bool _isExpanded = false;

  late AnimationController _springController;
  late Animation<double> _animX;
  late Animation<double> _animY;

  @override
  void initState() {
    super.initState();
    _springController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 400),
    );
  }

  @override
  void dispose() {
    _springController.dispose();
    super.dispose();
  }

  void _onPanUpdate(DragUpdateDetails details, Size size) {
    setState(() {
      // Calculate normalized tilt within [-0.15, 0.15] radians (~8.5 degrees)
      final normX = (details.localPosition.dx / size.width) - 0.5;
      final normY = (details.localPosition.dy / size.height) - 0.5;
      _rotateY = normX * 0.28;
      _rotateX = -normY * 0.28;
    });
  }

  void _onPanEnd(DragEndDetails details) {
    _animX = Tween<double>(begin: _rotateX, end: 0.0).animate(
      CurvedAnimation(parent: _springController, curve: Curves.elasticOut),
    );
    _animY = Tween<double>(begin: _rotateY, end: 0.0).animate(
      CurvedAnimation(parent: _springController, curve: Curves.elasticOut),
    );

    _springController.reset();
    _springController.forward();

    _animX.addListener(() {
      setState(() {
        _rotateX = _animX.value;
        _rotateY = _animY.value;
      });
    });
  }

  @override
  Widget build(BuildContext context) {
    final hero = widget.hero;

    // Color Dynamics based on Troop Class
    Color primaryGlow;
    Color secondaryGlow;
    String troopBadge;

    switch (hero.troopType) {
      case TroopType.infantry:
        primaryGlow = const Color(0xFF00F0FF); // Frost Cyan
        secondaryGlow = const Color(0xFF0284C7); // Deep Cobalt
        troopBadge = 'INFANTRY TANK';
        break;
      case TroopType.lancer:
        primaryGlow = const Color(0xFFF59E0B); // Solar Amber
        secondaryGlow = const Color(0xFFEA580C); // Flame Orange
        troopBadge = 'LANCER FLANK';
        break;
      case TroopType.marksman:
        primaryGlow = const Color(0xFFEC4899); // Neon Magenta
        secondaryGlow = const Color(0xFFEF4444); // Crimson Burst
        troopBadge = 'MARKSMAN DPS';
        break;
    }

    return LayoutBuilder(
      builder: (context, constraints) {
        final cardSize = Size(constraints.maxWidth, 300);

        return GestureDetector(
          onPanUpdate: (details) => _onPanUpdate(details, cardSize),
          onPanEnd: _onPanEnd,
          onTap: () => setState(() => _isExpanded = !_isExpanded),
          child: Transform(
            alignment: FractionalOffset.center,
            transform: Matrix4.identity()
              ..setEntry(3, 2, 0.0014) // 3D Perspective Depth
              ..rotateX(_rotateX)
              ..rotateY(_rotateY),
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 300),
              margin: const EdgeInsets.only(bottom: 18),
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(22),
                gradient: LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: [
                    const Color(0xFF132238).withOpacity(0.85),
                    const Color(0xFF0A1220).withOpacity(0.92),
                  ],
                ),
                border: Border.all(
                  color: primaryGlow.withOpacity(0.45),
                  width: 1.4,
                ),
                boxShadow: [
                  BoxShadow(
                    color: primaryGlow.withOpacity(0.18),
                    blurRadius: 22,
                    spreadRadius: 1,
                    offset: Offset(_rotateY * 30, -_rotateX * 30),
                  ),
                  BoxShadow(
                    color: Colors.black.withOpacity(0.6),
                    blurRadius: 20,
                    offset: const Offset(0, 8),
                  ),
                ],
              ),
              child: Padding(
                padding: const EdgeInsets.all(18),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Header Bar
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Row(
                          children: [
                            Container(
                              width: 44,
                              height: 44,
                              decoration: BoxDecoration(
                                shape: BoxShape.circle,
                                color: primaryGlow.withOpacity(0.14),
                                border: Border.all(color: primaryGlow, width: 1.2),
                                boxShadow: [
                                  BoxShadow(
                                    color: primaryGlow.withOpacity(0.3),
                                    blurRadius: 10,
                                  ),
                                ],
                              ),
                              child: Center(
                                child: Text(
                                  hero.troopIcon,
                                  style: const TextStyle(fontSize: 20),
                                ),
                              ),
                            ),
                            const SizedBox(width: 12),
                            Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  hero.name,
                                  style: const TextStyle(
                                    color: Colors.white,
                                    fontSize: 19,
                                    fontWeight: FontWeight.bold,
                                    fontFamily: 'Outfit',
                                    letterSpacing: 0.3,
                                  ),
                                ),
                                Text(
                                  '${hero.generationLabel} • ${hero.rarity}',
                                  style: TextStyle(
                                    color: primaryGlow.withOpacity(0.9),
                                    fontSize: 12,
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                              ],
                            ),
                          ],
                        ),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                          decoration: BoxDecoration(
                            gradient: LinearGradient(
                              colors: [primaryGlow.withOpacity(0.2), secondaryGlow.withOpacity(0.2)],
                            ),
                            borderRadius: BorderRadius.circular(20),
                            border: Border.all(color: primaryGlow.withOpacity(0.7), width: 1.2),
                          ),
                          child: Text(
                            troopBadge,
                            style: TextStyle(
                              color: primaryGlow,
                              fontSize: 10.5,
                              fontWeight: FontWeight.w800,
                              letterSpacing: 0.6,
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),

                    // Overview
                    Text(
                      hero.roleOverview,
                      style: const TextStyle(
                        color: Color(0xFFE2E8F0),
                        fontSize: 13,
                        height: 1.45,
                      ),
                    ),
                    const SizedBox(height: 14),

                    // Expedition Multiplier Pill
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                      decoration: BoxDecoration(
                        color: Colors.black.withOpacity(0.35),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: primaryGlow.withOpacity(0.25)),
                      ),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          const Text(
                            'Expedition Multiplier',
                            style: TextStyle(color: Color(0xFF94A3B8), fontSize: 12, fontWeight: FontWeight.w500),
                          ),
                          Text(
                            '+${hero.expeditionMultiplier.toStringAsFixed(2)}%',
                            style: TextStyle(
                              color: primaryGlow,
                              fontSize: 14,
                              fontWeight: FontWeight.bold,
                              fontFamily: 'Outfit',
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 12),

                    // F2P vs P2W Investment Verdict
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: const Color(0xFFF59E0B).withOpacity(0.08),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: const Color(0xFFF59E0B).withOpacity(0.35)),
                      ),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text('💡', style: TextStyle(fontSize: 15)),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Text(
                                  'Tactical Verdict',
                                  style: TextStyle(
                                    color: Color(0xFFF59E0B),
                                    fontSize: 11.5,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                                const SizedBox(height: 2),
                                Text(
                                  hero.f2pAdvice,
                                  style: const TextStyle(
                                    color: Color(0xFFE2E8F0),
                                    fontSize: 12,
                                    height: 1.35,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),

                    // Expandable Details (Skills & Exclusive Gear)
                    if (_isExpanded) ...[
                      const SizedBox(height: 14),
                      const Divider(color: Colors.white12, height: 1),
                      const SizedBox(height: 12),
                      _buildSkillTile('⚡ Exploration Skill', hero.explorationSkill, primaryGlow),
                      const SizedBox(height: 8),
                      _buildSkillTile('⚔️ Expedition Skill', hero.expeditionSkill, secondaryGlow),
                      const SizedBox(height: 8),
                      _buildSkillTile('⚙️ Exclusive Gear', hero.exclusiveGear, const Color(0xFF8B5CF6)),
                    ],

                    const SizedBox(height: 8),
                    Center(
                      child: Text(
                        _isExpanded ? '▲ Tap to collapse' : '▼ Tap for skill archives & widgets',
                        style: TextStyle(
                          color: primaryGlow.withOpacity(0.7),
                          fontSize: 11,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _buildSkillTile(String title, String detail, Color accent) {
    return Container(
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: Colors.black.withOpacity(0.25),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: accent.withOpacity(0.25)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: TextStyle(
              color: accent,
              fontSize: 11.5,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 3),
          Text(
            detail,
            style: const TextStyle(
              color: Color(0xFFCBD5E1),
              fontSize: 12,
              height: 1.35,
            ),
          ),
        ],
      ),
    );
  }
}
