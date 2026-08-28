import 'dart:async';
import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../models/chat_message.dart';

class AIService extends ChangeNotifier {
  // Configurable API keys via build-time environment or user SharedPreferences
  static const String envGeminiKey = String.fromEnvironment('GEMINI_API_KEY', defaultValue: '');
  static const String envGroqKey = String.fromEnvironment('GROQ_API_KEY', defaultValue: '');
  static const String envBackendUrl = String.fromEnvironment('BACKEND_URL', defaultValue: 'http://10.0.2.2:8000');

  String _geminiKey = envGeminiKey;
  String _groqKey = envGroqKey;
  String _backendUrl = envBackendUrl;
  String _ollamaHost = 'http://localhost:11434';
  String _ollamaModel = 'llama3.2:1b';
  String _selectedProvider = 'auto'; // 'auto', 'backend', 'gemini', 'groq', 'ollama', 'offline'

  bool _isGenerating = false;
  bool get isGenerating => _isGenerating;

  final List<ChatMessage> _messages = [];
  List<ChatMessage> get messages => List.unmodifiable(_messages);

  AIService() {
    _loadSettings();
    _addInitialGreeting();
  }

  void _addInitialGreeting() {
    if (_messages.isEmpty) {
      _messages.add(
        ChatMessage(
          id: 'welcome_1',
          content: '### ❄️ Welcome to Frosty Tactical Command!\n\nI am your **Whiteout Survival Grandmaster AI**. Ask me anything about:\n• 🐻 **Bear Trap & Rally Joiner Buffs** (Jessie +25% rule & 10/10/80 ratios)\n• 🛡️ **Hero Builds & Tier Lists** (Generations 0 to 16+ including Seigel, Bradley, Flint)\n• ⚔️ **PvP Troop Formations** (50/20/30, 60/20/20 Garrison Defense)\n• 🎯 **Crazy Joe & SvS Event Walkthroughs**\n\n*How can I assist your alliance today, Chief?*',
          isUser: false,
          timestamp: DateTime.now(),
          modelUsed: 'Frosty Tactical Core',
          latencySeconds: 0.0,
        ),
      );
    }
  }

