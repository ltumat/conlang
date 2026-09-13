import 'package:flutter/material.dart';
import 'package:conlang/screens/home_screen.dart';

class ConlangApp extends StatelessWidget {
  const ConlangApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Conlang',
      theme: ThemeData(
        useMaterial3: true,
        brightness: Brightness.light,
        fontFamily: 'NotoSerif',
        scaffoldBackgroundColor: const Color(0xFFF0F0F0),
        colorScheme: const ColorScheme.light(
          primary: Colors.black,
          onPrimary: Colors.white,
          secondary: Colors.black,
          onSecondary: Colors.white,
          tertiary: Colors.black,
          onTertiary: Colors.white,
          surface: Colors.white,
          onSurface: Colors.black,
          surfaceContainerHighest: Color(0xFFE0E0E0),
          surfaceContainerHigh: Color(0xFFE8E8E8),
          surfaceContainerLow: Color(0xFFF5F5F5),
          onSurfaceVariant: Color(0xFF555555),
          outlineVariant: Color(0xFFCCCCCC),
          error: Color(0xFFBA1A1A),
          onError: Colors.white,
        ),
      ),
      darkTheme: ThemeData(
        useMaterial3: true,
        brightness: Brightness.dark,
        fontFamily: 'NotoSerif',
        scaffoldBackgroundColor: const Color(0xFF1A1A1A),
        colorScheme: const ColorScheme.dark(
          primary: Colors.white,
          onPrimary: Colors.black,
          secondary: Colors.white,
          onSecondary: Colors.black,
          tertiary: Colors.white,
          onTertiary: Colors.black,
          surface: Color(0xFF222222),
          onSurface: Colors.white,
          surfaceContainerHighest: Color(0xFF2A2A2A),
          surfaceContainerHigh: Color(0xFF282828),
          surfaceContainerLow: Color(0xFF242424),
          onSurfaceVariant: Color(0xFF999999),
          outlineVariant: Color(0xFF333333),
          error: Color(0xFFEF9A9A),
          onError: Colors.black,
        ),
      ),
      home: const HomeScreen(),
    );
  }
}