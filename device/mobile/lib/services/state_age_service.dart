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
  };

  static final Map<int, List<String>> generationHeroes = {
    1: ['Jeronimo (Inf)', 'Natalia (Lan)', 'Molly (Mark)', 'Zinman (Mark)'],
    2: ['Flint (Inf)', 'Philly (Lan)', 'Alonso (Mark)'],
    3: ['Logan (Inf)', 'Greg (Lan)', 'Mia (Mark)'],
    4: ['Ahmose (Inf)', 'Reina (Lan)', 'Lynn (Mark)'],
    5: ['Hector (Inf)', 'Norah (Lan)', 'Gwen (Mark)'],
    6: ['Wayne (Inf)', 'Wu Ming (Lan)', 'Renee (Mark)'],
    7: ['Bradley (Inf)', 'Gordon (Lan)', 'Edith (Mark)'],
    8: ['Gatot (Inf)', 'Sonya (Lan)', 'Hendrik (Mark)'],
    9: ['Magnus (Inf)', 'Fred (Lan)', 'Xura (Mark)'],
    10: ['Gregory (Inf)', 'Freya (Lan)', 'Blanchette (Mark)'],
    11: ['Eleonora (Inf)', 'Lloyd (Lan)', 'Rufus (Mark)'],
    12: ['Hervor (Inf)', 'Karol (Lan)', 'Ligeia (Mark)'],
    13: ['Gisela (Inf)', 'Flora (Lan)', 'Vulcanus (Mark)'],
    14: ['Elif (Inf)', 'Dominic (Lan)', 'Cara (Mark)'],
    15: ['Hank (Inf)', 'Estrella (Lan)', 'Viveca (Mark)'],
    16: ['Seigel (Infantry)', 'Ursar (Lancer)', 'Aisling (Marksman)'],
  };

  /// Calculates State Age and Generation from a State Number (1 - 1500+)
  static StateCalculation calculateFromStateNumber(int stateNumber) {
    // Estimating state launch date based on state numbering pace
    // Older states (1-200) opened ~3 days apart; newer states opened ~0.8 days apart
    double daysAgo;
    if (stateNumber <= 100) {
      daysAgo = 1300 - (stateNumber * 2.5);
    } else if (stateNumber <= 500) {
      daysAgo = 1050 - ((stateNumber - 100) * 1.5);
    } else if (stateNumber <= 1000) {
      daysAgo = 450 - ((stateNumber - 500) * 0.7);
    } else {
      daysAgo = 100 - ((stateNumber - 1000) * 0.4);
    }

    int ageInDays = daysAgo.round().clamp(1, 1400);
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
    return _buildCalculation(ageInDays: days.clamp(0, 2000));
  }

  static StateCalculation _buildCalculation({required int ageInDays, int? stateNumber}) {
    int currentGen = 1;
    for (int gen = 16; gen >= 1; gen--) {
      int unlockDay = generationUnlockDays[gen] ?? 0;
      if (ageInDays >= unlockDay) {
        currentGen = gen;
        break;
      }
    }

    int? nextGen = currentGen < 16 ? currentGen + 1 : null;
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
      tacticalAdvice = 'Max out Flint on Lucky Wheel. Alonso is top exploration marksman. Start saving for Gen 3 Mia.';
      roadmap = [
        'Build Flint to 3-4★ on Lucky Wheel.',
        'Pair Flint + Alonso + Philly for top PvP marches.',
        'Keep Jessie ready as #1 joiner lead for Bear Trap (+25% Damage).'
      ];
    } else if (currentGen <= 6) {
      tacticalAdvice = 'Maintain 50/20/30 PvP troop ratios. Prioritize marksman carries (Lynn/Gwen) on the Lucky Wheel.';
      roadmap = [
        'Focus mythic general shards on the primary Lucky Wheel damage dealer.',
        'Ensure castle garrison has at least 50% Infantry to absorb rally burst.',
        'Check next generation countdown to avoid wasting generic shards right before a generation shift.'
      ];
    } else if (currentGen == 7) {
      tacticalAdvice = 'Bradley & Edith represent the biggest PvP combat power spike. Bradley is top frontline stun tank.';
      roadmap = [
        'Invest generic mythic shards in Bradley until 4★ with Exclusive Gear.',
        'Edith deals lethal armor-piercing damage directly to enemy backlines.',
        'Ideal Squad: Bradley (Lead) + Edith + Gordon/Hector.'
      ];
    } else if (currentGen < 16) {
      tacticalAdvice = 'Endgame stat scaling is active. Focus on exclusive gear level 6+ and Dawn Academy experts.';
      roadmap = [
        'Prioritize current generation Lucky Wheel banner hero.',
        'Upgrade Dawn Academy Experts (Agnes/Cyrille/Holger) for troop stat multipliers.',
        'Always send Jessie as joiner 1 in Bear Trap (+25% damage buff).'
      ];
    } else {
      tacticalAdvice = 'GENERATION 16 ACTIVE (Maximum Scaling: +2,131.70% Expedition Stats). Seigel is the invincible reflect tank.';
      roadmap = [
        'Seigel (Infantry): Reflects 25% damage and heals via Blacklight Halberd.',
        'Aisling (Marksman): Highest siege lethal multiplier in game history.',
        'Ursar (Lancer): Hall of Heroes Marks of Valor exclusive support.',
        'Rally Formation: 10/10/80 for Bear Trap, 50/20/30 for PvP SvS battles.'
      ];
    }

    return StateCalculation(
      stateNumber: stateNumber,
      ageInDays: ageInDays,
      currentGeneration: currentGen,
      currentGenLabel: 'Generation $currentGen (${currentGen == 16 ? 'Endgame Legendary' : 'Active'})',
      activeHeroes: activeHeroes,
      nextGeneration: nextGen,
      daysUntilNextGen: daysUntilNextGen,
      estimatedNextGenDate: nextGenDate,
      tacticalAdvice: tacticalAdvice,
      heroBuildRoadmap: roadmap,
    );
  }
}
