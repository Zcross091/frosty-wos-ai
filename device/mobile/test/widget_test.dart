import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:frosty_wos_ai/main.dart';
import 'package:frosty_wos_ai/models/chat_message.dart';
import 'package:frosty_wos_ai/models/hero_profile.dart';
import 'package:frosty_wos_ai/services/knowledge_service.dart';
import 'package:frosty_wos_ai/services/state_age_service.dart';

void main() {
  group('Frosty WOS AI Integrity Tests', () {
    test('Offline Knowledge Service contains Gen 17, Gen 16 and Core Heroes', () {
      expect(KnowledgeService.heroes.isNotEmpty, true);

      final aiden = KnowledgeService.getHeroByName('Aiden');
      expect(aiden, isNotNull);
      expect(aiden!.generation, 17);
      expect(aiden.troopType, TroopType.infantry);

      final eleanor = KnowledgeService.getHeroByName('Eleanor');
      expect(eleanor, isNotNull);
      expect(eleanor!.generation, 17);
      expect(eleanor.troopType, TroopType.marksman);

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

    test('State Age Calculator computes Generation and Timeline Milestones accurately', () {
      // Test State 1 (Oldest Server -> Gen 17)
      final state1Calc = StateAgeService.calculateFromStateNumber(1);
      expect(state1Calc.currentGeneration, 17);
      expect(state1Calc.activeHeroes.contains('Aiden (Infantry)'), true);
      expect(state1Calc.milestones.isNotEmpty, true);
      expect(state1Calc.unlockedMilestones.isNotEmpty, true);

      // Test Day 45 (Gen 2)
      final gen2Calc = StateAgeService.calculateFromDays(45);
      expect(gen2Calc.currentGeneration, 2);
      expect(gen2Calc.nextGeneration, 3);
      expect(gen2Calc.daysUntilNextGen, 75);

      // Day 45 should have Gen 1 & Gen 2 unlocked, but Fire Crystal (Day 60) upcoming
      expect(gen2Calc.unlockedMilestones.any((m) => m.day == 40), true);
      expect(gen2Calc.upcomingMilestones.any((m) => m.day == 60), true);
    });

    testWidgets('FrostyApp UI renders without runtime exceptions', (WidgetTester tester) async {
      await tester.pumpWidget(const FrostyApp());
      await tester.pump(const Duration(milliseconds: 200));

      expect(find.text('Frosty Tactical Oracle'), findsOneWidget);
    });
  });
}
