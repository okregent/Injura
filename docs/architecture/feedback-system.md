# Injura — Feedback System

## Philosophy
Feedback avoids rigid hardcoded rules and instead supports a configurable rule system.

## Rule File Structure
```
rules/
├── squat_rules.yaml
├── deadlift_rules.yaml
└── future_rules.yaml
```

## Design Principles
- Rules and thresholds must be configurable, not hardcoded
- Feedback must be explainable to the user
- Adaptive thresholds based on user profile (body proportions, mobility, discomfort)
