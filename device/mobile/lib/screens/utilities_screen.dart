import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:url_launcher/url_launcher.dart';
import '../services/knowledge_service.dart';

class UtilitiesScreen extends StatefulWidget {
  const UtilitiesScreen({super.key});

  @override
  State<UtilitiesScreen> createState() => _UtilitiesScreenState();
}

class _UtilitiesScreenState extends State<UtilitiesScreen> {
  int _activeTab = 0; // 0: FC Calc, 1: Charms, 2: SvS Points, 3: Transfer, 4: Gift Codes, 5: UTC Timers

  // FC Calculator State
  String _fcBuildingType = 'furnace';
  int _fcFromLevel = 0;
  int _fcToLevel = 5;

  // Charms Calculator State
  int _charmFromLevel = 0;
  int _charmToLevel = 5;

  // SvS Calculator State
  String _svsActivity = 'fc';
  final TextEditingController _svsAmountController = TextEditingController(text: '1000');

  // Transfer Calculator State
  final TextEditingController _transferPowerController = TextEditingController(text: '150');

  @override
  void dispose() {
    _svsAmountController.dispose();
    _transferPowerController.dispose();
    super.dispose();
  }

  // --- Dynamic Data Resolvers ---
  List<Map<String, String>> _resolveGiftCodes() {
    final dynamicData = KnowledgeService.dynamicUtilityData;
    if (dynamicData != null && dynamicData['gift_codes'] is List) {
      return (dynamicData['gift_codes'] as List).map<Map<String, String>>((item) {
        return {
          'code': item['code']?.toString() ?? '',
          'rewards': item['rewards']?.toString() ?? '',
        };
      }).toList();
    }
    return _defaultGiftCodes;
  }

  Map<int, List<num>> _resolveFcTable() {
    final dynamicData = KnowledgeService.dynamicUtilityData;
    if (dynamicData != null && dynamicData['fc_table'] is Map) {
      final Map<String, dynamic> raw = dynamicData['fc_table'];
      final Map<int, List<num>> res = {};
      raw.forEach((k, v) {
        final int? lvl = int.tryParse(k);
        if (lvl != null && v is Map) {
          res[lvl] = [
            v['furnace_fc'] ?? 0,
            v['furnace_rfc'] ?? 0,
            v['camp_fc'] ?? 0,
            v['camp_rfc'] ?? 0,
            v['days'] ?? 0,
          ];
        }
      });
      if (res.isNotEmpty) return res;
    }
    return _defaultFcTable;
  }

  Map<int, List<num>> _resolveCharmTable() {
    final dynamicData = KnowledgeService.dynamicUtilityData;
    if (dynamicData != null && dynamicData['charm_table'] is Map) {
      final Map<String, dynamic> raw = dynamicData['charm_table'];
      final Map<int, List<num>> res = {};
      raw.forEach((k, v) {
        final int? lvl = int.tryParse(k);
        if (lvl != null && v is Map) {
          res[lvl] = [
            v['guides'] ?? 0,
            v['designs'] ?? 0,
            v['boost'] ?? 0.0,
            v['svs_pts'] ?? 0,
          ];
        }
      });
      if (res.isNotEmpty) return res;
    }
    return _defaultCharmTable;
  }

  Map<String, Map<String, dynamic>> _resolveSvsRates() {
    final dynamicData = KnowledgeService.dynamicUtilityData;
    if (dynamicData != null && dynamicData['svs_rates'] is Map) {
      final Map<String, dynamic> raw = dynamicData['svs_rates'];
      final Map<String, Map<String, dynamic>> res = {};
      raw.forEach((k, v) {
        if (v is Map) {
          res[k] = Map<String, dynamic>.from(v);
        }
      });
      if (res.isNotEmpty) return res;
    }
    return _defaultSvsRates;
  }

