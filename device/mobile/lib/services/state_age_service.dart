import '../models/state_calculation.dart';

class StateAgeService {
  // Estimated base launch reference for Whiteout Survival State 1 (approx Feb 14, 2023)
  static final DateTime state1LaunchDate = DateTime(2023, 2, 14);

  // Generation Day Milestones
  static final Map<int, int> generationUnlockDays = {
    1: 0,
    2: 40,
    3: 120,
    4: 180,
    5: 250,
    6: 320,
    7: 400,
    8: 480,
    9: 560,
    10: 640,
    11: 720,
    12: 800,
    13: 880,
    14: 960,
    15: 1040,
    16: 1160,
    17: 1240,
  };

  static final Map<int, List<String>> generationHeroes = {
    1: ['Jeronimo (Inf)', 'Natalia (Lan)', 'Molly (Mark)', 'Zinman (Mark)'],
    2: ['Flint (Inf)', 'Philly (Lan)', 'Alonso (Mark)'],
    3: ['Logan (Inf)', 'Greg (Lan)', 'Mia (Mark)'],
    4: ['Ahmose (Inf)', 'Reina (Lan)', 'Lynn (Mark)'],
    5: ['Hector (Inf)', 'Norah (Lan)', 'Gwen (Mark)'],
    6: ['Wayne (Inf)', 'Wu Ming (Lan)', 'Renee (Mark)'],
    7: ['Edith (Inf)', 'Gordon (Lan)', 'Bradley (Mark)'],
    8: ['Gatot (Inf)', 'Sonya (Lan)', 'Hendrik (Mark)'],
    9: ['Magnus (Inf)', 'Fred (Lan)', 'Xura (Mark)'],
    10: ['Gregory (Inf)', 'Freya (Lan)', 'Blanchette (Mark)'],
    11: ['Eleonora (Inf)', 'Lloyd (Lan)', 'Rufus (Mark)'],
    12: ['Hervor (Inf)', 'Karol (Lan)', 'Ligeia (Mark)'],
    13: ['Gisela (Inf)', 'Flora (Lan)', 'Vulcanus (Mark)'],
    14: ['Elif (Inf)', 'Dominic (Lan)', 'Cara (Mark)'],
    15: ['Hank (Inf)', 'Estrella (Lan)', 'Viveca (Mark)'],
    16: ['Seigel (Infantry)', 'Ursar (Lancer)', 'Aisling (Marksman)'],
    17: ['Aiden (Infantry)', 'Bertha (Lancer)', 'Eleanor (Marksman)'],
  };

  /// Calculates State Age and Generation from a State Number (1 - 1500+)
  static StateCalculation calculateFromStateNumber(int stateNumber) {
    // Estimating state launch date based on state numbering pace
    // Older states (1-200) opened ~3 days apart; newer states opened ~0.8 days apart
    double daysAgo;
    if (stateNumber <= 100) {
      daysAgo = 1350 - (stateNumber * 2.5);
    } else if (stateNumber <= 500) {
      daysAgo = 1100 - ((stateNumber - 100) * 1.5);
    } else if (stateNumber <= 1000) {
      daysAgo = 500 - ((stateNumber - 500) * 0.7);
    } else {
      daysAgo = 150 - ((stateNumber - 1000) * 0.4);
    }

    int ageInDays = daysAgo.round().clamp(1, 1600);
    return _buildCalculation(ageInDays: ageInDays, stateNumber: stateNumber);
  }

  /// Calculates State Age and Generation from an exact server start date
  static StateCalculation calculateFromDate(DateTime startDate) {
    int ageInDays = DateTime.now().difference(startDate).inDays;
    if (ageInDays < 0) ageInDays = 0;
    return _buildCalculation(ageInDays: ageInDays);
  }

  /// Calculates State Age from direct day count input
  static StateCalculation calculateFromDays(int days) {
    return _buildCalculation(ageInDays: days.clamp(0, 2500));
  }

