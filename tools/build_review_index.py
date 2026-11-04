"""Build the local comparison index: python -m tools.build_review_index."""

import argparse
import html
import json
from pathlib import Path


def build_index(root: Path):
    rows = []
    for folder in sorted(root.glob("sample_video*")):
        path = folder / "analysis.json"
        if not path.exists():
            continue
        current = json.loads(path.read_text(encoding="utf-8"))
        baseline_path = folder / "baseline-analysis.json"
        baseline = json.loads(baseline_path.read_text(encoding="utf-8")) if baseline_path.exists() else None
        for side, data in current["sides"].items():
            before = baseline["sides"][side] if baseline else None
            timed = lambda item: sum(rep["metrics"]["timing"]["value"] is not None for rep in item["repetitions"])
            row = [
                f'<a href="{html.escape(folder.name)}/index.html">{html.escape(current["video"])}</a>',
                side,
                str(len(before["repetitions"])) if before else "unavailable",
                str(len(data["repetitions"])), str(len(data.get("candidates", []))),
                str(timed(before)) if before else "unavailable", str(timed(data)),
                str(len(current.get("recovered_frame_indices", []))),
                html.escape(data.get("calibration_method", "sequence_extrema")),
            ]
            rows.append("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>")
    parts = [
        '<!doctype html><html lang="en"><meta charset="utf-8"><title>Sample analysis investigation</title>',
        '<style>body{font:16px system-ui;margin:32px;color:#172030;max-width:1200px;line-height:1.6}'
        'table{border-collapse:collapse;width:100%}th,td{border:1px solid #ccd;padding:9px}th{background:#eef}'
        '.note{background:#fff2cf;padding:16px;border-left:4px solid #bd8a1e}img{max-width:100%}</style>',
        '<h1>Sample analysis: causes and revised results</h1>',
        ('<p><a href="count-evaluation.html">User-reported counts and count-only evaluation</a></p>'
         if (root / "count-evaluation.html").exists() else ''),
        ('<p><a href="manual-review.html">Manual video review and annotation templates</a></p>'
         if (root / "manual-review.html").exists()
         else '<p>Generate manual review with python -m tools.prepare_manual_review.</p>'),
        '<div class="note">Counts are detector outputs, not annotated ground truth. '
        'Uninterrupted detections and gap-crossing review candidates are separate. '
        'Candidates have no metric values or phase timing and never enter consistency statistics.</div>',
        '<p>Opt-in experimental reports may use source-image re-detection and posture-based calibration. '
        'Defaults are unchanged. Re-detected measurements remain marked for review; count agreement '
        'alone does not validate joint accuracy or timing boundaries.</p>',
        '<h2>Before / after</h2><p>Timings counts indicate how many detected repetitions have '
        'all three phase durations available. Body sides are compared, not automatically selected.</p>',
        '<table><tr><th>Video</th><th>Body side</th><th>Previous detections</th><th>Uninterrupted detections</th>'
        '<th>Unverified candidates</th><th>Previous timings</th><th>Current timings</th>'
        '<th>Source re-detections</th><th>Calibration</th></tr>',
        *rows, '</table>',
        '<h2>Findings</h2><ol>'
        '<li><b>Phase direction chatter:</b> raw frame-to-frame hip displacement changed sign with small noise. '
        'The revised cycle state retains descent/ascent and uses distinct bottom entry/exit thresholds. '
        'A genuine return to bottom after ascent remains explicit and still invalidates ordered phase timing.</li>'
        '<li><b>Aborted descent retained:</b> a small descent followed by standing did not cancel the pending rep. '
        'The next squat inherited an old start and idle standing frames. Returning to standing now cancels incomplete descent.</li>'
        '<li><b>Initial partial cycles:</b> an observation span starting mid-motion previously counted as complete. '
        'Revised detection requires observed standing before descent. The initial conservative review '
        'reclassified video 5 detections as candidates; source-image recovery is evaluated separately.</li>'
        '<li><b>Occlusion at the bottom:</b> video 6 loses source poses around squat bottoms. '
        'Optional tracking across gaps of at most 0.2 seconds identifies candidates only. '
        'No missing coordinate, angle, phase time, or true-bottom claim is reconstructed.</li></ol>',
        '<h2>Review still needed</h2><p>Manually check candidate boundaries, actual repetitions, and camera suitability. '
        'Preparation movement can affect global standing calibration and candidate start locations, especially video 6. '
        'No accuracy claim or automatic foot-orientation approval is made. See each recording for source frame ranges, '
        'candidate images, exclusions, CSV, and JSON.</p>',
    ]
    if (root / "hip-diagnostics.png").exists():
        parts.append('<h2>Observed hip trajectories</h2><p>Raw valid hip coordinates; red lines show the original '
                     'standing/bottom entry thresholds. Missing observations remain gaps. The revised bottom exit '
                     'uses 75% of the calibrated range, while entry remains at 85%.</p>'
                     '<img src="hip-diagnostics.png" alt="Observed hip trajectories for recordings 3 to 6">')
    if (root / "recordings-overview.jpg").exists():
        parts.append('<h2>Recording overview</h2><img src="recordings-overview.jpg" alt="Recording overview">')
    parts.append('</html>')
    (root / "index.html").write_text("\n".join(parts), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("artifacts/sample-review"))
    build_index(parser.parse_args().root)
