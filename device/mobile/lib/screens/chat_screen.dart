import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:provider/provider.dart';
import '../services/ai_service.dart';
import '../widgets/typing_indicator.dart';

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final TextEditingController _textController = TextEditingController();
  final ScrollController _scrollController = ScrollController();

  final List<String> _quickPrompts = [
    '🐻 Bear Trap Joiner Lineup',
    '👑 Write about Generation 16',
    '🔥 How to build Flint (Gen 2)',
    '⚔️ Best PvP 50/20/30 Squad',
    '🎯 Crazy Joe Wave 10/20 Guide',
  ];

  @override
  void dispose() {
    _textController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  void _send(AIService aiService, String text) {
    if (text.trim().isEmpty) return;
    _textController.clear();
    aiService.sendMessage(text);
    _scrollToBottom();
  }

  @override
  Widget build(BuildContext context) {
    final aiService = Provider.of<AIService>(context);

    // Auto-scroll when messages change or generation starts/ends
    WidgetsBinding.instance.addPostFrameCallback((_) => _scrollToBottom());

    return Scaffold(
      backgroundColor: const Color(0xFF060B13),
      appBar: AppBar(
        backgroundColor: const Color(0xFF0A111F).withOpacity(0.9),
        elevation: 0,
        title: Row(
          children: [
            Container(
              width: 32,
              height: 32,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: const Color(0xFF00F0FF).withOpacity(0.15),
                border: Border.all(color: const Color(0xFF00F0FF), width: 1.2),
              ),
              child: const Center(
                child: Text('❄️', style: TextStyle(fontSize: 16)),
              ),
            ),
            const SizedBox(width: 10),
            const Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Frosty AI Tactical Oracle',
                  style: TextStyle(
                    fontFamily: 'Outfit',
                    fontWeight: FontWeight.bold,
                    fontSize: 16,
                    color: Colors.white,
                  ),
                ),
                Text(
                  'Gemini 3.6 • Groq • Ollama • Gen 0-16+',
                  style: TextStyle(
                    fontSize: 11,
                    color: Color(0xFF00F0FF),
                  ),
                ),
              ],
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded, color: Color(0xFF94A3B8)),
            tooltip: 'Clear Chat History',
            onPressed: () => aiService.clearConversation(),
          ),
        ],
      ),
      body: Column(
        children: [
          // Quick Suggestion Chips
          Container(
            height: 48,
            padding: const EdgeInsets.symmetric(vertical: 6),
            child: ListView.builder(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 12),
              itemCount: _quickPrompts.length,
              itemBuilder: (context, index) {
                final prompt = _quickPrompts[index];
                return Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: ActionChip(
                    backgroundColor: const Color(0xFF0F192C),
                    side: BorderSide(
                      color: const Color(0xFF00F0FF).withOpacity(0.3),
                      width: 1,
                    ),
                    label: Text(
                      prompt,
                      style: const TextStyle(
                        color: Color(0xFFE2E8F0),
                        fontSize: 11.5,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    onPressed: () => _send(aiService, prompt),
                  ),
                );
              },
            ),
          ),

          const Divider(height: 1, color: Color(0xFF1E293B)),

          // Messages List
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              padding: const EdgeInsets.all(16),
              itemCount: aiService.messages.length + (aiService.isGenerating ? 1 : 0),
              itemBuilder: (context, index) {
                // Show Typing/Cooking Indicator at the bottom if generating
                if (index == aiService.messages.length) {
                  return const FrostyTypingIndicator();
                }

                final msg = aiService.messages[index];
                return _buildMessageBubble(msg);
              },
            ),
          ),

          // Message Input Field
          _buildInputBar(aiService),
        ],
      ),
    );
  }

  Widget _buildMessageBubble(dynamic msg) {
    final isUser = msg.isUser;

    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 6),
        constraints: BoxConstraints(
          maxWidth: MediaQuery.of(context).size.width * 0.88,
        ),
        decoration: BoxDecoration(
          color: isUser
              ? const Color(0xFF0284C7)
              : const Color(0xFF0F192C),
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(18),
            topRight: const Radius.circular(18),
            bottomLeft: Radius.circular(isUser ? 18 : 4),
            bottomRight: Radius.circular(isUser ? 4 : 18),
          ),
          border: Border.all(
            color: isUser
                ? const Color(0xFF38BDF8)
                : const Color(0xFF00F0FF).withOpacity(0.3),
            width: 1,
          ),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.3),
              blurRadius: 10,
              offset: const Offset(0, 3),
            ),
          ],
        ),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Markdown Content
              MarkdownBody(
                data: msg.content,
                selectable: true,
                styleSheet: MarkdownStyleSheet(
                  p: const TextStyle(
                    color: Color(0xFFF1F5F9),
                    fontSize: 13.5,
                    height: 1.45,
                  ),
                  h3: const TextStyle(
                    color: Color(0xFF00F0FF),
                    fontSize: 15,
                    fontWeight: FontWeight.bold,
                    fontFamily: 'Outfit',
                  ),
                  h4: const TextStyle(
                    color: Colors.white,
                    fontSize: 13.5,
                    fontWeight: FontWeight.bold,
                  ),
                  code: const TextStyle(
                    backgroundColor: Color(0xFF030712),
                    color: Color(0xFF38BDF8),
                    fontFamily: 'monospace',
                    fontSize: 12,
                  ),
                  listBullet: const TextStyle(
                    color: Color(0xFF00F0FF),
                  ),
                ),
              ),

              if (!isUser && msg.modelUsed != null) ...[
                const SizedBox(height: 8),
                const Divider(height: 1, color: Color(0xFF334155)),
                const SizedBox(height: 6),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      '⚡ ${msg.modelUsed}',
                      style: const TextStyle(
                        color: Color(0xFF64748B),
                        fontSize: 10.5,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    if (msg.latencySeconds != null && msg.latencySeconds! > 0)
                      Text(
                        '${msg.latencySeconds!.toStringAsFixed(2)}s',
                        style: const TextStyle(
                          color: Color(0xFF64748B),
                          fontSize: 10.5,
                        ),
                      ),
                  ],
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildInputBar(AIService aiService) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: const Color(0xFF0A111F),
        border: Border(
          top: BorderSide(color: const Color(0xFF00F0FF).withOpacity(0.2)),
        ),
      ),
      child: SafeArea(
        child: Row(
          children: [
            Expanded(
              child: TextField(
                controller: _textController,
                textInputAction: TextInputAction.send,
                onSubmitted: (val) => _send(aiService, val),
                style: const TextStyle(color: Colors.white, fontSize: 14),
                decoration: InputDecoration(
                  hintText: 'Ask Frosty tactical question...',
                  hintStyle: const TextStyle(color: Color(0xFF64748B), fontSize: 13),
                  filled: true,
                  fillColor: const Color(0xFF0F192C),
                  contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(24),
                    borderSide: BorderSide(color: const Color(0xFF00F0FF).withOpacity(0.3)),
                  ),
                  focusedBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(24),
                    borderSide: const BorderSide(color: Color(0xFF00F0FF), width: 1.5),
                  ),
                ),
              ),
            ),
            const SizedBox(width: 8),
            Container(
              decoration: const BoxDecoration(
                shape: BoxShape.circle,
                gradient: LinearGradient(
                  colors: [Color(0xFF00F0FF), Color(0xFF0088FF)],
                ),
              ),
              child: IconButton(
                icon: aiService.isGenerating
                    ? const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: Color(0xFF040914),
                        ),
                      )
                    : const Icon(Icons.send_rounded, color: Color(0xFF040914)),
                onPressed: aiService.isGenerating
                    ? null
                    : () => _send(aiService, _textController.text),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
