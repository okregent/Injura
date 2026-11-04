"""Inspect decoded source continuity independently of pose predictions.

Pixel changes and background optical flow are investigation aids, not a
validated cut/corruption detector. Decoder timestamps do not prove capture continuity.
"""

import csv
import html
import json
from pathlib import Path

import cv2
import numpy as np


def scan(video):
    cap = cv2.VideoCapture(str(video))
    rows, previous, previous_time, count = [], None, None, 0
    fps = cap.get(cv2.CAP_PROP_FPS)
    try:
        while True:
            success, image = cap.read()
            if not success:
                break
            width = 360
            height = round(image.shape[0] * width / image.shape[1])
            gray = cv2.cvtColor(cv2.resize(image, (width, height)), cv2.COLOR_BGR2GRAY)
            timestamp = cap.get(cv2.CAP_PROP_POS_MSEC)
            if previous is not None:
                difference = cv2.absdiff(previous, gray)
                # Predetermined background region excludes the central lifter.
                mask = np.zeros_like(gray)
                mask[:int(height * .18), :] = 255
                mask[:, int(width * .75):] = 255
                corners = cv2.goodFeaturesToTrack(previous, 150, .02, 8, mask=mask)
                motions = np.empty((0, 2))
                if corners is not None:
                    points, status, _ = cv2.calcOpticalFlowPyrLK(previous, gray, corners, None)
                    if points is not None:
                        reverse, back_status, _ = cv2.calcOpticalFlowPyrLK(gray, previous, points, None)
                        if reverse is not None:
                            good = ((status.ravel() == 1) & (back_status.ravel() == 1)
                                    & (np.linalg.norm(reverse - corners, axis=2).ravel() < 1))
                            motions = (points - corners).reshape(-1, 2)[good]
                median = np.median(motions, axis=0) if len(motions) >= 5 else None
                rows.append({"source_frame": count, "decoder_time_ms": timestamp,
                             "decoder_delta_ms": timestamp - previous_time,
                             "gray_mean_abs_change": float(difference.mean()),
                             "background_tracks": len(motions),
                             "background_dx_at_width360": float(median[0]) if median is not None else None,
                             "background_dy_at_width360": float(median[1]) if median is not None else None,
                             "background_shift_at_width360": float(np.linalg.norm(median)) if median is not None else None})
            previous, previous_time = gray, timestamp
            count += 1
    finally:
        cap.release()
    return fps, count, rows


def contact_sheet(video, target, output):
    cap = cv2.VideoCapture(str(video))
    images = []
    try:
        for source in range(target - 2, target + 3):
            cap.set(cv2.CAP_PROP_POS_FRAMES, source)
            success, image = cap.read()
            if not success:
                raise OSError(f"Could not read {video} frame {source}")
            image = cv2.resize(image, (round(image.shape[1] * 360 / image.shape[0]), 360))
            cv2.putText(image, str(source), (8, 22), cv2.FONT_HERSHEY_SIMPLEX, .6, (0, 255, 255), 2)
            images.append(image)
    finally:
        cap.release()
    if not cv2.imwrite(str(output), cv2.hconcat(images)):
        raise OSError(output)


def build(root=Path("artifacts/sample-review/model-comparison/source-continuity")):
    root.mkdir(parents=True, exist_ok=True)
    summary = {}
    for number, targets in [(3, (310, 444)), (5, (230,))]:
        video = Path(f"sample_video{number}.mp4")
        fps, count, rows = scan(video)
        with (root / f"video{number}-transitions.csv").open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        ranked = sorted(rows, key=lambda r: r["gray_mean_abs_change"], reverse=True)
        summary[str(number)] = {"fps": fps, "decoded_frames": count,
                                "top_pixel_change": ranked[:5],
                                "target_transitions": [dict(row, pixel_change_rank=1 + ranked.index(row))
                                                       for row in rows if row["source_frame"] in targets]}
        for target in targets:
            contact_sheet(video, target, root / f"video{number}-around-{target}.jpg")
    (root / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    parts = ['<!doctype html><meta charset="utf-8"><title>Source continuity review</title>',
             '<style>body{font:16px system-ui;margin:28px;line-height:1.6}img{max-width:100%}pre{overflow:auto}</style>',
             '<h1>Source continuity versus pose detection gaps</h1>',
             '<p>Video 3: abrupt lifter-position change at 309 to 310 (~12.92 s), with nearly stationary '
             'background tracks. It has the largest pixel change in this video, but editing/frame omission '
             'versus actual motion is not established. '
             'This is separate from the remaining Heavy pose gap at 444 (18.50 s), whose adjacent '
             'images look continuous. A direct causal link is not established.</p>',
             '<p>Video 5: inspected frames 228-232 around the Heavy gap at 230 (~9.58 s) show '
             'continuous motion. No source defect is established at that gap.</p>',
             '<p>Pixel difference and fixed-background optical flow are descriptive aids, not '
             'validated editing/corruption tests. Normal movement, camera motion and cuts may all '
             'produce changes. Decoder times can remain regular after editing; regular times do not '
             'prove original capture continuity. Production metrics and exclusions are unchanged.</p>',
             '<p><a href="summary.json">Summary</a> | <a href="video3-transitions.csv">Video 3 CSV</a> | '
             '<a href="video5-transitions.csv">Video 5 CSV</a></p>']
    for number, targets in [(3, (310, 444)), (5, (230,))]:
        for target in targets:
            parts.append(f'<h2>Video {number}, around frame {target}</h2>'
                         f'<img src="video{number}-around-{target}.jpg" alt="Five consecutive source frames">')
    parts.append('<pre>' + html.escape(json.dumps(summary, indent=2)) + '</pre>')
    (root / "index.html").write_text('\n'.join(parts), encoding="utf-8")
    print(json.dumps({n: s["target_transitions"] for n, s in summary.items()}, indent=2))


if __name__ == "__main__":
    build()
