import 'package:flutter_test/flutter_test.dart';
import 'package:mindsense_burnout/main.dart';

void main() {
  testWidgets('App basic smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(const MindSenseApp());
    expect(find.byType(MindSenseApp), findsOneWidget);
  });
}
