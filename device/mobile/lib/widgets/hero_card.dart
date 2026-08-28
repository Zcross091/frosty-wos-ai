import 'package:flutter/material.dart';
import '../models/hero_profile.dart';

class HeroCard extends StatelessWidget {
  final HeroProfile hero;

  const HeroCard({super.key, required this.hero});

  @override
  Widget build(BuildContext context) {
    Color typeColor;
    switch (hero.troopType) {
      case TroopType.infantry:
        typeColor = const Color(0xFF60A5FA); // Blue
        break;
      case TroopType.lancer:
        typeColor = const Color(0xFFF87171); // Red
        break;
      case TroopType.marksman:
        typeColor = const Color(0xFF4ADE80); // Green
        break;
    }

    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(
        color: const Color(0xFF0F192C).withOpacity(0.85),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(
          color: const Color(0xFF38BDF8).withOpacity(0.2),
          width: 1,
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.4),
            blurRadius: 16,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header
            Row(
              mainAxisAlignment: MainAxisAlignment.between,
              children: [
                Row(
                  children: [
                    Text(
                      hero.troopIcon,
                      style: const TextStyle(fontSize: 22),
                    ),
                    const SizedBox(width: 10),
                    Text(
                      hero.name,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                        fontFamily: 'Outfit',
                      ),
                    ),
                  ],
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: typeColor.withOpacity(0.15),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: typeColor.withOpacity(0.5)),
                  ),
                  child: Text(
                    hero.troopTypeString.toUpperCase(),
                    style: TextStyle(
                      color: typeColor,
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 0.8,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 4),
            Text(
              '${hero.generationLabel} • ${hero.rarity}',
              style: const TextStyle(
                color: Color(0xFF94A3B8),
                fontSize: 13,
                fontWeight: FontWeight.w500,
              ),
            ),
            const SizedBox(height: 12),

            // Role Overview
            Text(
              hero.roleOverview,
              style: const TextStyle(
                color: Color(0xFFE2E8F0),
                fontSize: 13.5,
                height: 1.4,
              ),
            ),
            const SizedBox(height: 14),

            // Stat Multiplier Chip
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              decoration: BoxDecoration(
                color: const Color(0xFF00F0FF).withOpacity(0.08),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: const Color(0xFF00F0FF).withOpacity(0.25)),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text(
                    'Expedition Multiplier',
                    style: TextStyle(color: Color(0xFF94A3B8), fontSize: 12),
                  ),
                  Text(
                    '+${hero.expeditionMultiplier.toStringAsFixed(2)}%',
                    style: const TextStyle(
                      color: Color(0xFF00F0FF),
                      fontSize: 13,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 12),

            // Key Skills
            _buildSkillSection('⚡ Exploration Skill', hero.explorationSkill),
            const SizedBox(height: 6),
            _buildSkillSection('⚔️ Expedition Skill', hero.expeditionSkill),
            const SizedBox(height: 6),
            _buildSkillSection('⚙️ Exclusive Gear', hero.exclusiveGear),
            const SizedBox(height: 10),

            // F2P vs P2W Advice Box
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.black.withOpacity(0.3),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: const Color(0xFFF1C40F).withOpacity(0.3)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    '💡 Investment Verdict',
                    style: TextStyle(
                      color: Color(0xFFF1C40F),
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    hero.f2pAdvice,
                    style: const TextStyle(
                      color: Color(0xFFE2E8F0),
                      fontSize: 12.5,
                      height: 1.35,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSkillSection(String label, String detail) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: const TextStyle(
            color: Color(0xFF38BDF8),
            fontSize: 11.5,
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 2),
        Text(
          detail,
          style: const TextStyle(
            color: Color(0xFFCBD5E1),
            fontSize: 12,
            height: 1.3,
          ),
        ),
      ],
    );
  }
}