  Future<void> _loadSettings() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      _geminiKey = prefs.getString('custom_gemini_key') ?? envGeminiKey;
      _groqKey = prefs.getString('custom_groq_key') ?? envGroqKey;
      _backendUrl = prefs.getString('custom_backend_url') ?? envBackendUrl;
      _ollamaHost = prefs.getString('custom_ollama_host') ?? 'http://localhost:11434';
      _ollamaModel = prefs.getString('custom_ollama_model') ?? 'llama3.2:1b';
      _selectedProvider = prefs.getString('selected_ai_provider') ?? 'auto';
      notifyListeners();
    } catch (_) {}
  }

  Future<void> updateSettings({
    String? geminiKey,
    String? groqKey,
    String? backendUrl,
    String? ollamaHost,
    String? ollamaModel,
    String? provider,
  }) async {
    final prefs = await SharedPreferences.getInstance();
    if (geminiKey != null) {
      _geminiKey = geminiKey.trim();
      await prefs.setString('custom_gemini_key', _geminiKey);
    }
    if (groqKey != null) {
      _groqKey = groqKey.trim();
      await prefs.setString('custom_groq_key', _groqKey);
    }
    if (backendUrl != null) {
      _backendUrl = backendUrl.trim();
      await prefs.setString('custom_backend_url', _backendUrl);
    }
    if (ollamaHost != null) {
      _ollamaHost = ollamaHost.trim();
      await prefs.setString('custom_ollama_host', _ollamaHost);
    }
    if (ollamaModel != null) {
      _ollamaModel = ollamaModel.trim();
      await prefs.setString('custom_ollama_model', _ollamaModel);
    }
    if (provider != null) {
      _selectedProvider = provider;
      await prefs.setString('selected_ai_provider', _selectedProvider);
    }
    notifyListeners();
  }

  String get currentProvider => _selectedProvider;
  String get geminiKey => _geminiKey;
  String get groqKey => _groqKey;
  String get backendUrl => _backendUrl;
  String get ollamaHost => _ollamaHost;

  /// Main message submission handler
  Future<void> sendMessage(String userText) async {
    final cleanText = userText.trim();
    if (cleanText.isEmpty || _isGenerating) return;

    final userMessage = ChatMessage(
      id: 'msg_${DateTime.now().millisecondsSinceEpoch}_user',
      content: cleanText,
      isUser: true,
      timestamp: DateTime.now(),
    );

    _messages.add(userMessage);
    _isGenerating = true;
    notifyListeners();

    final stopwatch = Stopwatch()..start();
    String botAnswer = '';
    String modelUsed = 'Offline Tactical Core';

    try {
      if (_selectedProvider == 'backend') {
        final result = await _callBackend(cleanText);
        botAnswer = result['text']!;
        modelUsed = result['model']!;
      } else if (_selectedProvider == 'gemini') {
        final result = await _callGemini(cleanText);
        botAnswer = result['text']!;
        modelUsed = result['model']!;
      } else if (_selectedProvider == 'groq') {
        final result = await _callGroq(cleanText);
        botAnswer = result['text']!;
        modelUsed = result['model']!;
      } else if (_selectedProvider == 'ollama') {
        final result = await _callOllama(cleanText);
        botAnswer = result['text']!;
        modelUsed = result['model']!;
      } else if (_selectedProvider == 'offline') {
        botAnswer = _generateOfflineFallback(cleanText);
        modelUsed = 'Offline Tactical Core';
      } else {
        // --- AUTO CASCADE FAILOVER ---
        // 1. Try Central Backend REST Server (ChromaDB RAG + Server LLMs)
        bool backendSuccess = false;
        try {
          final result = await _callBackend(cleanText).timeout(const Duration(seconds: 8));
          if (result['text']!.isNotEmpty) {
            botAnswer = result['text']!;
            modelUsed = result['model']!;
            backendSuccess = true;
          }
        } catch (_) {
          backendSuccess = false;
        }

        if (!backendSuccess) {
          // 2. Try Direct Gemini (if user configured key)
          if (_geminiKey.isNotEmpty) {
            try {
              final result = await _callGemini(cleanText).timeout(const Duration(seconds: 8));
              botAnswer = result['text']!;
              modelUsed = result['model']!;
              backendSuccess = true;
            } catch (_) {}
          }
        }

        if (!backendSuccess) {
          // 3. Try Direct Groq (if user configured key)
          if (_groqKey.isNotEmpty) {
            try {
              final result = await _callGroq(cleanText).timeout(const Duration(seconds: 8));
              botAnswer = result['text']!;
              modelUsed = result['model']!;
              backendSuccess = true;
            } catch (_) {}
          }
        }

        if (!backendSuccess) {
          // 4. Try Local Ollama
          try {
            final result = await _callOllama(cleanText).timeout(const Duration(seconds: 5));
            botAnswer = result['text']!;
            modelUsed = result['model']!;
            backendSuccess = true;
          } catch (_) {}
        }

        if (!backendSuccess) {
          // 5. Ultimate Fallback: Rich Offline Tactical Knowledge Synthesizer
          botAnswer = _generateOfflineFallback(cleanText);
          modelUsed = 'Offline Tactical Core';
        }
      }
    } catch (e) {
      botAnswer = _generateOfflineFallback(cleanText);
      modelUsed = 'Offline Tactical Core';
    } finally {
      stopwatch.stop();
      _isGenerating = false;

      final botMessage = ChatMessage(
        id: 'msg_${DateTime.now().millisecondsSinceEpoch}_bot',
        content: botAnswer,
        isUser: false,
        timestamp: DateTime.now(),
        modelUsed: modelUsed,
        latencySeconds: stopwatch.elapsedMilliseconds / 1000.0,
      );

      _messages.add(botMessage);
      notifyListeners();
    }
  }

  // --- 0. Central Backend Server Provider ---
  Future<Map<String, String>> _callBackend(String prompt) async {
    if (_backendUrl.isEmpty) throw Exception('Backend URL not configured');

    String cleanUrl = _backendUrl.trim();
    if (cleanUrl.endsWith('/')) {
      cleanUrl = cleanUrl.substring(0, cleanUrl.length - 1);
    }
    final uri = cleanUrl.endsWith('/api/chat') ? Uri.parse(cleanUrl) : Uri.parse('$cleanUrl/api/chat');

    final payload = {
      'query': prompt,
      'history': _messages
          .where((m) => m.id != 'welcome_1')
          .map((m) => {'role': m.isUser ? 'user' : 'assistant', 'content': m.content})
          .toList(),
    };

    final response = await http.post(
      uri,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(payload),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(utf8.decode(response.bodyBytes));
      return {
        'text': (data['text'] ?? data['response'] ?? '') as String,
        'model': (data['model'] ?? 'Frosty Central Server') as String,
      };
    }
    throw Exception('Backend HTTP ${response.statusCode}');
  }

  void clearConversation() {
    _messages.clear();
    _addInitialGreeting();
    notifyListeners();
  }

  // --- 1. Google Gemini Provider ---
  Future<Map<String, String>> _callGemini(String prompt) async {
    const modelsToTry = ['gemini-3.6-flash', 'gemini-2.5-flash', 'gemini-1.5-flash', 'gemini-1.5-pro'];

    final systemInstruction = _buildSystemPrompt(prompt);

    for (final model in modelsToTry) {
      try {
        final url = Uri.parse(
          'https://generativelanguage.googleapis.com/v1beta/models/$model:generateContent?key=$_geminiKey',
        );

        final payload = {
          'contents': [
            {
              'parts': [
                {'text': '$systemInstruction\n\nUser Question: $prompt'}
              ]
            }
          ],
          'generationConfig': {'temperature': 0.6, 'maxOutputTokens': 1200}
        };

        final response = await http.post(
          url,
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode(payload),
        );

        if (response.statusCode == 200) {
          final data = jsonDecode(response.body);
          final candidates = data['candidates'] as List?;
          if (candidates != null && candidates.isNotEmpty) {
            final parts = candidates[0]['content']['parts'] as List?;
            if (parts != null && parts.isNotEmpty) {
              return {
                'text': parts[0]['text'] as String,
                'model': 'Gemini ($model)',
              };
            }
          }
        }
      } catch (_) {}
    }
    throw Exception('Gemini API calls failed');
  }

  // --- 2. Groq Provider ---
  Future<Map<String, String>> _callGroq(String prompt) async {
    const modelsToTry = [
      'openai/gpt-oss-120b',
      'qwen/qwen3.8-27b',
      'qwen/qwen3.6-27b',
      'llama-3.3-70b-versatile',
      'groq/compound',
      'openai/gpt-oss-20b'
    ];

    final systemInstruction = _buildSystemPrompt(prompt);

    for (final model in modelsToTry) {
      try {
        final url = Uri.parse('https://api.groq.com/openai/v1/chat/completions');
        final payload = {
          'model': model,
          'messages': [
            {'role': 'system', 'content': systemInstruction},
            {'role': 'user', 'content': prompt}
          ],
          'temperature': 0.6,
          'max_tokens': 1200,
        };

        final response = await http.post(
          url,
          headers: {
            'Authorization': 'Bearer $_groqKey',
            'Content-Type': 'application/json',
          },
          body: jsonEncode(payload),
        );

        if (response.statusCode == 200) {
          final data = jsonDecode(response.body);
          final choices = data['choices'] as List?;
          if (choices != null && choices.isNotEmpty) {
            final content = choices[0]['message']['content'] as String;
            return {
              'text': content,
              'model': 'Groq ($model)',
            };
          }
        }
      } catch (_) {}
    }
    throw Exception('Groq API calls failed');
  }

  // --- 3. Local Ollama Provider ---
  Future<Map<String, String>> _callOllama(String prompt) async {
    final url = Uri.parse('$_ollamaHost/api/chat');
    final systemInstruction = _buildSystemPrompt(prompt);

    final payload = {
      'model': _ollamaModel,
      'messages': [
        {'role': 'system', 'content': systemInstruction},
        {'role': 'user', 'content': prompt}
      ],
      'stream': false,
      'options': {'num_predict': 350, 'temperature': 0.6}
    };

    final response = await http.post(
      url,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(payload),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      final content = data['message']['content'] as String;
      return {
        'text': content,
        'model': 'Local Ollama ($_ollamaModel)',
      };
    }
    throw Exception('Local Ollama instance unreachable');
  }

  // --- 4. Deep Offline Tactical Knowledge Synthesizer ---
  String _generateOfflineFallback(String query) {
    final q = query.toLowerCase();

    // 1. Specific Hero Queries
    if (q.contains('seigel')) {
      return '''
### 🛡️ Hero Dossier: Seigel — Generation 16 (Legendary Infantry)
• **Role:** The undisputed #1 frontline kinetic reflect tank in endgame Whiteout Survival.
• **Primary Skill (*Spike Guard*):** Extends armor spikes for 5s — boosts Defense by +25% and reflects 25% incoming damage back to attackers.
• **Expedition Skill (*Armor of Night*):** +25% Health for all squad troops and reduces enemy backline Attack by 35%.
• **Exclusive Gear (*Blacklight Halberd*):** Heals 25% of reflected damage as Health. Grants +15% defender Lethality.
• **Tactical Verdict:** Priority #1 investment for Gen 16 states. Pair with `Aisling (DPS) + Ursar` in a `50/20/30` formation.
''';
    }

    if (q.contains('aisling')) {
      return '''
### 🏹 Hero Dossier: Aisling — Generation 16 (Legendary Marksman)
• **Role:** High-velocity siege sniper & endgame backline burst DPS.
• **Primary Skill (*Moonpiercer*):** Line AOE attack dealing 380% burst with 60% armor penetration.
• **Expedition Multiplier:** Massive `+2,131.70%` Expedition power.
• **Exclusive Gear (*Silverwind Bow*):** Attacks ignore 35% target defense and adds +20% damage to rally troops.
• **Tactical Verdict:** The premier damage dealer in Gen 16. Prioritize general mythic shards to 4★ minimum.
''';
    }

    if (q.contains('ursar')) {
      return '''
### 🐎 Hero Dossier: Ursar — Generation 16 (Legendary Lancer)
• **Role:** Windbreaker Support DPS & debuff specialist (Hall of Heroes exclusive).
• **Primary Skill (*Toxic Gale*):** Spreads poison clouds causing 60% continuous DPS and slowing enemies by 20%.
• **Expedition Skill (*Windbreaker*):** All troops Attack +25% and reduces enemy frontline defense by 30%.
• **Tactical Verdict:** Acquire via weekly Hall of Heroes (Marks of Valor). Ideal third hero for Gen 16 rallies.
''';
    }

    if (q.contains('hank') || q.contains('viveca') || q.contains('estrella') || q.contains('gen 15') || q.contains('15')) {
      return '''
### 👑 Generation 15 Tactical Dossier
• **Active Window:** ~Day 1,080+ of server age (State 260–330 tier).
• **🔷 Hank (Infantry - Lucky Wheel):** Frontline endurance shield. Top Lucky Wheel target for Gen 15.
• **🔶 Estrella (Lancer):** Rapid flank burst dealer with high armor shred.
• **🔴 Viveca (Marksman):** Sustained backline siege DPS for Bear Trap and SvS.
• **Shard Advice:** Focus Lucky Wheel spins on Hank (Infantry). Save remaining generic mythic shards for Gen 16 Seigel.
''';
    }

    if (q.contains('bradley') || q.contains('edith') || q.contains('gordon') || q.contains('gen 7') || q.contains('generation 7')) {
      return '''
### 🛡️ Generation 7 Tactical Dossier
• **Active Window:** ~Day 400–479 of server age.
• **🔷 Bradley (Infantry - Lucky Wheel):** Fortress defense tank absorbing 30% max HP damage and stunning attackers.
• **🔴 Edith (Marksman):** Armor-piercing assassin designed to bypass enemy frontlines.
• **🔶 Gordon (Lancer):** Flank disruption and stun support.
• **Tactical Verdict:** Invest 100% of generic mythic shards into Bradley to 4★. He remains a viable fortress tank through Gen 10!
''';
    }

    if (q.contains('flint')) {
      return '''
### 🔥 Hero Dossier: Flint — Generation 2 (Mythic Infantry)
• **Role:** Frontline burn tank with Dragonbane flamethrower. #1 F2P Lucky Wheel target in Gen 2.
• **Unlock:** ~Day 40+ on Gen 2 Lucky Wheel.
• **Signature Skill (*Incinerator*):** Automatically heals **40% max HP** once per battle.
• **Exclusive Gear (*Dragonbane*):** After triggering Incinerator, gains **+24% Attack** until battle ends.
• **F2P Advice:** Reach 3-4★ on Lucky Wheel before saving generic shards for Gen 3.
''';
    }

    if (q.contains('alonso')) {
      return '''
### 🎯 Hero Dossier: Alonso — Generation 2 (Mythic Marksman)
• **Role:** High-burst ranged DPS with teamwide stun trapnet.
• **Skill (*Trapnet*):** AOE attack x280% + 1.5s stun.
• **Tactical Verdict:** Essential for Exploration (Arena) and Hero's Journey. Build alongside Flint.
''';
    }

    if (q.contains('jessie')) {
      return '''
### 🎖️ Hero Dossier: Jessie — Epic Core (The #1 Rally Joiner)
• **Role:** THE MOST IMPORTANT RALLY JOINER HERO IN WHITEOUT SURVIVAL.
• **Top-Right Skill (*Inspire* Lv. 5):** **+25% DAMAGE DEALT FOR THE ENTIRE ALLIANCE RALLY**.
• **Golden Rule:** ALWAYS send Jessie as your #1 hero when joining Bear Trap, Castle Battle, and SvS rallies!
• **Star Priority:** Max out to 5★ immediately using Epic General Shards.
''';
    }

    if (q.contains('sergey') || q.contains('patrick')) {
      return '''
### 🛡️ Epic Defense Champions: Sergey & Patrick
• **Sergey (Infantry):** First expedition skill (*Iron Defense*) reduces incoming damage by **-20%**. Top choice for early exploration tank and city wall defense.
• **Patrick (Infantry):** First expedition skill (*First Aid*) grants **+15% HP** to entire rally/garrison. Essential for Sunfire Castle defense and Crazy Joe HQ garrison.
• **Recommendation:** Max both heroes early. Keep Sergey as your primary early tank until Flint/Bradley.
''';
    }

    if (q.contains('mia') || q.contains('lynn') || q.contains('gwen') || q.contains('renee') || q.contains('hendrik')) {
      return '''
### 🏹 Mid-Game Lucky Wheel Carries (Gen 3 - 6)
• **Gen 3 Mia (Marksman):** Top Lucky Wheel priority. Essential for early Bear Trap damage spikes.
• **Gen 4 Lynn (Marksman):** High attack speed stun sniper. Build to 4★ on Lucky Wheel.
• **Gen 5 Gwen (Marksman):** Exceptional burst DPS carry for Gen 5 states.
• **Gen 6 Renee (Marksman) / Wayne (Infantry):** Renee brings high lethality backline DPS.
• **Strategy:** Save 120–160 Lucky Wheel spins per generation to guarantee 3-4★ on the featured hero without spending money.
''';
    }

    // 2. Events & Game Modes
    if (q.contains('crazy joe') || q.contains('joe')) {
      return '''
### 🧟 Crazy Joe Grandmaster Defense Guide
1. **Wave Mechanics:** Joe attacks alliance cities across 20 waves (~40 mins).
2. **HQ Waves (Waves 10 & 20):** Massive hordes march directly to Alliance HQ! All online members must recall defensive marches and reinforce HQ with Infantry/Lancers.
3. **The Reinforcement Rule:**
   • **NEVER send Marksmen out to reinforce allies or HQ!** Keep Marksmen stationed inside your own city barricade.
   • Send only **Infantry & Lancers** to reinforce online allies.
4. **Empty City Point Tactic:** Reinforcing offline/online alliance members scores double points while your garrison defends your city.
''';
    }

    if (q.contains('bear') || q.contains('trap')) {
      return '''
### 🐻 Bear Trap Grandmaster Strategy (Max DPS)
1. **Critical Joiner Rule:**
   • Personal hero gear/stats DO NOT apply when joining rallies.
   • **Only the TOP 4 joiners' first expedition skill (Top-Right)** buffs the rally!
2. **Best Joiner Lineups:**
   • **March 1:** `Jessie` (+25% Damage Dealt)
   • **March 2:** `Seo-yoon` (+20% Attack) or `Jeronimo` (+15% Damage)
   • **March 3 & 4:** Highest remaining attack hero.
3. **Troop Ratio:** Use **`10% Infantry / 10% Lancer / 80% Marksman`** (or `0/20/80`). The Bear cannot kill your troops, so maximize backline Marksman DPS!
4. **March Speed:** Relocate close to the trap before opening to keep march times under 15 seconds.
''';
    }

    if (q.contains('castle') || q.contains('sunfire') || q.contains('fortress') || q.contains('stronghold')) {
      return '''
### 🏰 Sunfire Castle & Garrison Defense Doctrine
1. **Optimal Troop Ratio:** Use **`60% Infantry / 20% Lancer / 20% Marksman`** (`60/20/20`). High infantry ensures the garrison wall survives sustained enemy rallies.
2. **Wall Captain Heroes:**
   • **Defense:** Use `Patrick` (+15% HP) or `Sergey` (-20% Damage Taken) as secondary leads.
   • **Endgame:** `Bradley` (Gen 7) or `Seigel` (Gen 16) for frontline barrier absorption.
3. **Turret Control:** Always secure at least 2 Turrets before rallying the Sunfire Castle to minimize incoming bombardment damage.
''';
    }

    if (q.contains('svs') || q.contains('state vs state') || q.contains('state of power')) {
      return '''
### 🏆 State vs State (SvS) War Playbook
1. **Prep Stage (Days 1–5):**
   • **Day 1:** Resource Gathering & Speedups.
   • **Day 2:** Chief Gear, Hero Gear & Charms.
   • **Day 3:** Pet Training & Tech Research.
   • **Day 4:** Hero Growth (Spend generic mythic shards & Lucky Wheel).
   • **Day 5:** Troop Training (Burn troop speedups during 20% buff).
2. **Battle Stage (Day 6):**
   • Sunfire Castle battle + Cross-State Kill Event (KE).
   • Keep bubble active when not rallying to avoid losing millions of power!
''';
    }

    if (q.contains('foundry') || q.contains('canyon') || q.contains('frostfire')) {
      return '''
### 🏭 Foundry Battle & Canyon Clash Strategy
• **Foundry Battle:** Prioritize capturing the Main Furnace and Munitions Factory early. Assign speed marchers to capture repair shops and keep boilers fortified.
• **Frostfire Mine:** Focus on high-level ore veins and crystal nodes. Avoid unnecessary PvP clashes early; score points through mining and boss objectives.
• **Canyon Clash:** Balanced 3-lane assault. Keep communication in voice or pin markers for coordinated lane pushes.
''';
    }

    // 3. Formations, Ratios & Lineups
    if (q.contains('ratio') || q.contains('formation') || q.contains('lineup') || q.contains('troops') || q.contains('50/20/30')) {
      return '''
### ⚔️ Tactical Troop Ratios & Formations
• 🛡️ **Standard PvP / Field Battle:** `50% Infantry / 20% Lancer / 30% Marksman` (`50/20/30`). Gives your marksmen the protection needed to deal max sustained damage.
• 🐻 **Bear Trap (Max PvE Damage):** `10% Infantry / 10% Lancer / 80% Marksman` (`10/10/80`). Maximizes sustained DPS against non-attacking targets.
• 🏰 **Castle Garrison Defense:** `60% Infantry / 20% Lancer / 20% Marksman` (`60/20/20`). Absorbs siege damage and resists multi-rallies.
• 🎯 **High Burst Attack (4-1-1):** `40% Infantry / 10% Lancer / 50% Marksman` (`40/10/50`). High risk, high reward against weaker opponents.

💡 **Golden Rule:** *Never let your Infantry drop below 40% in PvP or your marksmen will be wiped out immediately.*
''';
    }

    // 4. Upgrades, Shards & Chief Gear
    if (q.contains('gear') || q.contains('charm') || q.contains('upgrade') || q.contains('chief')) {
      return '''
### ⚙️ Chief Gear, Charms & Upgrade Priorities
1. **Chief Gear Upgrade Order:**
   • **Priority 1 (Frontline):** *Infantry Armor & Helmet* (Health & Defense).
   • **Priority 2 (DPS):** *Marksman Weapon & Boots* (Attack & Lethality).
   • **Priority 3:** Lancer gear.
2. **Chief Charms:** Always upgrade charms evenly across all pieces to unlock tier bonuses, prioritizing Infantry Health charms.
3. **Hero Exclusive Gear:**
   • Upgrade to **Level 10** for base skill unlock.
   • Level 20 & 30 grant massive rally stat bonuses.
''';
    }

    if (q.contains('shard') || q.contains('wheel') || q.contains('f2p') || q.contains('save')) {
      return '''
### 💎 Shard Management & Lucky Wheel Economy
1. **The Lucky Wheel Rule:**
   • Save **120–160 Wheel Spins** per generation.
   • Only spin for the premier meta heroes: `Flint (Gen 2)` ➔ `Mia (Gen 3)` ➔ `Lynn (Gen 4)` ➔ `Hector (Gen 5)` ➔ `Bradley (Gen 7)` ➔ `Seigel (Gen 16)`.
2. **Generic Mythic Shards:**
   • Never spend generic shards on heroes available through Intel or Hero Hall (like Molly or Zinman).
   • Hoard shards for your generation's primary Lucky Wheel tank or damage carry to reach 4★.
''';
    }

    if (q.contains('expert') || q.contains('academy') || q.contains('dawn')) {
      return '''
### 🎓 Dawn Academy Experts Guide
• **Unlock:** Furnace Lv 25 + Fire Crystal 1 (~Day 150+).
• **Strategic Pausing:** Never level experts blindly. Pause at breakpoint levels (**Lv 10, 20, 30**) where talent bonuses spike.
• **F2P Priority:** `Agnes` (Construction & Research speed) ➔ `Cyrille` (Healing & Training speed) ➔ `Baldur` (Event stamina & economy).
• **Combat Priority:** `Romulus` and `Valeria` for massive combat lethality.
''';
    }

    // 5. Generation Schedule Overview
    if (q.contains('generation') || q.contains('gen') || q.contains('schedule') || q.contains('state age')) {
      return '''
### 📅 Whiteout Survival Generation Roadmap
• **Gen 1 (Day 0):** `Jeronimo (Inf) · Natalia (Lan) · Molly (Mark)`
• **Gen 2 (Day 40):** `Flint (Inf) · Philly (Lan) · Alonso (Mark)`
• **Gen 3 (Day 120):** `Logan (Inf) · Greg (Lan) · Mia (Mark)`
• **Gen 4 (Day 180):** `Ahmose (Inf) · Reina (Lan) · Lynn (Mark)`
• **Gen 5 (Day 250):** `Hector (Inf) · Norah (Lan) · Gwen (Mark)`
• **Gen 6 (Day 320):** `Wayne (Inf) · Wu Ming (Lan) · Renee (Mark)`
• **Gen 7 (Day 400):** `Bradley (Inf) · Gordon (Lan) · Edith (Mark)`
• **Gen 8 (Day 480):** `Gatot (Inf) · Sonya (Lan) · Hendrik (Mark)`
• **Gen 9 (Day 550):** `Magnus (Inf) · Fred (Lan) · Xura (Mark)`
• **Gen 10 (Day 620):** `Gregory (Inf) · Freya (Lan) · Blanchette (Mark)`
• **Gen 11 (Day 690):** `Eleonora (Inf) · Lloyd (Lan) · Rufus (Mark)`
• **Gen 12 (Day 760):** `Hervor (Inf) · Karol (Lan) · Ligeia (Mark)`
• **Gen 13 (Day 830):** `Gisela (Inf) · Flora (Lan) · Vulcanus (Mark)`
• **Gen 14 (Day 900):** `Elif (Inf) · Dominic (Lan) · Cara (Mark)`
• **Gen 15 (Day 960):** `Hank (Inf) · Estrella (Lan) · Viveca (Mark)`
• **Gen 16 (Day 1080+):** `Seigel (Inf) · Ursar (Lan) · Aisling (Mark)`
''';
    }

    // 6. Dynamic Intelligent Fallback
    return '''
### ❄️ Frosty Grandmaster Tactical Advisory

**Tactical Analysis for:** *"$query"*

1. **Troop & Formation Strategy:**
   • For field battles, maintain a balanced **`50/20/30`** ratio (`50% Infantry, 20% Lancers, 30% Marksmen`).
   • For Bear Trap PvE, deploy **`10/10/80`** to maximize backline damage.
2. **Rally Joiner Priority:**
   • Always send **Jessie (+25% Damage)** or **Seo-yoon (+20% Attack)** in joiner slot #1.
3. **Hero Investment:**
   • Prioritize your server generation's Lucky Wheel hero to 3–4★ before saving generic mythic shards.

💡 *Ask me specifically about any hero (e.g. Seigel, Bradley, Flint), event (Crazy Joe, Bear Trap, SvS), or formation ratio for in-depth tactical math!*
''';
  }

  String _buildSystemPrompt(String query) {
    return '''You are Frosty, the premier Whiteout Survival Tactical Oracle and Grandmaster Military Advisor.
You possess complete mastery of Whiteout Survival mechanics, heroes (Gen 0 to Gen 16+), troop ratios (50/20/30, 10/10/80), Bear Trap rally joiner dynamics (Jessie +25% buff), Crazy Joe defense, and Dawn Academy Experts.

Deliver concise, highly actionable, expert answers formatted in clean Markdown with bold bullet points, emojis, and a clear tactical verdict.''';
  }
}