  // --- Default Fallback Tables ---
  static const Map<int, List<num>> _defaultFcTable = {
    1: [600, 0, 350, 0, 8],
    2: [1200, 0, 700, 0, 12],
    3: [2000, 0, 1150, 0, 16],
    4: [3200, 0, 1800, 0, 22],
    5: [4800, 0, 2700, 0, 30],
    6: [2500, 180, 1400, 100, 40],
    7: [3500, 320, 1950, 180, 52],
    8: [5000, 550, 2800, 300, 65],
    9: [7000, 850, 3900, 480, 80],
    10: [10000, 1300, 5500, 720, 100],
    11: [14000, 1900, 7800, 1050, 120],
    12: [19500, 2700, 11000, 1500, 145],
  };

  static const Map<int, List<num>> _defaultCharmTable = {
    1: [10, 0, 2.5, 7000],
    2: [25, 5, 5.5, 17500],
    3: [50, 15, 9.0, 35000],
    4: [90, 30, 14.0, 63000],
    5: [150, 55, 20.5, 105000],
    6: [240, 95, 28.5, 168000],
    7: [360, 150, 38.0, 252000],
    8: [520, 230, 50.0, 364000],
    9: [720, 340, 64.5, 504000],
    10: [980, 490, 82.0, 686000],
    11: [1300, 680, 105.0, 910000],
    12: [1750, 920, 132.0, 1225000],
  };

  static const Map<String, Map<String, dynamic>> _defaultSvsRates = {
    'fc': {'name': 'Fire Crystals', 'rate': 2000, 'unit': 'FC', 'day': 'Day 1 & Day 5'},
    'rfc': {'name': 'Refined Fire Crystals', 'rate': 30000, 'unit': 'RFC', 'day': 'Day 1 & Day 5'},
    'speedup_hr': {'name': 'Speedups (Hours)', 'rate': 1800, 'unit': 'Hours', 'day': 'Day 1, 2 & 5'},
    'speedup_min': {'name': 'Speedups (Minutes)', 'rate': 30, 'unit': 'Minutes', 'day': 'Day 1, 2 & 5'},
    'fc_shard': {'name': 'FC Shards (Helios)', 'rate': 1000, 'unit': 'Shards', 'day': 'Day 2 & Day 5'},
    'lucky_wheel': {'name': 'Lucky Wheel Spins', 'rate': 4000, 'unit': 'Spins', 'day': 'Day 2'},
    'hero_shard': {'name': 'Mythic Hero Shards', 'rate': 6000, 'unit': 'Shards', 'day': 'Day 2'},
    'expert_sigil': {'name': 'Dawn Expert Sigils', 'rate': 6000, 'unit': 'Sigils', 'day': 'Day 2'},
    'polar_terror': {'name': 'Polar Terror Rallies', 'rate': 30000, 'unit': 'Rallies', 'day': 'Day 3'},
    'mithril': {'name': 'Mithril (Exclusive Gear)', 'rate': 144000, 'unit': 'Mithril', 'day': 'Day 4 & 5'},
    't10_train': {'name': 'T10 Troops Trained', 'rate': 60, 'unit': 'Troops', 'day': 'Day 4'},
    't11_train': {'name': 'T11 Troops Trained', 'rate': 75, 'unit': 'Troops', 'day': 'Day 4'},
    't12_train': {'name': 'T12 Troops Trained', 'rate': 90, 'unit': 'Troops', 'day': 'Day 4'},
  };

