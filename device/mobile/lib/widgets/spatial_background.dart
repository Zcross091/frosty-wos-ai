import 'package:flutter/material.dart';

/// Solid High-Performance Dark Obsidian Theme Container
class SpatialBackground extends StatelessWidget {
  final Widget child;
  const SpatialBackground({super.key, required this.child});

  @override
  Widget build(BuildContext context) {
    return Container(
      color: const Color(0xFF040812),
      child: child,
    );
  }
}
