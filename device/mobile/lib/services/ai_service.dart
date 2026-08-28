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

  String _geminiKey = envGeminiKey;
  String _groqKey = envGroqKey;
  String _ollamaHost = 'http://localhost:11434';
  String _ollamaModel = 'llama3.2:1b';
  String _selectedProvider = 'auto'; // 'auto', 'gemini', 'groq', 'ollama', 'offline'


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
      _ollamaHost = prefs.getString('custom_ollama_host') ?? 'http://localhost:11434';
      _ollamaModel = prefs.getString('custom_ollama_model') ?? 'llama3.2:1b';
      _selectedProvider = prefs.getString('selected_ai_provider') ?? 'auto';
      notifyListeners();
    } catch (_) {}
  }

  Future<void> updateSettings({
    String? geminiKey,
    String? groqKey,
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
      if (_selectedProvider == 'gemini') {
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
        // 1. Try Gemini
        try {
          final result = await _callGemini(cleanText).timeout(const Duration(seconds: 10));
          botAnswer = result['text']!;
          modelUsed = result['model']!;
        } catch (_) {
          // 2. Fallback to Groq
          try {
            final result = await _callGroq(cleanText).timeout(const Duration(seconds: 10));
            botAnswer = result['text']!;
            modelUsed = result['model']!;
          } catch (_) {
            // 3. Fallback to Ollama
            try {
              final result = await _callOllama(cleanText).timeout(const Duration(seconds: 5));
              botAnswer = result['text']!;
              modelUsed = result['model']!;
            } catch (_) {
              // 4. Fallback to Offline Tactical Core
              botAnswer = _generateOfflineFallback(cleanText);
              modelUsed = 'Offline Tactical Core';
            }
          }
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

  // --- 4. Offline Tactical Knowledge Synthesizer ---
  String _generateOfflineFallback(String query) {
    final q = query.toLowerCase();

    if (q.contains('bear') || (q.contains('rally') && q.contains('join'))) {
      return '''
### 🐻 Bear Trap & Rally Joiner Master Guide

**1. Critical Rally Joiner Rule:**
• In Whiteout Survival, when you **join** an alliance rally, your personal hero stats do *not* buff the rally march.
• **Only the TOP 4 rally joiners' first expedition skill (Top-Right Skill)** buffs the entire alliance rally damage!

**2. Optimal Joiner Hero Setup:**
• **Joiner March 1 (Leader):** `Jessie` (Top-Right Skill: **+25% Damage Dealt** to entire rally).
• **Joiner March 2 (Leader):** `Seo-yoon` (+20% Attack) or `Jeronimo` (+15% Attack/Damage).
• **Joiner March 3 (Leader):** Highest remaining marksman damage hero.

**3. Troop Distribution Ratio:**
• Use **`10% Infantry / 10% Lancer / 80% Marksman`** (or `0/20/80`). Bear Trap never kills your troops, so maximize backline Marksman DPS!

💡 **Grandmaster Tip:** *Keep march times short (<15s) by gathering around the trap before opening!*
''';
    }

    if (q.contains('16') || q.contains('seigel') || q.contains('aisling') || q.contains('ursar')) {
      return '''
### 👑 Generation 16 (Legendary) Tactical Dossier

Generation 16 unlocks around **Day 1,160+** of server age (~80 days after Gen 15) with massive **+2,131.70%** Expedition multipliers.

**1. 🛡️ Seigel (Legendary Infantry):**
• **Role:** Ultra-tanky frontline reflect shield & Night's Guard veteran.
• **Skill (Spike Guard):** Extends spike armor for 5s — Defense +25% and reflects 25% damage back.
• **Exclusive Gear:** *Blacklight Halberd* (heals 25% of reflected damage as Health).

**2. 🏹 Aisling (Legendary Marksman):**
• **Role:** High-velocity siege sniper & endgame backline burst DPS.
• **Strengths:** Highest marksman lethal multiplier in Whiteout Survival history.

**3. 🐎 Ursar (Legendary Lancer):**
• **Role:** Windbreaker Support DPS & debuff applicator (Hall of Heroes exclusive).

💡 **PvP Squad:** `Seigel (Lead) + Aisling (DPS) + Ursar` with `50/20/30` ratio.
''';
    }

    if (q.contains('flint')) {
      return '''
### 🔥 Hero Dossier: Flint — Generation 2 (Mythic Infantry)

**Role & Overview:**
• Gen 2 Mythic Infantry / Combat — frontline burn tank & Dragonbane flamethrower specialist.
• **Unlock:** ~Day 40+ on Gen 2 Lucky Wheel.

**Key Multipliers:**
• Expedition: Infantry Attack `+240.19%` · Infantry Defense `+240.19%`.
• Skill (Incinerator): Automatically heals **40% max HP** once per battle.

**Exclusive Gear (Dragonbane):**
• After triggering Incinerator, gains **+24% Attack** until battle ends. +15% defender Attack.

💰 **F2P Advice:** *The #1 must-have Lucky Wheel hero in Gen 2. Build to 3-4★ before saving generic shards.*
''';
    }

    if (q.contains('lineup') || q.contains('ratio') || q.contains('formation')) {
      return '''
### ⚔️ Tactical Troop Ratios & Formations

In Whiteout Survival, a standard march consists of **3 Hero Slots** (1 Leader + 2 Deputies) and **3 Troop Types**:

**Standard Tactical Troop Ratios:**
• 🛡️ **Standard PvP / Field Battle:** `50% Infantry / 20% Lancer / 30% Marksman` (`50/20/30`)
• 🐻 **Bear Trap (Max PvE Damage):** `10% Infantry / 10% Lancer / 80% Marksman` (`10/10/80`)
• 🏰 **Castle Garrison Defense:** `60% Infantry / 20% Lancer / 20% Marksman` (`60/20/20`)
• 🎯 **High Burst 4-1-1 Attack:** `40% Infantry / 10% Lancer / 50% Marksman` (`40/10/50`)

💡 **Golden Rule:** *Never let your Infantry drop below 40-50% in PvP or your marksmen will be eliminated immediately.*
''';
    }

    return '''
### ❄️ Frosty Tactical Advisory

**Whiteout Survival Combat Principles:**
1. **Hero Synergy:** Always deploy 1 frontline Infantry hero (Flint/Bradley/Seigel), 1 Lancer, and 1 backline Marksman (Alonso/Edith/Aisling).
2. **Rally Mechanics:** In alliance rallies, only the top 4 joiners' first skill applies (+25% Jessie, +20% Seo-yoon).
3. **Defense Shield:** Maintain at least 50% Infantry in field battles and castle garrisons.

💡 *Synthesized directly from Frosty's verified Whiteout Survival offline archives.*
''';
  }

  String _buildSystemPrompt(String query) {
    return '''You are Frosty, the premier Whiteout Survival Tactical Oracle and Grandmaster Military Advisor.
You possess complete mastery of Whiteout Survival mechanics, heroes (Gen 0 to Gen 16+), troop ratios (50/20/30, 10/10/80), Bear Trap rally joiner dynamics (Jessie +25% buff), Crazy Joe defense, and Dawn Academy Experts.

Deliver concise, highly actionable, expert answers formatted in clean Markdown with bold bullet points, emojis, and a clear tactical verdict.''';
  }
}