  static const List<Map<String, String>> _defaultGiftCodes = [
    {'code': 'WOS2026', 'rewards': '1000 Gems, 5x 1h Speedups, 10x Gold Keys, 500k Meat/Wood'},
    {'code': 'STATEOFPOWER', 'rewards': '500 Gems, 10x Advanced Wild Marks, 20x Charm Guides'},
    {'code': 'DC300K', 'rewards': '1500 Gems, 20x Mythic Shards, 10x 1h Speedups'},
    {'code': 'FROSTYTACTICS', 'rewards': 'Exclusive Frosty Avatar Frame, 300 Gems, 5x Stamina'},
    {'code': 'BEARHUNT2026', 'rewards': '800 Gems, 100x Stamina, 10x March Speedups'},
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF040812),
      appBar: AppBar(
        backgroundColor: const Color(0xFF070D18),
        elevation: 0,
        title: const Row(
          children: [
            Text('🧮 ', style: TextStyle(fontSize: 18)),
            Text(
              'Tactical Utilities & Calculators',
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
      body: Column(
        children: [
          // Sub-Tab Selector
          Container(
            color: const Color(0xFF070D18),
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            child: SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              physics: const BouncingScrollPhysics(),
              child: Row(
                children: [
                  _buildSubTab(0, '💎 Fire Crystal', 'FC'),
                  _buildSubTab(1, '🛡️ Chief Charms', 'Charms'),
                  _buildSubTab(2, '🏆 SvS Points', 'SvS'),
                  _buildSubTab(3, '🚀 State Transfer', 'Transfer'),
                  _buildSubTab(4, '🎁 Gift Codes', 'Codes'),
                  _buildSubTab(5, '⏰ UTC Timers', 'Timers'),
                ],
              ),
            ),
          ),

          // Tab Content
          Expanded(
            child: SingleChildScrollView(
              physics: const BouncingScrollPhysics(),
              padding: const EdgeInsets.all(16),
              child: _buildActiveTabContent(),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSubTab(int index, String label, String shortLabel) {
    final isSelected = _activeTab == index;
    return Padding(
      padding: const EdgeInsets.only(right: 8),
      child: GestureDetector(
        onTap: () => setState(() => _activeTab = index),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
          decoration: BoxDecoration(
            gradient: isSelected
                ? const LinearGradient(colors: [Color(0xFF00F0FF), Color(0xFF0284C7)])
                : null,
            color: isSelected ? null : const Color(0xFF0F192C),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
              color: isSelected ? const Color(0xFF00F0FF) : Colors.white12,
            ),
          ),
          child: Text(
            label,
            style: TextStyle(
              color: isSelected ? const Color(0xFF040914) : const Color(0xFF94A3B8),
              fontSize: 12.5,
              fontWeight: isSelected ? FontWeight.bold : FontWeight.w600,
              fontFamily: 'Outfit',
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildActiveTabContent() {
    switch (_activeTab) {
      case 0:
        return _buildFCCalculator();
      case 1:
        return _buildCharmsCalculator();
      case 2:
        return _buildSvSCalculator();
      case 3:
        return _buildTransferCalculator();
      case 4:
        return _buildGiftCodesView();
      case 5:
        return _buildUTCTimersView();
      default:
        return const SizedBox();
    }
  }

  // --- 1. Fire Crystal Calculator ---
  Widget _buildFCCalculator() {
    final fcTable = _resolveFcTable();
    final maxFcLevel = fcTable.keys.isNotEmpty ? fcTable.keys.reduce((a, b) => a > b ? a : b) : 10;
    final isFurnace = _fcBuildingType == 'furnace';
    int totalFC = 0;
    int totalRFC = 0;
    int totalDays = 0;

    for (int lvl = _fcFromLevel + 1; lvl <= _fcToLevel; lvl++) {
      final row = fcTable[lvl] ?? [0, 0, 0, 0, 0];
      if (isFurnace) {
        totalFC += row[0].toInt();
        totalRFC += row[1].toInt();
      } else {
        totalFC += row[2].toInt();
        totalRFC += row[3].toInt();
      }
      totalDays += row[4].toInt();
    }
    final int svsPoints = (totalFC * 2000) + (totalRFC * 30000);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildCard(
          title: '💎 Fire Crystal Upgrade Planner',
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('Select Building Type:', style: TextStyle(color: Color(0xFF94A3B8), fontSize: 12)),
              const SizedBox(height: 6),
              Row(
                children: [
                  Expanded(
                    child: _buildSelectionChip(
                      label: 'Furnace / Embassy / Command',
                      isSelected: isFurnace,
                      onTap: () => setState(() => _fcBuildingType = 'furnace'),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: _buildSelectionChip(
                      label: 'Troop Camp (Inf/Lan/Mar)',
                      isSelected: !isFurnace,
                      onTap: () => setState(() => _fcBuildingType = 'camp'),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              Row(
                children: [
                  Expanded(
                    child: _buildDropdown(
                      label: 'Current FC Level',
                      value: _fcFromLevel,
                      items: List.generate(maxFcLevel, (i) => i),
                      itemLabel: (val) => val == 0 ? 'Lv 30 (FC 0)' : 'FC $val',
                      onChanged: (val) {
                        if (val != null && val < _fcToLevel) setState(() => _fcFromLevel = val);
                      },
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: _buildDropdown(
                      label: 'Target FC Level',
                      value: _fcToLevel,
                      items: List.generate(maxFcLevel, (i) => i + 1),
                      itemLabel: (val) => 'FC $val',
                      onChanged: (val) {
                        if (val != null && val > _fcFromLevel) setState(() => _fcToLevel = val);
                      },
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),
        _buildCard(
          title: '📊 Required Upgrade Materials',
          child: Column(
            children: [
              _buildResultRow('Regular Fire Crystals (FC)', '$totalFC FC', const Color(0xFF00F0FF)),
              if (totalRFC > 0) ...[
                const SizedBox(height: 8),
                _buildResultRow('Refined Fire Crystals (RFC)', '$totalRFC RFC', const Color(0xFFA855F7)),
              ],
              const SizedBox(height: 8),
              _buildResultRow('Base Construction Time', '~$totalDays Days', const Color(0xFFF59E0B)),
              const SizedBox(height: 8),
              _buildResultRow('SvS City Construction Points', '${_formatNumber(svsPoints)} Pts', const Color(0xFF10B981)),
            ],
          ),
        ),
      ],
    );
  }

  // --- 2. Chief Charms Calculator ---
  Widget _buildCharmsCalculator() {
    final charmTable = _resolveCharmTable();
    final maxCharmLevel = charmTable.keys.isNotEmpty ? charmTable.keys.reduce((a, b) => a > b ? a : b) : 11;
    int totalGuides = 0;
    int totalDesigns = 0;
    double totalBoost = 0;
    int totalSvS = 0;

    for (int lvl = _charmFromLevel + 1; lvl <= _charmToLevel; lvl++) {
      final row = charmTable[lvl] ?? [0, 0, 0.0, 0];
      totalGuides += row[0].toInt();
      totalDesigns += row[1].toInt();
      totalBoost += row[2].toDouble();
      totalSvS += row[3].toInt();
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildCard(
          title: '🛡️ Chief Charms Upgrade Planner (Per Slot)',
          child: Column(
            children: [
              Row(
                children: [
                  Expanded(
                    child: _buildDropdown(
                      label: 'Current Charm Level',
                      value: _charmFromLevel,
                      items: List.generate(maxCharmLevel, (i) => i),
                      itemLabel: (val) => val == 0 ? 'Unequipped (Lv 0)' : 'Level $val',
                      onChanged: (val) {
                        if (val != null && val < _charmToLevel) setState(() => _charmFromLevel = val);
                      },
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: _buildDropdown(
                      label: 'Target Charm Level',
                      value: _charmToLevel,
                      items: List.generate(maxCharmLevel, (i) => i + 1),
                      itemLabel: (val) => 'Level $val',
                      onChanged: (val) {
                        if (val != null && val > _charmFromLevel) setState(() => _charmToLevel = val);
                      },
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),
        _buildCard(
          title: '📊 Required Materials & Combat Stats',
          child: Column(
            children: [
              _buildResultRow('Charm Guides Needed', '$totalGuides Guides', const Color(0xFF00F0FF)),
              const SizedBox(height: 8),
              _buildResultRow('Charm Designs Needed', '$totalDesigns Designs', const Color(0xFFA855F7)),
              const SizedBox(height: 8),
              _buildResultRow('Lethality / Health Surge', '+${totalBoost.toStringAsFixed(1)}%', const Color(0xFFF59E0B)),
              const SizedBox(height: 8),
              _buildResultRow('SvS Charm Points (70 pts/score)', '${_formatNumber(totalSvS)} Pts', const Color(0xFF10B981)),
            ],
          ),
        ),
      ],
    );
  }

  // --- 3. SvS Points Calculator ---
  Widget _buildSvSCalculator() {
    final svsRates = _resolveSvsRates();
    if (!svsRates.containsKey(_svsActivity)) {
      _svsActivity = svsRates.keys.first;
    }
    final selectedRate = svsRates[_svsActivity]!;
    final int amount = int.tryParse(_svsAmountController.text.trim()) ?? 0;
    final int totalPoints = amount * (selectedRate['rate'] as int);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildCard(
          title: '🏆 SvS Prep Phase Points Calculator',
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('Select Activity:', style: TextStyle(color: Color(0xFF94A3B8), fontSize: 12)),
              const SizedBox(height: 6),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 14),
                decoration: BoxDecoration(
                  color: const Color(0xFF132238),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: const Color(0xFF38BDF8).withOpacity(0.3)),
                ),
                child: DropdownButtonHideUnderline(
                  child: DropdownButton<String>(
                    value: _svsActivity,
                    isExpanded: true,
                    dropdownColor: const Color(0xFF0F192C),
                    items: svsRates.entries.map((e) {
                      return DropdownMenuItem<String>(
                        value: e.key,
                        child: Text(e.value['name'] as String, style: const TextStyle(color: Colors.white)),
                      );
                    }).toList(),
                    onChanged: (val) {
                      if (val != null) setState(() => _svsActivity = val);
                    },
                  ),
                ),
              ),
              const SizedBox(height: 16),
              const Text('Enter Quantity:', style: TextStyle(color: Color(0xFF94A3B8), fontSize: 12)),
              const SizedBox(height: 6),
              Container(
                decoration: BoxDecoration(
                  color: const Color(0xFF132238),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: const Color(0xFF38BDF8).withOpacity(0.3)),
                ),
                child: TextField(
                  controller: _svsAmountController,
                  keyboardType: TextInputType.number,
                  style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                  decoration: InputDecoration(
                    suffixText: selectedRate['unit'] as String,
                    suffixStyle: const TextStyle(color: Color(0xFF00F0FF)),
                    border: InputBorder.none,
                    contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                  ),
                  onChanged: (_) => setState(() {}),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),
        _buildCard(
          title: '🌟 Point Conversion Result',
          child: Column(
            children: [
              _buildResultRow('Total SvS Points Earned', '${_formatNumber(totalPoints)} Points', const Color(0xFF10B981)),
              const SizedBox(height: 8),
              _buildResultRow('Optimal Day to Spend', selectedRate['day'] as String, const Color(0xFFF59E0B)),
            ],
          ),
        ),
      ],
    );
  }

  // --- 4. State Transfer Calculator ---
  Widget _buildTransferCalculator() {
    final double power = double.tryParse(_transferPowerController.text.trim()) ?? 150.0;
    int passes = 1;
    String tier = 'Ordinary Transfer';

    if (power < 30) {
      passes = 1;
    } else if (power < 50) {
      passes = 2;
    } else if (power < 75) {
      passes = 3;
    } else if (power < 100) {
      passes = 5;
    } else if (power < 130) {
      passes = 8;
    } else if (power < 170) {
      passes = 12;
    } else if (power < 220) {
      passes = 18;
    } else if (power < 280) {
      passes = 25;
    } else if (power < 350) {
      passes = 35;
      tier = 'High Power Transfer';
    } else if (power < 450) {
      passes = 50;
      tier = 'High Power Transfer';
    } else if (power < 600) {
      passes = 65;
      tier = 'Top Tier Transfer';
    } else {
      passes = 80;
      tier = 'Whale Transfer (Requires Leading Invite)';
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildCard(
          title: '🚀 State Transfer Pass Calculator',
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('Enter Chief Power (in Millions):', style: TextStyle(color: Color(0xFF94A3B8), fontSize: 12)),
              const SizedBox(height: 6),
              Container(
                decoration: BoxDecoration(
                  color: const Color(0xFF132238),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: const Color(0xFF38BDF8).withOpacity(0.3)),
                ),
                child: TextField(
                  controller: _transferPowerController,
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                  decoration: const InputDecoration(
                    suffixText: 'Million Power',
                    suffixStyle: TextStyle(color: Color(0xFF00F0FF)),
                    border: InputBorder.none,
                    contentPadding: EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                  ),
                  onChanged: (_) => setState(() {}),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),
        _buildCard(
          title: '🎫 Transfer Pass Requirement',
          child: Column(
            children: [
              _buildResultRow('Required Transfer Passes', '$passes Passes', const Color(0xFF00F0FF)),
              const SizedBox(height: 8),
              _buildResultRow('Transfer Category', tier, const Color(0xFFF59E0B)),
              const SizedBox(height: 14),
              const Divider(height: 1, color: Colors.white12),
              const SizedBox(height: 12),
              const Text(
                '• Furnace Lv 25 minimum\n• Empty infirmary & no active marches\n• 30-Day transfer cooldown between hops\n• Target state must have open ordinary/leading quota',
                style: TextStyle(color: Color(0xFF94A3B8), fontSize: 12, height: 1.4),
              ),
            ],
          ),
        ),
      ],
    );
  }

  // --- 5. Gift Codes ---
  Widget _buildGiftCodesView() {
    final giftCodes = _resolveGiftCodes();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildCard(
          title: '🎁 Active Whiteout Survival Promo Codes',
          child: Column(
            children: giftCodes.map((c) {
              return Container(
                margin: const EdgeInsets.only(bottom: 10),
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: const Color(0xFF132238),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: const Color(0xFF10B981).withOpacity(0.3)),
                ),
                child: Row(
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            c['code']!,
                            style: const TextStyle(
                              color: Color(0xFF10B981),
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                              fontFamily: 'Outfit',
                              letterSpacing: 1.1,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            c['rewards']!,
                            style: const TextStyle(color: Color(0xFF94A3B8), fontSize: 11.5),
                          ),
                        ],
                      ),
                    ),
                    IconButton(
                      icon: const Icon(Icons.copy_rounded, color: Color(0xFF00F0FF), size: 20),
                      onPressed: () {
                        Clipboard.setData(ClipboardData(text: c['code']!));
                        ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(
                            content: Text('Copied code: ${c['code']}'),
                            backgroundColor: const Color(0xFF0284C7),
                            duration: const Duration(seconds: 2),
                          ),
                        );
                      },
                    ),
                  ],
                ),
              );
            }).toList(),
          ),
        ),
        const SizedBox(height: 16),
        ElevatedButton.icon(
          onPressed: () async {
            final url = Uri.parse('https://wos-giftcode.centurygame.com/');
            if (await canLaunchUrl(url)) {
              await launchUrl(url, mode: LaunchMode.externalApplication);
            }
          },
          icon: const Icon(Icons.open_in_browser_rounded),
          label: const Text('Open Official Century Games Redeem Portal', style: TextStyle(fontWeight: FontWeight.bold)),
          style: ElevatedButton.styleFrom(
            backgroundColor: const Color(0xFF00F0FF),
            foregroundColor: const Color(0xFF040914),
            minimumSize: const Size(double.infinity, 50),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
          ),
        ),
      ],
    );
  }

  // --- 6. UTC Alliance Timers ---
  Widget _buildUTCTimersView() {
    final nowUtc = DateTime.now().toUtc();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildCard(
          title: '⏰ Alliance UTC Battle Windows',
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Current UTC Time: ${nowUtc.hour.toString().padLeft(2, '0')}:${nowUtc.minute.toString().padLeft(2, '0')} UTC',
                style: const TextStyle(color: Color(0xFF00F0FF), fontSize: 14, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 14),
              _buildTimerRow('Foundry Battle', '19:00 & 21:00 UTC (Sat/Sun)'),
              const SizedBox(height: 8),
              _buildTimerRow('Canyon Clash', '12:00 & 19:00 UTC (Bi-weekly)'),
              const SizedBox(height: 8),
              _buildTimerRow('SVS Battle Phase', '10:00 – 22:00 UTC (Saturday)'),
              const SizedBox(height: 8),
              _buildTimerRow('Bear Trap', 'Every 48 Hours (Alliance set)'),
              const SizedBox(height: 8),
              _buildTimerRow('Fortress Battle', '14:00 & 19:00 UTC (Alternating)'),
            ],
          ),
        ),
      ],
    );
  }

  // --- UI Helpers ---
  Widget _buildCard({required String title, required Widget child}) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: const Color(0xFF0F192C).withOpacity(0.9),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: const Color(0xFF00F0FF).withOpacity(0.25)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: const TextStyle(color: Colors.white, fontSize: 15, fontWeight: FontWeight.bold, fontFamily: 'Outfit'),
          ),
          const SizedBox(height: 14),
          child,
        ],
      ),
    );
  }

  Widget _buildResultRow(String label, String value, Color color) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(label, style: const TextStyle(color: Color(0xFF94A3B8), fontSize: 13)),
        Text(value, style: TextStyle(color: color, fontSize: 14, fontWeight: FontWeight.bold, fontFamily: 'Outfit')),
      ],
    );
  }

