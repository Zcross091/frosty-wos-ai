import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:frosty_wos_ai/main.dart';
import 'package:frosty_wos_ai/models/chat_message.dart';
import 'package:frosty_wos_ai/models/hero_profile.dart';
import 'package:frosty_wos_ai/services/knowledge_service.dart';
import 'package:frosty_wos_ai/services/state_age_service.dart';

void main() {
  group('Frosty WOS AI Integrity Tests', () {
    test('Offline Knowledge Service contains Gen 16 and Core Heroes', () {
      expect(KnowledgeService.heroes.isNotEmpty, true);

      final seigel = KnowledgeService.getHeroByName('Seigel');
      expect(seigel, isNotNull);
      expect(seigel!.generation, 16);
      expect(seigel.troopType, TroopType.infantry);

      final flint = KnowledgeService.getHeroByName('Flint');
      expect(flint, isNotNull);
      expect(flint!.generation, 2);

      final jessie = KnowledgeService.getHeroByName('Jessie');
      expect(jessie, isNotNull);
      expect(jessie!.generation, 0);
    });

    test('ChatMessage content and text alias integrity', () {
      final msg = ChatMessage(
        id: '1',
        content: 'Tactical advice',
        isUser: false,
        timestamp: DateTime.now(),
        modelUsed: 'Frosty Core',
      );
      expect(msg.content, 'Tactical advice');
      expect(msg.text, 'Tactical advice');
    });

    test('State Age Calculator computes Generation accurately', () {
      // Test State 1 (Oldest Server -> Gen 16)
      final state1Calc = StateAgeService.calculateFromStateNumber(1);
      expect(state1Calc.currentGeneration, 16);
      expect(state1Calc.activeHeroes.contains('Seigel (Infantry)'), true);

      // Test Day 45 (Gen 2)
      final gen2Calc = StateAgeService.calculateFromDays(45);
      expect(gen2Calc.currentGeneration, 2);
      expect(gen2Calc.nextGeneration, 3);
      expect(gen2Calc.daysUntilNextGen, 75);
    });

    testWidgets('FrostyApp UI renders without runtime exceptions', (WidgetTester tester) async {
      await tester.pumpWidget(const FrostyApp());
      await tester.pump(const Duration(milliseconds: 200));

      expect(find.text('Frosty Tactical Oracle'), findsOneWidget);
    });
  });
}
