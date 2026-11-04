# Configured Measurement Rules

Implementation is on `feature/biomechanics`. `engine/squat/rules.py` compares
explicit caller conditions against measured repetitions. It supplies no
validated coaching thresholds, posture grades or medical inference.

`MeasurementRule` fields: `id`, `metric`, `field` (null for scalar outcomes),
`comparator`, `threshold`, `message`, and `enabled` (defaults to false).
Comparators are `gt`, `gte`, `lt`, `lte`, `eq`, `ne`; equality is exact numeric
equality. Thresholds must be finite numbers, not booleans. IDs must be unique.
Unknown fields, targets and comparators are rejected; configuration executes no
expressions. Callers own threshold meaning and message wording.

| Metric | Field | Unit |
|---|---|---|
| timing | total_seconds, descent_seconds, bottom_seconds, ascent_seconds | seconds |
| knee_flexion, hip_flexion | null | degrees |
| torso_lean | max_lean_angle, lean_change | degrees |
| depth | depth_ratio | dimensionless ratio |

`load_rules(path)` accepts JSON containing only a `rules` list. The committed
`engine/squat/squat_rules.json` is empty. No default active technique rules or
new dependencies are introduced. YAML and adaptive profiles are deferred.
Apply a file explicitly through `tools.review_samples --rules PATH`.

`evaluate_rules(analysis, rules)` returns one result per measured repetition and
rule, with status `matched`, `not_matched`, `withheld`, or `disabled`. Evidence
contains the one-based repetition, rule ID, metric/field, comparator, threshold,
unit, usable observed value and message or withholding reason. Only matches
carry configured messages; nonmatches do not imply good technique.

Candidates are never evaluated. Missing/nonfinite values, partial/unavailable
quality, recovered observations and experimental calibration withhold evaluation.
Disabled rules remain disabled regardless of measurement quality. Full coverage
does not establish anatomical accuracy; matches are numeric comparisons only.
No automatic side/model selection or metric mutation occurs.

Enabled rules also require an approved, side-matched human recording review for
their metric. Missing/unknown/rejected review withholds interpretation without
erasing raw measurements. See [recording review](recording-review.md).

Review JSON records `configured_rules` and side-specific `rule_evaluations`;
HTML renders configured results with evidence. Availability notices remain
separate. Empty rules preserve prior measurements and report behavior.