  static StateCalculation _buildCalculation({required int ageInDays, int? stateNumber}) {
    int currentGen = 1;
    for (int gen = 17; gen >= 1; gen--) {
      int unlockDay = generationUnlockDays[gen] ?? 0;
      if (ageInDays >= unlockDay) {
        currentGen = gen;
        break;
      }
    }

    int? nextGen = currentGen < 17 ? currentGen + 1 : null;
    int? daysUntilNextGen;
    DateTime? nextGenDate;

    if (nextGen != null) {
      int nextUnlockDay = generationUnlockDays[nextGen] ?? 0;
      daysUntilNextGen = (nextUnlockDay - ageInDays).clamp(0, 999);
      nextGenDate = DateTime.now().add(Duration(days: daysUntilNextGen));
    }

    List<String> activeHeroes = generationHeroes[currentGen] ?? [];

    // Tactical shard advice
    String tacticalAdvice;
    List<String> roadmap = [];

    if (currentGen == 1) {
      tacticalAdvice = 'Hoard General Mythic shards for Gen 2 Lucky Wheel (Flint). Do not over-invest in Molly or Zinman.';
      roadmap = [
        'Save at least 150-200 Lucky Wheel spins for Gen 2 (Day ~40).',
        'Use Sergey as main defense tank and Jessie as primary rally joiner lead.',
        'Target 3★ Flint when Gen 2 arrives for massive frontline spike.'
      ];
    } else if (currentGen == 2) {
      tacticalAdvice = 'Gen 2 Active. Flint is the essential F2P infantry tank via Lucky Wheel. Alonso shines in Arena.';
      roadmap = [
        'Spin Lucky Wheel for Flint until at least 3-4★.',
        'Obtain Alonso from Hall of Heroes / King of Icefield.',
        'Use Jessie + Flint + Alonso as top Bear Trap lead squad.'
      ];
    } else if (currentGen == 3) {
      tacticalAdvice = 'Gen 3 Active. Mia (Lucky Wheel) is an absolute must-have for Bear Trap and backline AoE stun.';
      roadmap = [
        'Max Mia from Lucky Wheel milestones.',
        'Logan offers heavy garrison defense.',
        'Save generic shards for Gen 4 Lynn if you are F2P.'
      ];
    } else if (currentGen == 4) {
      tacticalAdvice = 'Gen 4 Active. Lynn (Marksman) dominates Lucky Wheel and brings heavy armor penetration.';
      roadmap = [
        'Invest Lucky Wheel tokens into Lynn.',
        'Ahmose provides elite frontline damage reduction.',
        'Transition your PvP marches to 50/20/30 ratios.'
      ];
    } else if (currentGen < 16) {
      tacticalAdvice = 'Endgame stat scaling is active. Focus on exclusive gear level 6+ and Dawn Academy experts.';
      roadmap = [
        'Prioritize current generation Lucky Wheel banner hero.',
        'Upgrade Dawn Academy Experts (Agnes/Cyrille/Holger) for troop stat multipliers.',
        'Always send Jessie as joiner 1 in Bear Trap (+25% damage buff).'
      ];
    } else if (currentGen == 16) {
      tacticalAdvice = 'GENERATION 16 ACTIVE (Maximum Scaling: +2,131.70% Expedition Stats). Seigel is the invincible reflect tank.';
      roadmap = [
        'Seigel (Infantry): Reflects 25% damage and heals via Blacklight Halberd.',
        'Aisling (Marksman): Highest siege lethal multiplier in game history.',
        'Ursar (Lancer): Hall of Heroes Marks of Valor exclusive support.',
        'Prepare shards and Lucky Wheel spins for Gen 17 Aiden (Day 1240+).'
      ];
    } else {
      tacticalAdvice = 'GENERATION 17 ACTIVE (Apex 2,450% Multipliers). Aiden (Kinetic Aegis) & Eleanor (Armor Shred) dominate the meta.';
      roadmap = [
        'Aiden (Infantry): Spin Lucky Wheel to 4★ minimum for +25% squad Rage & 35% shield.',
        'Eleanor (Marksman): Spend all weekly Marks of Valor in Hall of Heroes to strip 45% enemy defense.',
        'Bertha (Lancer): Acquire via King of Icefield / Daily Deals for 8% periodic squad healing.',
        'Apex Formation: 50/20/30 Aiden (Lead) + Bertha + Eleanor.'
      ];
    }

    return StateCalculation(
      stateNumber: stateNumber,
      ageInDays: ageInDays,
      currentGeneration: currentGen,
      currentGenLabel: 'Generation $currentGen (${currentGen >= 16 ? 'Endgame Legendary' : 'Active'})',
      activeHeroes: activeHeroes,
      nextGeneration: nextGen,
      daysUntilNextGen: daysUntilNextGen,
      estimatedNextGenDate: nextGenDate,
      tacticalAdvice: tacticalAdvice,
      heroBuildRoadmap: roadmap,
    );
  }
}
