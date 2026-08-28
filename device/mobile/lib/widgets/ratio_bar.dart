import 'package:flutter/material.dart';

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
        // Legend
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            _buildLegendItem('🛡️ Infantry', '$infantry%', const Color(0xFF60A5FA)),
            _buildLegendItem('🐎 Lancer', '$lancer%', const Color(0xFFF87171)),
            _buildLegendItem('🏹 Marksman', '$marksman%', const Color(0xFF4ADE80)),
          ],
        ),
        const SizedBox(height: 10),

        // Visual Proportion Bar
        Container(
          height: 14,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(10),
            color: Colors.black.withOpacity(0.4),
          ),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(10),
            child: Row(
              children: [
                if (infantry > 0)
                  Expanded(
                    flex: infantry,
                    child: Container(
                      color: const Color(0xFF3B82F6),
                    ),
                  ),
                if (lancer > 0)
                  Expanded(
                    flex: lancer,
                    child: Container(
                      color: const Color(0xFFEF4444),
                    ),
                  ),
                if (marksman > 0)
                  Expanded(
                    flex: marksman,
                    child: Container(
                      color: const Color(0xFF22C55E),
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
    return Row(
      children: [
        Container(
          width: 8,
          height: 8,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: color,
          ),
        ),
        const SizedBox(width: 6),
        Text(
          '$label: ',
          style: const TextStyle(
            color: Color(0xFF94A3B8),
            fontSize: 12,
          ),
        ),
        Text(
          value,
          style: TextStyle(
            color: color,
            fontWeight: FontWeight.bold,
            fontSize: 12.5,
          ),
        ),
      ],
    );
  }
}
