"""Build the local comparison index: python -m tools.build_review_index."""

import argparse
import csv
import html
import json
from pathlib import Path

from tools.evaluate_counts import reference_range


def summary_cards(root):
    """Summarize saved runs without selecting a model/side or summing sides."""
    references = {}
    reference_path = root / "count-annotations.csv"
    if reference_path.exists():
        with reference_path.open(encoding="utf-8-sig", newline="") as handle:
            references = {row["video"]: reference_range(row) for row in csv.DictReader(handle)}
    cards = []
    for folder in sorted(root.glob("sample_video*")):
        path = folder / "analysis.json"
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        video = data["video"]
        bounds = references.get(video)
        reference = (str(bounds[0]) if bounds[0] == bounds[1] else f"{bounds[0]}–{bounds[1]}") if bounds else "미입력"
        model = {0: "Lite", 1: "Full", 2: "Heavy"}.get(data.get("model_complexity"), "확인 불가")
        parts = [f'<article><h3>{html.escape(video)}</h3>',
                 f'<p>사용자 보고 횟수: <b>{html.escape(reference)}</b> · 프레임 경계 미확정</p>',
                 f'<p>현재 보고서 모델: {model} · 재검출 프레임 {len(data.get("recovered_frame_indices", []))}개</p>']
        for side, details in data["sides"].items():
            side_label = {"left": "왼쪽", "right": "오른쪽"}.get(side, side)
            totals = {"available": 0, "partial": 0, "unavailable": 0}
            for rep in details["repetitions"]:
                for metric in rep["metrics"].values():
                    status = "unavailable" if metric["value"] is None else metric["quality"]["status"]
                    totals[status if status in totals else "unavailable"] += 1
            parts.append(f'<p><b>{html.escape(side_label)}: 검출 반복 {len(details["repetitions"])}개 · '
                         f'검토 후보 {len(details.get("candidates", []))}개</b><br>'
                         f'측정 항목: 자료 충족 {totals["available"]} · 부분 측정 {totals["partial"]} · '
                         f'측정 불가 {totals["unavailable"]}<br>'
                         f'보정: {html.escape(details.get("calibration_method", "확인 불가"))}</p>')
            if not details["repetitions"]:
                parts.append('<p class="note">완전한 반복 구간을 검출하지 못했습니다. 검토 후보를 반복 횟수에 합산하지 않습니다.</p>')
            gates = details.get("recording_gates", {})
            if gates:
                counts = {status: sum(gate["status"] == status for gate in gates.values())
                          for status in ("approved", "unknown", "rejected")}
                parts.append('<p>Recording review (items): ' + html.escape(str(counts))
                             + '. Approval does not validate accuracy.</p>')
            else:
                parts.append('<p>Recording review: unknown (no saved item gates).</p>')
        options = data.get("experimental_options", {})
        if any(options.values()):
            parts.append('<p>실험 옵션 사용: ' + html.escape(', '.join(k for k, enabled in options.items() if enabled)) + '</p>')
        detail = folder / "index.html"
        if detail.exists():
            parts.append(f'<p><a href="{html.escape(folder.name, quote=True)}/index.html">상세 측정값·관절 표시·사유 보기</a></p>')
        # Optional alternatives are explicit saved runs, never automatic winners.
        stem_number = folder.name.removeprefix("sample_video")
        alternatives = []
        for label, relative in [
            ("Heavy + 재검출", f"model-comparison/video{stem_number}-heavy-recovered"),
            ("Heavy + 실험 보정", f"model-comparison/video{stem_number}-heavy-robust"),
        ]:
            alternative = root / relative / "analysis.json"
            if not alternative.exists() or not (root / relative / "index.html").exists():
                continue
            saved = json.loads(alternative.read_text(encoding="utf-8"))
            counts = ' / '.join(f'{side}: {len(value["repetitions"])} (후보 {len(value.get("candidates", []))})'
                                for side, value in saved["sides"].items())
            alternatives.append(f'<li><a href="{relative}/index.html">{html.escape(label)}</a>: {html.escape(counts)}</li>')
        if alternatives:
            parts.append('<details><summary>다른 모델·옵션의 저장 결과 비교</summary><p>좌표·횟수를 혼합하거나 자동 선택하지 않습니다.</p><ul>'
                         + ''.join(alternatives) + '</ul></details>')
        parts.append('</article>')
        cards.append(''.join(parts))
    return cards


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
        '.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,400px),1fr));gap:18px}'
        'article{border:1px solid #ccd;border-radius:10px;padding:18px}summary{cursor:pointer}details{margin:14px 0}.scroll{overflow:auto}'
        '.note{background:#fff2cf;padding:16px;border-left:4px solid #bd8a1e}img{max-width:100%}</style>',
        '<h1>샘플 분석 요약</h1><p>현재 저장된 결과를 영상별로 모았습니다. 좌우는 같은 반복의 별도 분석이며 합산하지 않습니다.</p>',
        '<div class="note">검토 후보는 측정 반복·통계에서 제외됩니다. 측정 항목 수는 반복 수가 아니며, '
        '자료 충족은 관절 정확도나 좋은 자세를 보장하지 않습니다. 사용자 보고 횟수는 독립적으로 확정한 프레임 경계가 아닙니다.</div>',
        '<div class="cards">', *summary_cards(root), '</div>',
        '<details><summary>개발 검증 기록·모델 비교·수동 검토 자료</summary>',
        ('<p><a href="model-comparison/index.html">Video 6: Full vs Heavy model comparison and tracking investigation</a></p>'
         if (root / "model-comparison/index.html").exists() else ''),
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
        '<div class="scroll"><table><tr><th>Video</th><th>Body side</th><th>Previous detections</th><th>Uninterrupted detections</th>'
        '<th>Unverified candidates</th><th>Previous timings</th><th>Current timings</th>'
        '<th>Source re-detections</th><th>Calibration</th></tr>',
        *rows, '</table></div>',
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
    investigation_links = []
    for title, relative in [
        ("3~6번 Full/Heavy 비교", "model-comparison/batch-comparison.html"),
        ("원본 영상의 프레임 연속성", "model-comparison/source-continuity/index.html"),
        ("보정 실험과 경계 변화", "model-comparison/calibration-experiment/index.html"),
        ("1·2번 추가 검증", "additional-validation/model-comparison/calibration-experiment/index.html"),
        ("Heavy 누락 원인", "model-comparison/diagnostics/index.html"),
    ]:
        if (root / relative).is_file():
            investigation_links.append(f'<li><a href="{relative}">{html.escape(title)}</a></li>')
    if investigation_links:
        parts.extend(['<h2>추가 검증 자료</h2><ul>', *investigation_links, '</ul>'])
    if (root / "hip-diagnostics.png").exists():
        parts.append('<h2>Observed hip trajectories</h2><p>Raw valid hip coordinates; red lines show the original '
                     'standing/bottom entry thresholds. Missing observations remain gaps. The revised bottom exit '
                     'uses 75% of the calibrated range, while entry remains at 85%.</p>'
                     '<img src="hip-diagnostics.png" alt="Observed hip trajectories for recordings 3 to 6">')
    if (root / "recordings-overview.jpg").exists():
        parts.append('<h2>Recording overview</h2><img src="recordings-overview.jpg" alt="Recording overview">')
    parts.append('</details></html>')
    (root / "index.html").write_text("\n".join(parts), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("artifacts/sample-review"))
    build_index(parser.parse_args().root)
