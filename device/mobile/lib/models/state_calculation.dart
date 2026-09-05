class StateMilestone {
  final int day;
  final String title;
  final String category; // 'Hero', 'Fire Crystal', 'Pet', 'Event', 'Gear', 'Academy'
  final String icon;
  final String description;
  final bool isUnlocked;
  final int daysRemaining;

  const StateMilestone({
    required this.day,
    required this.title,
    required this.category,
    required this.icon,
    required this.description,
    required this.isUnlocked,
    required this.daysRemaining,
  });
}

class StateCalculation {
  final int? stateNumber;
  final int ageInDays;
  final DateTime? estimatedLaunchDate;
  final int currentGeneration;
  final String currentGenLabel;
  final List<String> activeHeroes;
  final int? nextGeneration;
  final int? daysUntilNextGen;
  final DateTime? estimatedNextGenDate;
  final String tacticalAdvice;
  final List<String> heroBuildRoadmap;
  final List<StateMilestone> milestones;

  const StateCalculation({
    this.stateNumber,
    required this.ageInDays,
    this.estimatedLaunchDate,
    required this.currentGeneration,
    required this.currentGenLabel,
    required this.activeHeroes,
    this.nextGeneration,
    this.daysUntilNextGen,
    this.estimatedNextGenDate,
    required this.tacticalAdvice,
    required this.heroBuildRoadmap,
    this.milestones = const [],
  });

  List<StateMilestone> get unlockedMilestones => milestones.where((m) => m.isUnlocked).toList();
  List<StateMilestone> get upcomingMilestones => milestones.where((m) => !m.isUnlocked).toList();
}
