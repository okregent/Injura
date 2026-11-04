# Recording Review and Interpretation Gates

Implemented on `feature/biomechanics`. `engine/squat/recording.py` provides
side-specific `RecordingReview` records and item-specific `recording_gate`.
Each condition is true (reviewed support), false (known failure), or null
(unknown). No detector confidence or user checklist automatically fills it.

A record contains `side` (left/right), optional `reviewer`, `notes`, and flags:
`side_view`, `camera_fixed`, `subject_clear`, `hips_visible`, `knees_visible`,
`ankles_visible`, `shoulders_visible`, `feet_visible`, `foot_side_on`,
`continuous_original_speed`, and `constant_frame_rate`. Flags require actual
booleans or null; an empty reviewer is invalid. A missing reviewer is unapproved.
Review the selected side and whole clip; interval-specific approval is not yet
supported. A failed whole-clip condition may conservatively withhold that item.

All supported items require reviewed side view, fixed camera and unambiguous
subject. Additional required conditions depend on the metric:

| Metric | Additional reviewed conditions |
|---|---|
| depth | hips |
| timing | hips, continuous original speed, constant cadence |
| knee flexion | hips, knees, ankles |
| hip flexion | shoulders, hips, knees |
| torso lean | shoulders, hips |
| hip-to-knee gap | hips, knees |
| knee travel | knees, feet |
| foot-normalized knee travel | knees, feet, side-on foot orientation |
| heel rise | feet |

Unknown/missing review, reviewer or selected-side mismatch returns `unknown`.
A required false flag returns `rejected`; known failures precede other unknown
flags. All required flags true return `approved`. Approval describes reviewed
capture support only, not joint accuracy, good technique or coaching validation.
For example uncertain cadence withholds timing without rejecting visible angles.

`evaluate_rules(..., recording_review=review)` withholds enabled rules unless the
metric gate is approved. Disabled rules remain disabled; quality, recovered-frame
and experimental-calibration gates still apply after capture review. Raw metric
values, detected repetitions, candidates and availability notices are preserved.

## Source-Bound CLI Workflow

```bash
python -m tools.prepare_recording_review sample_video3.mp4 --output artifacts/sample-review/recording-review-video3.json
python -m tools.review_samples sample_video3.mp4 --facing left --reuse-extraction --recording-review artifacts/sample-review/recording-review-video3.json --rules engine/squat/squat_rules.json
```

The first command writes an unapproved template with both sides, null flags and
no reviewer; it refuses to overwrite an existing file. Complete only conditions
actually reviewed. No frame-by-frame labeling is required by this record.

File schema contains only `video`, `size`, `mtime_ns`, and `reviews`. The loader
checks exact source filename, byte count and modification time, plus unique
sides, before extraction. Ordinary stale/wrong-file reviews are rejected.
This is metadata binding, not a content hash or proof of reviewer truthfulness.
In-memory library callers must bind their review to their extraction themselves.

Reports retain reviewer/notes and per-item `recording_gates`; HTML and summary
dashboard distinguish approval, unknown and rejection. Older reports lacking
gates are displayed as unknown. Signed side/foot flags are mapped to the
existing foot-normalization recording conditions; metric masks still apply.
The CLI facing-direction input remains explicit and is not inferred by review.

Default rules remain empty and absent review remains unknown. No default
technique limits or automated recording classifier are introduced. Next define
the versioned validation manifest and predeclared acceptance limits under
[E3 acceptance](../validation/E3_ACCEPTANCE.md).
