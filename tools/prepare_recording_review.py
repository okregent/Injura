"""Write an unapproved source-bound review template; never overwrite reviews."""

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from engine.squat.recording import RecordingReview


def prepare(video, output):
    video, output = Path(video), Path(output)
    signature = video.stat()
    data = {"video": video.name, "size": signature.st_size, "mtime_ns": signature.st_mtime_ns,
            "reviews": [asdict(RecordingReview(side)) for side in ("left", "right")]}
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(prepare(args.video, args.output).resolve())
    except OSError as error:
        parser.error(str(error))
