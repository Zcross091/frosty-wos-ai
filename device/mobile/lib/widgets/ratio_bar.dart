import 'package:flutter/material.dart';

/// 3D Glowing Troop Ratio Bar
class RatioBar extends StatelessWidget {
  final int infantry;
  final int lancer;
  final int marksman;

  const RatioBar({
    super.key,
    required this.infantry,
    required this.lancer,
    required this.marksman,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Legend with Glowing Neon Dots
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            _buildLegendItem('🔷 Infantry', '$infantry%', const Color(0xFF00F0FF)),
            _buildLegendItem('🔶 Lancer', '$lancer%', const Color(0xFFF59E0B)),
            _buildLegendItem('🔴 Marksman', '$marksman%', const Color(0xFFEC4899)),
          ],
        ),
        const SizedBox(height: 10),

        // Visual Proportion Bar with 3D Depth & Inset Shadow
        Container(
          height: 16,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(12),
            color: const Color(0xFF060D18),
            border: Border.all(color: Colors.white10),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.5),
                blurRadius: 6,
                offset: const Offset(0, 2),
              ),
            ],
          ),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(11),
            child: Row(
              children: [
                if (infantry > 0)
                  Expanded(
                    flex: infantry,
                    child: Container(
                      decoration: const BoxDecoration(
                        gradient: LinearGradient(
                          colors: [Color(0xFF0284C7), Color(0xFF00F0FF)],
                        ),
                      ),
                    ),
                  ),
                if (lancer > 0)
                  Expanded(
                    flex: lancer,
                    child: Container(
                      decoration: const BoxDecoration(
                        gradient: LinearGradient(
                          colors: [Color(0xFFEA580C), Color(0xFFF59E0B)],
                        ),
                      ),
                    ),
                  ),
                if (marksman > 0)
                  Expanded(
                    flex: marksman,
                    child: Container(
                      decoration: const BoxDecoration(
                        gradient: LinearGradient(
                          colors: [Color(0xFFEF4444), Color(0xFFEC4899)],
                        ),
                      ),
                    ),
                  ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildLegendItem(String label, String value, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            '$label ',
            style: const TextStyle(
              color: Color(0xFF94A3B8),
              fontSize: 11.5,
              fontWeight: FontWeight.w500,
            ),
          ),
          Text(
            value,
            style: TextStyle(
              color: color,
              fontWeight: FontWeight.bold,
              fontSize: 12,
              fontFamily: 'Outfit',
            ),
          ),
        ],
      ),
    );
  }
}
