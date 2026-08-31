import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:url_launcher/url_launcher.dart';

class UpdateService {
  static const String currentVersion =
      String.fromEnvironment('APP_VERSION', defaultValue: '1.0.0');
  static String latestVersionTag = '';
  static const String githubApiUrl =
      'https://api.github.com/repos/Zcross091/frosty-wos-ai/releases/latest';

  /// Checks GitHub API for the latest release and displays an update pop-up ONLY if a newer version is available.
  static Future<void> checkForUpdates(BuildContext context, {bool manualCheck = false}) async {
    try {
      final response = await http
          .get(
            Uri.parse(githubApiUrl),
            headers: {'Accept': 'application/vnd.github.v3+json'},
          )
          .timeout(const Duration(seconds: 6));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final rawTag = data['tag_name'] as String? ?? '';
        final cleanTag = rawTag.toLowerCase().replaceAll('v', '').split('+').first.trim();
        latestVersionTag = cleanTag;
        final releaseName = data['name'] as String? ?? 'New Frosty Release';
        final releaseBody = data['body'] as String? ?? 'A new version of Frosty WOS AI is now available.';
        final htmlUrl = data['html_url'] as String? ?? 'https://github.com/Zcross091/frosty-wos-ai/releases';

        // Check for APK asset URL in release assets
        String? apkDownloadUrl;
        final assets = data['assets'] as List?;
        if (assets != null) {
          for (final asset in assets) {
            final name = asset['name'] as String? ?? '';
            if (name.endsWith('.apk')) {
              apkDownloadUrl = asset['browser_download_url'] as String?;
              break;
            }
          }
        }
        final targetUrl = apkDownloadUrl ?? htmlUrl;

        // ONLY trigger update dialog if latest tag is strictly newer than current installed version
        if (_isNewerVersion(currentVersion, cleanTag)) {
          final prefs = await SharedPreferences.getInstance();
          final lastSkipped = prefs.getString('last_skipped_version');

          // If manual check or user has not dismissed this specific version
          if (manualCheck || lastSkipped != cleanTag) {
            if (context.mounted) {
              _showUpdateDialog(
                context,
                latestVersion: cleanTag,
                releaseTitle: releaseName,
                releaseNotes: releaseBody,
                downloadUrl: targetUrl,
              );
            }
          }
        } else if (manualCheck) {
          if (context.mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(
                content: Text('✅ Frosty is up to date (v$currentVersion)'),
                backgroundColor: Color(0xFF22C55E),
              ),
            );
          }
        }
      }
    } catch (_) {
      if (manualCheck && context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('⚠️ Unable to check GitHub for updates. Check internet connection.'),
            backgroundColor: Color(0xFFEF4444),
          ),
        );
      }
    }
  }

  /// Semver comparison: returns TRUE ONLY if latest > current
  static bool _isNewerVersion(String current, String latest) {
    if (latest.isEmpty) return false;
    try {
      final cleanCurrent = current.toLowerCase().replaceAll('v', '').split('+').first.trim();
      final cleanLatest = latest.toLowerCase().replaceAll('v', '').split('+').first.trim();

      if (cleanCurrent == cleanLatest) return false;

      final curParts = cleanCurrent.split('.').map((e) => int.tryParse(e) ?? 0).toList();
      final latParts = cleanLatest.split('.').map((e) => int.tryParse(e) ?? 0).toList();

      final maxLen = curParts.length > latParts.length ? curParts.length : latParts.length;
      for (int i = 0; i < maxLen; i++) {
        final cur = i < curParts.length ? curParts[i] : 0;
        final lat = i < latParts.length ? latParts[i] : 0;
        if (lat > cur) return true;
        if (lat < cur) return false;
      }
    } catch (_) {}
    return false;
  }

  static void _showUpdateDialog(
    BuildContext context, {
    required String latestVersion,
    required String releaseTitle,
    required String releaseNotes,
    required String downloadUrl,
  }) {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (ctx) {
        return Dialog(
          backgroundColor: const Color(0xFF0F192C),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(22),
            side: const BorderSide(color: Color(0xFF00F0FF), width: 1.5),
          ),
          child: Padding(
            padding: const EdgeInsets.all(22),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Header Icon & Title
                Row(
                  children: [
                    Container(
                      width: 44,
                      height: 44,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: const Color(0xFF00F0FF).withOpacity(0.15),
                        border: Border.all(color: const Color(0xFF00F0FF), width: 1.5),
                      ),
                      child: const Center(
                        child: Text('🚀', style: TextStyle(fontSize: 22)),
                      ),
                    ),
                    const SizedBox(width: 14),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            'New Update Available!',
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 17,
                              fontWeight: FontWeight.bold,
                              fontFamily: 'Outfit',
                            ),
                          ),
                          Text(
                            'v$latestVersion (Current: v$currentVersion)',
                            style: const TextStyle(
                              color: Color(0xFF00F0FF),
                              fontSize: 12.5,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),

                // Release Title
                Text(
                  releaseTitle,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 14,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 8),

                // Release Notes Container
                Container(
                  constraints: const BoxConstraints(maxHeight: 160),
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.black.withOpacity(0.35),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: const Color(0xFF38BDF8).withOpacity(0.2)),
                  ),
                  child: SingleChildScrollView(
                    child: Text(
                      releaseNotes,
                      style: const TextStyle(
                        color: Color(0xFFCBD5E1),
                        fontSize: 12,
                        height: 1.4,
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: 20),

                // Action Buttons
                Row(
                  children: [
                    Expanded(
                      child: TextButton(
                        onPressed: () async {
                          final prefs = await SharedPreferences.getInstance();
                          await prefs.setString('last_skipped_version', latestVersion);
                          if (ctx.mounted) Navigator.pop(ctx);
                        },
                        child: const Text(
                          'Later',
                          style: TextStyle(
                            color: Color(0xFF94A3B8),
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      flex: 2,
                      child: ElevatedButton.icon(
                        icon: const Icon(Icons.download_rounded, size: 18),
                        label: const Text(
                          'Update Now',
                          style: TextStyle(
                            fontWeight: FontWeight.bold,
                            fontFamily: 'Outfit',
                          ),
                        ),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: const Color(0xFF00F0FF),
                          foregroundColor: const Color(0xFF040914),
                          padding: const EdgeInsets.symmetric(vertical: 12),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(14),
                          ),
                        ),
                        onPressed: () async {
                          Navigator.pop(ctx);
                          final uri = Uri.parse(downloadUrl);
                          try {
                            await launchUrl(uri, mode: LaunchMode.externalApplication);
                          } catch (_) {}
                        },
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}
