import 'package:flutter/material.dart';
import 'package:conlang/screens/home_screen.dart';

class ConlangApp extends StatelessWidget {
  const ConlangApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Conlang',
      theme: ThemeData(
        colorSchemeSeed: Colors.deepPurple,
        useMaterial3: true,
        brightness: Brightness.light,
        fontFamily: 'NotoSerif',
      ),
      darkTheme: ThemeData(
        colorSchemeSeed: Colors.deepPurple,
        useMaterial3: true,
        brightness: Brightness.dark,
        fontFamily: 'NotoSerif',
      ),
      home: const HomeScreen(),
    );
  }
}
