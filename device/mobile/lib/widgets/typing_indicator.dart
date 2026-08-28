import 'package:flutter/material.dart';
import 'package:flutter_spinkit/flutter_spinkit.dart';

class FrostyTypingIndicator extends StatelessWidget {
  const FrostyTypingIndicator({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.symmetric(vertical: 8, horizontal: 16),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: const Color(0xFF0F192C),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(
          color: const Color(0xFF00F0FF).withOpacity(0.35),
          width: 1.2,
        ),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF00F0FF).withOpacity(0.12),
            blurRadius: 16,
            spreadRadius: 1,
          ),
        ],
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 28,
            height: 28,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: const Color(0xFF00D2FF).withOpacity(0.2),
              border: Border.all(color: const Color(0xFF00F0FF), width: 1),
            ),
            child: const Center(
              child: Text(
                '❄️',
                style: TextStyle(fontSize: 14),
              ),
            ),
          ),
          const SizedBox(width: 12),
          const Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                'Frosty is cooking your tactical answer...',
                style: TextStyle(
                  color: Color(0xFF00F0FF),
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                  fontFamily: 'Outfit',
                ),
              ),
              SizedBox(height: 2),
              Text(
                'Synthesizing Whiteout Survival master archives',
                style: TextStyle(
                  color: Color(0xFF94A3B8),
                  fontSize: 11,
                ),
              ),
            ],
          ),
          const SizedBox(width: 14),
          const SpinKitThreeBounce(
            color: Color(0xFF00F0FF),
            size: 14.0,
          ),
        ],
      ),
    );
  }
}
