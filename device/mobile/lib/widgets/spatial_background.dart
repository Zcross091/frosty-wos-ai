import 'dart:math';
import 'package:flutter/material.dart';

/// High-Performance 60 FPS Spatial Background
/// Features floating ice shards, luminous ambient glow orbs, and glassmorphic depth.
class SpatialBackground extends StatefulWidget {
  final Widget child;
  const SpatialBackground({super.key, required this.child});

  @override
  State<SpatialBackground> createState() => _SpatialBackgroundState();
}

class _SpatialBackgroundState extends State<SpatialBackground>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  final List<_FrostParticle> _particles = [];
  final Random _random = Random();

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 15),
    )..repeat();

    // Initialize 24 ambient frost particles
    for (int i = 0; i < 24; i++) {
      _particles.add(_FrostParticle(
        x: _random.nextDouble(),
        y: _random.nextDouble(),
        radius: _random.nextDouble() * 2.2 + 1.0,
        speed: _random.nextDouble() * 0.06 + 0.02,
        opacity: _random.nextDouble() * 0.45 + 0.15,
        rotation: _random.nextDouble() * 2 * pi,
        rotationSpeed: (_random.nextDouble() - 0.5) * 0.02,
      ));
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Stack(
      fit: StackFit.expand,
      children: [
        // 1. Solid Obsidian Background Base
        const Positioned.fill(
          child: ColoredBox(color: Color(0xFF040812)),
        ),

        // 2. Luminous Radial Depth
        Positioned.fill(
          child: Container(
            decoration: const BoxDecoration(
              gradient: RadialGradient(
                center: Alignment(0, -0.3),
                radius: 1.2,
                colors: [
                  Color(0xFF0D1C34), // Rich Ice Navy
                  Color(0xFF060B14), // Obsidian Slate
                  Color(0xFF03060B), // Pitch Void
                ],
                stops: [0.0, 0.6, 1.0],
              ),
            ),
          ),
        ),

        // 3. Ambient Floating Glowing Orbs
        Positioned(
          top: -60,
          right: -40,
          child: IgnorePointer(
            child: Container(
              width: 240,
              height: 240,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: RadialGradient(
                  colors: [
                    const Color(0xFF00F0FF).withOpacity(0.18),
                    const Color(0xFF0088FF).withOpacity(0.05),
                    Colors.transparent,
                  ],
                ),
              ),
            ),
          ),
        ),
        Positioned(
          bottom: 120,
          left: -60,
          child: IgnorePointer(
            child: Container(
              width: 260,
              height: 260,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: RadialGradient(
                  colors: [
                    const Color(0xFF8B5CF6).withOpacity(0.14),
                    const Color(0xFFEC4899).withOpacity(0.04),
                    Colors.transparent,
                  ],
                ),
              ),
            ),
          ),
        ),

        // 4. Animated Frost Particle Canvas
        Positioned.fill(
          child: IgnorePointer(
            child: AnimatedBuilder(
              animation: _controller,
              builder: (context, _) {
                return CustomPaint(
                  size: Size.infinite,
                  painter: _FrostParticlePainter(particles: _particles, progress: _controller.value),
                );
              },
            ),
          ),
        ),

        // 5. Content Layer
        Positioned.fill(
          child: widget.child,
        ),
      ],
    );
  }
}

class _FrostParticle {
  double x;
  double y;
  final double radius;
  final double speed;
  final double opacity;
  double rotation;
  final double rotationSpeed;

  _FrostParticle({
    required this.x,
    required this.y,
    required this.radius,
    required this.speed,
    required this.opacity,
    required this.rotation,
    required this.rotationSpeed,
  });
}

class _FrostParticlePainter extends CustomPainter {
  final List<_FrostParticle> particles;
  final double progress;

  _FrostParticlePainter({required this.particles, required this.progress});

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..style = PaintingStyle.fill
      ..isAntiAlias = true;

    for (final p in particles) {
      p.y -= p.speed * 0.008;
      if (p.y < -0.05) p.y = 1.05;
      p.rotation += p.rotationSpeed;

      final dx = p.x * size.width;
      final dy = p.y * size.height;

      paint.color = const Color(0xFF00F0FF).withOpacity(p.opacity);

      // Draw Diamond Shard
      canvas.save();
      canvas.translate(dx, dy);
      canvas.rotate(p.rotation);

      final path = Path()
        ..moveTo(0, -p.radius * 2.5)
        ..lineTo(p.radius * 1.5, 0)
        ..lineTo(0, p.radius * 2.5)
        ..lineTo(-p.radius * 1.5, 0)
        ..close();

      canvas.drawPath(path, paint);
      canvas.restore();
    }
  }

  @override
  bool shouldRepaint(covariant _FrostParticlePainter oldDelegate) => true;
}
