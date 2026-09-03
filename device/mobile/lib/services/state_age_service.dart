import '../models/state_calculation.dart';
import 'knowledge_service.dart';

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

  static final List<Map<String, dynamic>> rawMilestones = [
    {
      'day': 0,
      'title': 'Generation 1 Heroes',
      'category': 'Hero',
      'icon': '👑',
      'description': 'Natalia, Jeronimo, Molly & Zinman. Focus on Sergey (Tank) and Jessie (Rally Joiner +25% Dmg).'
    },
    {
      'day': 14,
      'title': 'Tundra Territory Opens',
      'category': 'Event',
      'icon': '🗺️',
      'description': 'Alliance territory expands to Tundra zone; high-tier resource tiles and tundra beasts unlock.'
    },
    {
      'day': 34,
      'title': 'Arena Pool Expansion',
      'category': 'Event',
      'icon': '⚔️',
      'description': 'Arena opponent pool expands across state cluster.'
    },
    {
      'day': 40,
      'title': 'Generation 2 Heroes (Flint / Alonso / Philly)',
      'category': 'Hero',
      'icon': '🔥',
      'description': 'Flint on Lucky Wheel (#1 F2P Tank), Alonso in Hall of Heroes / King of Icefield.'
    },
    {
      'day': 45,
      'title': 'Chief Gear & Charms T1',
      'category': 'Gear',
      'icon': '🛡️',
      'description': 'Polish Chief Gear to T1 and socket initial elemental charms for squad Attack and Defense.'
    },
    {
      'day': 53,
      'title': 'First Sunfire Castle Battle',
      'category': 'Event',
      'icon': '🏰',
      'description': 'First battle for Supreme Presidency, State Capital control, and ministerial titles.'
    },
    {
      'day': 54,
      'title': 'Pet System Gen 1 & Beast Cage',
      'category': 'Pet',
      'icon': '🐾',
      'description': 'Requires Furnace Lv 18. Construct Beast Cage to tame Cave Hyena, Arctic Wolf, and Musk Ox.'
    },
    {
      'day': 60,
      'title': 'Fire Crystal Age (FC 1–3)',
      'category': 'Fire Crystal',
      'icon': '💎',
      'description': 'Requires Furnace Lv 30 & Monument task. Upgrade structures and troops to Fire Crystal 1–3.'
    },
    {
      'day': 80,
      'title': 'State vs. State (SvS) & King of Icefield',
      'category': 'Event',
      'icon': '⚔️',
      'description': 'First cross-state war! 6-day preparation phase (Castle prep) followed by Battle Phase.'
    },
    {
      'day': 90,
      'title': 'Pet Generation 2 (Titan Roc & Giant Tapir)',
      'category': 'Pet',
      'icon': '🦅',
      'description': 'Unlocks Titan Roc (March Speed) and Giant Tapir (Rally Defense).'
    },
    {
      'day': 100,
      'title': 'State Transfer Phase 1',
      'category': 'Event',
      'icon': '🚀',
      'description': 'Transfer window opens to relocate to older or neighboring servers in your state bracket.'
    },
    {
      'day': 120,
      'title': 'Generation 3 Heroes (Mia / Logan / Greg)',
      'category': 'Hero',
      'icon': '🎯',
      'description': 'Mia on Lucky Wheel (#1 Bear Trap carry), Logan arena and garrison defender.'
    },
    {
      'day': 140,
      'title': 'Pet Generation 3 (Snow Leopard & Giant Elk)',
      'category': 'Pet',
      'icon': '🐆',
      'description': 'Unlocks Snow Leopard (Backline Lethality) and Giant Elk (Resource Gathering).'
    },
    {
      'day': 150,
      'title': 'Fire Crystal 4–5 & Crystal Laboratory',
      'category': 'Fire Crystal',
      'icon': '🔮',
      'description': 'Refine Fire Crystals into Refined Crystals for FC 4 and FC 5 upgrades.'
    },
    {
      'day': 180,
      'title': 'Generation 4 Heroes (Lynn / Ahmose / Reina)',
      'category': 'Hero',
      'icon': '🏹',
      'description': 'Lynn on Lucky Wheel (armor-piercing marksman), Ahmose frontline invincibility tank.'
    },
    {
      'day': 200,
      'title': 'Pet Generation 4 (Cave Lion & Snow Ape)',
      'category': 'Pet',
      'icon': '🦁',
      'description': 'Unlocks Cave Lion (Squad Stun) and Snow Ape (Frontline damage mitigation).'
    },
    {
      'day': 220,
      'title': 'War Academy & T11 Troops',
      'category': 'Academy',
      'icon': '🏛️',
      'description': 'Dawn / War Academy research unlocks. Train elite Tier 11 Infantry, Lancers, and Marksmen.'
    },
    {
      'day': 250,
      'title': 'Generation 5 Heroes (Hector / Norah / Gwen)',
      'category': 'Hero',
      'icon': '🛡️',
      'description': 'Hector on Lucky Wheel (top fortress tank), Norah lancer flanker, Gwen sniper.'
    },
    {
      'day': 280,
      'title': 'Pet Generation 5 (Iron Rhino & Saber-tooth)',
      'category': 'Pet',
      'icon': '🦏',
      'description': 'Unlocks Iron Rhino (Defense surge) and Saber-tooth (Critical strike power).'
    },
    {
      'day': 300,
      'title': 'Fire Crystal 6–8 Age',
      'category': 'Fire Crystal',
      'icon': '💎',
      'description': 'Massive health scaling and combat stat multipliers for FC 6, 7, and 8.'
    },
    {
      'day': 320,
      'title': 'Generation 6 Heroes (Renee / Wayne / Wu Ming)',
      'category': 'Hero',
      'icon': '⚔️',
      'description': 'Renee on Lucky Wheel (marksman carry), Wayne garrison defender.'
    },
    {
      'day': 360,
      'title': 'Pet Generation 6 (Titan Beaver & Gorgon Viper)',
      'category': 'Pet',
      'icon': '🐍',
      'description': 'Unlocks Titan Beaver (Rapid healing) and Gorgon Viper (Toxic rally debuffs).'
    },
    {
      'day': 400,
      'title': 'Generation 7 Heroes (Bradley / Edith / Gordon)',
      'category': 'Hero',
      'icon': '🎯',
      'description': 'Bradley on Lucky Wheel (premier fortress stun lead), Edith backline assassin.'
    },
    {
      'day': 450,
      'title': 'Chief Gear T4 & Legendary Charms',
      'category': 'Gear',
      'icon': '👑',
      'description': 'Apex Chief Gear tier granting massive squad Lethality and Damage Reduction.'
    },
    {
      'day': 480,
      'title': 'Generation 8 Heroes & Pet Gen 7',
      'category': 'Hero',
      'icon': '🛡️',
      'description': 'Hendrik (Lucky Wheel), Gatot + Frostscale Chameleon (Evasion shield).'
    },
    {
      'day': 500,
      'title': 'Fire Crystal 9–10 Age',
      'category': 'Fire Crystal',
      'icon': '🔮',
      'description': 'Refined Crystal economy expansion; structure and unit mastery for FC 9 and FC 10.'
    },
    {
      'day': 550,
      'title': 'Generation 9 Heroes (Magnus / Fred / Xura)',
      'category': 'Hero',
      'icon': '⚔️',
      'description': 'Magnus on Lucky Wheel, Fred lancer flanking DPS, Xura marksman.'
    },
    {
      'day': 620,
      'title': 'Generation 10 Heroes (Blanchette / Gregory / Freya)',
      'category': 'Hero',
      'icon': '🏹',
      'description': 'Blanchette on Lucky Wheel (premier PvE carry), Gregory troop HP buffer.'
    },
    {
      'day': 690,
      'title': 'Generation 11 Heroes (Eleonora / Lloyd / Rufus)',
      'category': 'Hero',
      'icon': '🛡️',
      'description': 'Eleonora on Lucky Wheel, Rufus heavy armor shredder.'
    },
    {
      'day': 750,
      'title': 'Fire Crystal 11–12 & T12 Troops',
      'category': 'Fire Crystal',
      'icon': '⚡',
      'description': 'Supreme Tier 12 troops and Apex Fire Crystal mastery.'
    },
    {
      'day': 760,
      'title': 'Generation 12 Heroes (Ligeia / Hervor / Karol)',
      'category': 'Hero',
      'icon': '🎯',
      'description': 'Ligeia on Lucky Wheel (Bear Trap top carry), Hervor rally anchor.'
    },
    {
      'day': 830,
      'title': 'Generation 13 Heroes (Gisela / Flora / Vulcanus)',
      'category': 'Hero',
      'icon': '🛡️',
      'description': 'Gisela on Lucky Wheel, Vulcanus explosive burst.'
    },
    {
      'day': 900,
      'title': 'Generation 14 Heroes (Cara / Elif / Dominic)',
      'category': 'Hero',
      'icon': '🏹',
      'description': 'Cara on Lucky Wheel, Elif defense wall.'
    },
    {
      'day': 960,
      'title': 'Generation 15 Heroes (Hank / Estrella / Viveca)',
      'category': 'Hero',
      'icon': '👑',
      'description': 'Hank on Lucky Wheel tank, Viveca marksman.'
    },
    {
      'day': 1160,
      'title': 'Generation 16 Heroes (Seigel / Ursar / Aisling)',
      'category': 'Hero',
      'icon': '🛡️',
      'description': 'Seigel (Kinetic Reflect), Aisling (High Velocity Sniper), Ursar (HoH Lancer).'
    },
    {
      'day': 1240,
      'title': 'Generation 17 Heroes (Aiden / Bertha / Eleanor)',
      'category': 'Hero',
      'icon': '⚡',
      'description': 'Aiden (Lucky Wheel Rage battery), Eleanor (HoH 45% Armor Shred), Bertha (Healer).'
    },
  ];

  /// Calculates State Age and Generation from a State Number (1 - 1500+)
  static StateCalculation calculateFromStateNumber(int stateNumber) {
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
    int maxGen = 17;
    final availableGens = KnowledgeService.getAvailableGenerations();
    if (availableGens.isNotEmpty && availableGens.first > maxGen) {
      maxGen = availableGens.first;
    }

    int getUnlockDay(int gen) {
      if (generationUnlockDays.containsKey(gen)) {
        return generationUnlockDays[gen]!;
      }
      return 1240 + (gen - 17) * 80;
    }

    int currentGen = 1;
    for (int gen = maxGen; gen >= 1; gen--) {
      int unlockDay = getUnlockDay(gen);
      if (ageInDays >= unlockDay) {
        currentGen = gen;
        break;
      }
    }

    int? nextGen = currentGen < maxGen ? currentGen + 1 : null;
    int? daysUntilNextGen;
    DateTime? nextGenDate;

    if (nextGen != null) {
      int nextUnlockDay = getUnlockDay(nextGen);
      daysUntilNextGen = (nextUnlockDay - ageInDays).clamp(0, 999);
      nextGenDate = DateTime.now().add(Duration(days: daysUntilNextGen));
    }

    List<String> activeHeroes = generationHeroes[currentGen] ?? [];
    if (activeHeroes.isEmpty) {
      final genHeroes = KnowledgeService.getHeroesByGeneration(currentGen);
      if (genHeroes.isNotEmpty) {
        activeHeroes = genHeroes
            .map((h) => '${h.name} (${h.troopType.name.substring(0, 1).toUpperCase()}${h.troopType.name.substring(1, 3)})')
            .toList();
      }
    }

    // Build Milestones list
    final List<StateMilestone> milestones = rawMilestones.map((raw) {
      final int targetDay = raw['day'] as int;
      final bool isUnlocked = ageInDays >= targetDay;
      final int remaining = (targetDay - ageInDays).clamp(0, 9999);
      return StateMilestone(
        day: targetDay,
        title: raw['title'] as String,
        category: raw['category'] as String,
        icon: raw['icon'] as String,
        description: raw['description'] as String,
        isUnlocked: isUnlocked,
        daysRemaining: remaining,
      );
    }).toList();

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
    } else if (currentGen == 17) {
      tacticalAdvice = 'GENERATION 17 ACTIVE (Apex 2,450% Multipliers). Aiden (Kinetic Aegis) & Eleanor (Armor Shred) dominate the meta.';
      roadmap = [
        'Aiden (Infantry): Spin Lucky Wheel to 4★ minimum for +25% squad Rage & 35% shield.',
        'Eleanor (Marksman): Spend all weekly Marks of Valor in Hall of Heroes to strip 45% enemy defense.',
        'Bertha (Lancer): Acquire via King of Icefield / Daily Deals for 8% periodic squad healing.',
        'Apex Formation: 50/20/30 Aiden (Lead) + Bertha + Eleanor.'
      ];
    } else {
      tacticalAdvice = 'GENERATION $currentGen ACTIVE. High-tier endgame scaling active. Maximize Lucky Wheel and Hall of Heroes.';
      roadmap = activeHeroes.isNotEmpty
          ? activeHeroes.map((h) => '$h: Core meta hero. Build to 4★ minimum with exclusive gear.').toList()
          : [
              'Build current Gen $currentGen Lucky Wheel carry hero.',
              'Spend weekly Marks of Valor in Hall of Heroes.',
              'Maintain 50/20/30 PvP troop ratios in all marches.'
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
      milestones: milestones,
    );
  }
}