  Widget _buildTimerRow(String event, String time) {
    return Container(
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: const Color(0xFF132238),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(event, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
          Text(time, style: const TextStyle(color: Color(0xFF38BDF8), fontSize: 12)),
        ],
      ),
    );
  }

  Widget _buildSelectionChip({required String label, required bool isSelected, required VoidCallback onTap}) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 8),
        decoration: BoxDecoration(
          color: isSelected ? const Color(0xFF00F0FF).withOpacity(0.15) : const Color(0xFF132238),
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: isSelected ? const Color(0xFF00F0FF) : Colors.white12),
        ),
        child: Center(
          child: Text(
            label,
            textAlign: TextAlign.center,
            style: TextStyle(
              color: isSelected ? const Color(0xFF00F0FF) : const Color(0xFF94A3B8),
              fontSize: 11,
              fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildDropdown<T>({
    required String label,
    required T value,
    required List<T> items,
    required String Function(T) itemLabel,
    required ValueChanged<T?> onChanged,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: const TextStyle(color: Color(0xFF94A3B8), fontSize: 11)),
        const SizedBox(height: 4),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 10),
          decoration: BoxDecoration(
            color: const Color(0xFF132238),
            borderRadius: BorderRadius.circular(10),
            border: Border.all(color: const Color(0xFF38BDF8).withOpacity(0.3)),
          ),
          child: DropdownButtonHideUnderline(
            child: DropdownButton<T>(
              value: value,
              isExpanded: true,
              dropdownColor: const Color(0xFF0F192C),
              items: items.map((item) {
                return DropdownMenuItem<T>(
                  value: item,
                  child: Text(itemLabel(item), style: const TextStyle(color: Colors.white, fontSize: 12.5)),
                );
              }).toList(),
              onChanged: onChanged,
            ),
          ),
        ),
      ],
    );
  }

  String _formatNumber(int number) {
    if (number >= 1000000000) {
      return '${(number / 1000000000).toStringAsFixed(2)}B';
    } else if (number >= 1000000) {
      return '${(number / 1000000).toStringAsFixed(2)}M';
    } else if (number >= 1000) {
      return '${(number / 1000).toStringAsFixed(1)}k';
    }
    return number.toString();
  }
}
