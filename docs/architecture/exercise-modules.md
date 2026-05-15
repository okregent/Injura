# Injura — Exercise Module Architecture

## Modular Structure
```
ExerciseAnalyzer (Base)
├── SquatAnalyzer
├── DeadliftAnalyzer
├── PushupAnalyzer
└── Future Modules
```

## Design Rules
- Each exercise module independently manages movement rules, thresholds, and feedback logic
- Modules must be independently extendable without affecting others
- MVP implements SquatAnalyzer only
