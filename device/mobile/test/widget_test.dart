import 'package:flutter_test/flutter_test.dart';
import 'package:frosty_wos_ai/models/hero_profile.dart';
import 'package:frosty_wos_ai/models/state_calculation.dart';
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

    test('State Age Calculator computes Generation accurately', () {
      // Test State 1 (Oldest Server -> Gen 16)
      final state1Calc = StateAgeService.calculateFromStateNumber(1);
      expect(state1Calc.currentGeneration, 16);
      expect(state1Calc.activeHeroes.contains('Seigel (Infantry Shield)'), true);

      // Test Day 45 (Gen 2)
      final gen2Calc = StateAgeService.calculateFromDays(45);
      expect(gen2Calc.currentGeneration, 2);
      expect(gen2Calc.nextGeneration, 3);
      expect(gen2Calc.daysUntilNextGen, 75); // 120 - 45 = 75
    });
  });
}
