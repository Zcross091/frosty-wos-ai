import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../models/state_calculation.dart';
import '../services/state_age_service.dart';

class StateAgeScreen extends StatefulWidget {
  const StateAgeScreen({super.key});

  @override
  State<StateAgeScreen> createState() => _StateAgeScreenState();
}

class _StateAgeScreenState extends State<StateAgeScreen> {
  final TextEditingController _stateInputController = TextEditingController(text: '750');
  StateCalculation? _calculation;
  int _selectedMode = 0; // 0 = By State Number, 1 = By Days, 2 = By Date
  String _timelineFilter = 'All'; // 'All', 'Upcoming', 'Unlocked', 'Fire Crystal', 'Pet', 'Hero', 'Event'

  @override
  void initState() {
    super.initState();
    _recalculate();
  }

  @override
  void dispose() {
    _stateInputController.dispose();
    super.dispose();
  }

  void _recalculate() {
    final text = _stateInputController.text.trim();
    final val = int.tryParse(text) ?? 500;

    setState(() {
      if (_selectedMode == 0) {
        _calculation = StateAgeService.calculateFromStateNumber(val);
      } else {
        _calculation = StateAgeService.calculateFromDays(val);
      }
    });
  }

  Future<void> _pickDate() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: DateTime.now().subtract(const Duration(days: 300)),
      firstDate: DateTime(2023, 1, 1),
      lastDate: DateTime.now(),
      builder: (context, child) {
        return Theme(
          data: ThemeData.dark().copyWith(
            colorScheme: const ColorScheme.dark(
              primary: Color(0xFF00F0FF),
              onPrimary: Color(0xFF040914),
              surface: Color(0xFF0F192C),
              onSurface: Colors.white,
            ),
          ),
          child: child!,
        );
      },
    );

    if (picked != null) {
      setState(() {
        _selectedMode = 2;
        _calculation = StateAgeService.calculateFromDate(picked);
        _stateInputController.text = _calculation!.ageInDays.toString();
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF040812),
      appBar: AppBar(
        backgroundColor: const Color(0xFF070D18),
        elevation: 0,
        title: const Row(
          children: [
            Text('⏱️ ', style: TextStyle(fontSize: 18)),
            Text(
              'State Timeline & Server Age',
              style: TextStyle(
                fontFamily: 'Outfit',
                fontWeight: FontWeight.bold,
                fontSize: 18,
                color: Colors.white,
                letterSpacing: 0.3,
              ),
            ),
          ],
        ),
      ),
      body: Container(
        color: const Color(0xFF040812),
        child: SingleChildScrollView(
          physics: const BouncingScrollPhysics(),
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Mode Selector
              Container(
                padding: const EdgeInsets.all(4),
                decoration: BoxDecoration(
                  color: const Color(0xFF0F192C).withOpacity(0.85),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: const Color(0xFF00F0FF).withOpacity(0.25)),
                ),
                child: Row(
                  children: [
                    Expanded(
                      child: _buildModeTab(
                        label: 'State #',
                        isSelected: _selectedMode == 0,
                        onTap: () {
                          setState(() => _selectedMode = 0);
                          _recalculate();
                        },
                      ),
                    ),
                    Expanded(
                      child: _buildModeTab(
                        label: 'Server Days',
                        isSelected: _selectedMode == 1,
                        onTap: () {
                          setState(() => _selectedMode = 1);
                          _recalculate();
                        },
                      ),
                    ),
                    Expanded(
                      child: _buildModeTab(
                        label: '📅 Pick Date',
                        isSelected: _selectedMode == 2,
                        onTap: _pickDate,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),

              // Input Field
              if (_selectedMode != 2) ...[
                Row(
                  children: [
                    Expanded(
                      child: Container(
                        decoration: BoxDecoration(
                          color: const Color(0xFF0F192C).withOpacity(0.85),
                          borderRadius: BorderRadius.circular(16),
                          border: Border.all(color: const Color(0xFF38BDF8).withOpacity(0.3)),
                        ),
                        child: TextField(
                          controller: _stateInputController,
                          keyboardType: TextInputType.number,
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                            fontFamily: 'Outfit',
                          ),
                          decoration: InputDecoration(
                            hintText: _selectedMode == 0 ? 'Enter State (e.g. 750)' : 'Enter Days (e.g. 450)',
                            hintStyle: const TextStyle(color: Color(0xFF64748B), fontSize: 13),
                            prefixIcon: Icon(
                              _selectedMode == 0 ? Icons.flag_rounded : Icons.timer_outlined,
                              color: const Color(0xFF00F0FF),
                            ),
                            border: InputBorder.none,
                            contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                          ),
                          onChanged: (_) => _recalculate(),
                        ),
                      ),
                    ),
                    const SizedBox(width: 10),
                    ElevatedButton(
                      onPressed: _recalculate,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF00F0FF),
                        foregroundColor: const Color(0xFF040914),
                        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 15),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                        elevation: 0,
                      ),
                      child: const Text('Calculate', style: TextStyle(fontWeight: FontWeight.bold)),
                    ),
                  ],
                ),
                const SizedBox(height: 20),
              ],

              // Results Cards
              if (_calculation != null) ...[
                _buildCalculationCard(_calculation!),
                const SizedBox(height: 16),
                _buildRoadmapCard(_calculation!),
                const SizedBox(height: 16),
                _buildTimelineCard(_calculation!),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildModeTab({required String label, required bool isSelected, required VoidCallback onTap}) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.symmetric(vertical: 10),
        decoration: BoxDecoration(
          gradient: isSelected
              ? const LinearGradient(
                  colors: [Color(0xFF00F0FF), Color(0xFF0284C7)],
                )
              : null,
          color: isSelected ? null : Colors.transparent,
          borderRadius: BorderRadius.circular(12),
        ),
        child: Center(
          child: Text(
            label,
            style: TextStyle(
              color: isSelected ? const Color(0xFF040914) : const Color(0xFF94A3B8),
              fontSize: 12.5,
              fontWeight: FontWeight.bold,
              fontFamily: 'Outfit',
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildCalculationCard(StateCalculation calc) {
    return Container(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            const Color(0xFF132238).withOpacity(0.85),
            const Color(0xFF0A1220).withOpacity(0.95),
          ],
        ),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: const Color(0xFF00F0FF).withOpacity(0.35), width: 1.2),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF00F0FF).withOpacity(0.12),
            blurRadius: 20,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Generation Banner
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'ACTIVE GENERATION',
                      style: TextStyle(
                        color: Color(0xFF00F0FF),
                        fontSize: 11,
                        fontWeight: FontWeight.bold,
                        letterSpacing: 1.2,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      calc.currentGenLabel,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 22,
                        fontWeight: FontWeight.w900,
                        fontFamily: 'Outfit',
                      ),
                    ),
                  ],
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                  decoration: BoxDecoration(
                    color: const Color(0xFF00F0FF).withOpacity(0.15),
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(color: const Color(0xFF00F0FF)),
                    boxShadow: [
                      BoxShadow(
                        color: const Color(0xFF00F0FF).withOpacity(0.25),
                        blurRadius: 10,
                      ),
                    ],
                  ),
                  child: Text(
                    'Day ~${calc.ageInDays}',
                    style: const TextStyle(
                      color: Color(0xFF00F0FF),
                      fontSize: 14,
                      fontWeight: FontWeight.bold,
                      fontFamily: 'Outfit',
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 18),
            const Divider(height: 1, color: Colors.white12),
            const SizedBox(height: 16),

            // Active Heroes
            const Text(
              'Featured Generation Heroes:',
              style: TextStyle(
                color: Color(0xFF94A3B8),
                fontSize: 12,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: calc.activeHeroes.map((hero) {
                return Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                  decoration: BoxDecoration(
                    color: const Color(0xFF1E293B).withOpacity(0.8),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: const Color(0xFF38BDF8).withOpacity(0.4)),
                  ),
                  child: Text(
                    hero,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                );
              }).toList(),
            ),
            const SizedBox(height: 20),

            // Next Generation Countdown
            if (calc.nextGeneration != null) ...[
              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: Colors.black.withOpacity(0.4),
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: const Color(0xFFF59E0B).withOpacity(0.4)),
                  boxShadow: [
                    BoxShadow(
                      color: const Color(0xFFF59E0B).withOpacity(0.1),
                      blurRadius: 12,
                    ),
                  ],
                ),
                child: Row(
                  children: [
                    const Text('⏳', style: TextStyle(fontSize: 24)),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Generation ${calc.nextGeneration} Unlocks In:',
                            style: const TextStyle(
                              color: Color(0xFFF59E0B),
                              fontSize: 12,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          const SizedBox(height: 2),
                          Text(
                            '${calc.daysUntilNextGen} Days remaining',
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                              fontFamily: 'Outfit',
                            ),
                          ),
                          if (calc.estimatedNextGenDate != null)
                            Text(
                              'Est. Date: ${DateFormat.yMMMd().format(calc.estimatedNextGenDate!)}',
                              style: const TextStyle(
                                color: Color(0xFF94A3B8),
                                fontSize: 11,
                              ),
                            ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildRoadmapCard(StateCalculation calc) {
    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFF0F192C).withOpacity(0.85),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: const Color(0xFF38BDF8).withOpacity(0.25)),
      ),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Row(
              children: [
                Text('🎯', style: TextStyle(fontSize: 18)),
                SizedBox(width: 8),
                Text(
                  'Tactical Shard Investment Roadmap',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                    fontFamily: 'Outfit',
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),

            // Advice Banner
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: const Color(0xFF00F0FF).withOpacity(0.08),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: const Color(0xFF00F0FF).withOpacity(0.3)),
              ),
              child: Text(
                calc.tacticalAdvice,
                style: const TextStyle(
                  color: Color(0xFFE2E8F0),
                  fontSize: 13,
                  height: 1.4,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ),
            const SizedBox(height: 16),

            // Roadmap Steps
            ...calc.heroBuildRoadmap.map((step) {
              return Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('• ', style: TextStyle(color: Color(0xFF00F0FF), fontSize: 16)),
                    Expanded(
                      child: Text(
                        step,
                        style: const TextStyle(
                          color: Color(0xFFCBD5E1),
                          fontSize: 12.5,
                          height: 1.35,
                        ),
                      ),
                    ),
                  ],
                ),
              );
            }),
          ],
        ),
      ),
    );
  }

  Widget _buildTimelineCard(StateCalculation calc) {
    // Apply filters
    List<StateMilestone> filtered = calc.milestones;
    if (_timelineFilter == 'Upcoming') {
      filtered = calc.upcomingMilestones;
    } else if (_timelineFilter == 'Unlocked') {
      filtered = calc.unlockedMilestones;
    } else if (_timelineFilter == 'Fire Crystal') {
      filtered = calc.milestones.where((m) => m.category == 'Fire Crystal').toList();
    } else if (_timelineFilter == 'Pet') {
      filtered = calc.milestones.where((m) => m.category == 'Pet').toList();
    } else if (_timelineFilter == 'Hero') {
      filtered = calc.milestones.where((m) => m.category == 'Hero').toList();
    } else if (_timelineFilter == 'Event') {
      filtered = calc.milestones.where((m) => m.category == 'Event' || m.category == 'Academy' || m.category == 'Gear').toList();
    }

    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFF0F192C).withOpacity(0.85),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: const Color(0xFF00F0FF).withOpacity(0.25)),
      ),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Row(
                  children: [
                    Text('📜', style: TextStyle(fontSize: 18)),
                    SizedBox(width: 8),
                    Text(
                      'State Timeline & Feature Unlocks',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        fontFamily: 'Outfit',
                      ),
                    ),
                  ],
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: const Color(0xFF0284C7).withOpacity(0.2),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: const Color(0xFF0284C7)),
                  ),
                  child: Text(
                    '${calc.unlockedMilestones.length}/${calc.milestones.length} Unlocked',
                    style: const TextStyle(color: Color(0xFF38BDF8), fontSize: 11, fontWeight: FontWeight.bold),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),

            // Filter Chips
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              physics: const BouncingScrollPhysics(),
              child: Row(
                children: [
                  _buildTimelineFilterChip('All', 'All (${calc.milestones.length})'),
                  _buildTimelineFilterChip('Upcoming', '⏳ Upcoming (${calc.upcomingMilestones.length})'),
                  _buildTimelineFilterChip('Unlocked', '✅ Unlocked (${calc.unlockedMilestones.length})'),
                  _buildTimelineFilterChip('Fire Crystal', '💎 Fire Crystal'),
                  _buildTimelineFilterChip('Pet', '🐾 Pets'),
                  _buildTimelineFilterChip('Hero', '👑 Heroes'),
                  _buildTimelineFilterChip('Event', '⚔️ Events & Gear'),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // Milestone List
            if (filtered.isEmpty)
              const Padding(
                padding: EdgeInsets.symmetric(vertical: 20),
                child: Center(
                  child: Text('No milestones matching this filter.', style: TextStyle(color: Color(0xFF64748B))),
                ),
              )
            else
              ListView.separated(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                itemCount: filtered.length,
                separatorBuilder: (_, __) => const SizedBox(height: 10),
                itemBuilder: (context, index) {
                  final m = filtered[index];
                  return Container(
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(
                      color: m.isUnlocked
                          ? const Color(0xFF132238).withOpacity(0.6)
                          : const Color(0xFF070D18).withOpacity(0.8),
                      borderRadius: BorderRadius.circular(14),
                      border: Border.all(
                        color: m.isUnlocked
                            ? const Color(0xFF10B981).withOpacity(0.3)
                            : const Color(0xFFF59E0B).withOpacity(0.3),
                      ),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(m.icon, style: const TextStyle(fontSize: 20)),
                            const SizedBox(width: 10),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Row(
                                    children: [
                                      Expanded(
                                        child: Text(
                                          m.title,
                                          style: const TextStyle(
                                            color: Colors.white,
                                            fontSize: 14,
                                            fontWeight: FontWeight.bold,
                                            fontFamily: 'Outfit',
                                          ),
                                        ),
                                      ),
                                      Container(
                                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                        decoration: BoxDecoration(
                                          color: m.isUnlocked
                                              ? const Color(0xFF10B981).withOpacity(0.15)
                                              : const Color(0xFFF59E0B).withOpacity(0.15),
                                          borderRadius: BorderRadius.circular(6),
                                          border: Border.all(
                                            color: m.isUnlocked ? const Color(0xFF10B981) : const Color(0xFFF59E0B),
                                          ),
                                        ),
                                        child: Text(
                                          m.isUnlocked ? '✅ Day ${m.day}' : '⏳ In ${m.daysRemaining}d',
                                          style: TextStyle(
                                            color: m.isUnlocked ? const Color(0xFF10B981) : const Color(0xFFF59E0B),
                                            fontSize: 11,
                                            fontWeight: FontWeight.bold,
                                          ),
                                        ),
                                      ),
                                    ],
                                  ),
                                  const SizedBox(height: 6),
                                  Text(
                                    m.description,
                                    style: const TextStyle(
                                      color: Color(0xFF94A3B8),
                                      fontSize: 12,
                                      height: 1.35,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  );
                },
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildTimelineFilterChip(String filterKey, String label) {
    final isSelected = _timelineFilter == filterKey;
    return Padding(
      padding: const EdgeInsets.only(right: 8),
      child: GestureDetector(
        onTap: () => setState(() => _timelineFilter = filterKey),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
          decoration: BoxDecoration(
            color: isSelected ? const Color(0xFF00F0FF).withOpacity(0.2) : const Color(0xFF1E293B).withOpacity(0.6),
            borderRadius: BorderRadius.circular(10),
            border: Border.all(
              color: isSelected ? const Color(0xFF00F0FF) : Colors.white12,
            ),
          ),
          child: Text(
            label,
            style: TextStyle(
              color: isSelected ? const Color(0xFF00F0FF) : const Color(0xFF94A3B8),
              fontSize: 11.5,
              fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
            ),
          ),
        ),
      ),
    );
  }
}
