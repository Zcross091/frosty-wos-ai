enum TroopType { infantry, lancer, marksman }

class HeroProfile {
  final String name;
  final int generation;
  final String generationLabel;
  final TroopType troopType;
  final String rarity;
  final String roleOverview;
  final int attack;
  final int defense;
  final int health;
  final double expeditionMultiplier;
  final String explorationSkill;
  final String expeditionSkill;
  final String exclusiveGear;
  final String f2pAdvice;
  final String bestTeam;

  HeroProfile({
    required this.name,
    required this.generation,
    required this.generationLabel,
    required this.troopType,
    required this.rarity,
    required this.roleOverview,
    required this.attack,
    required this.defense,
    required this.health,
    required this.expeditionMultiplier,
    required this.explorationSkill,
    required this.expeditionSkill,
    required this.exclusiveGear,
    required this.f2pAdvice,
    required this.bestTeam,
  });

  String get troopTypeString {
    switch (troopType) {
      case TroopType.infantry:
        return 'Infantry';
      case TroopType.lancer:
        return 'Lancer';
      case TroopType.marksman:
        return 'Marksman';
    }
  }

  String get troopIcon {
    switch (troopType) {
      case TroopType.infantry:
        return '🛡️';
      case TroopType.lancer:
        return '🐎';
      case TroopType.marksman:
        return '🏹';
    }
  }
}
