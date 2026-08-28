class StateCalculation {
  final int? stateNumber;
  final int ageInDays;
  final int currentGeneration;
  final String currentGenLabel;
  final List<String> activeHeroes;
  final int? nextGeneration;
  final int? daysUntilNextGen;
  final DateTime? estimatedNextGenDate;
  final String tacticalAdvice;
  final List<String> heroBuildRoadmap;

  StateCalculation({
    this.stateNumber,
    required this.ageInDays,
    required this.currentGeneration,
    required this.currentGenLabel,
    required this.activeHeroes,
    this.nextGeneration,
    this.daysUntilNextGen,
    this.estimatedNextGenDate,
    required this.tacticalAdvice,
    required this.heroBuildRoadmap,
  });
}
