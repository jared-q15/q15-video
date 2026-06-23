#!/usr/bin/env python3
"""Stitch HyperFrames demo segments with crossfade transitions."""
import subprocess
import sys

segments = [
    "/workspace/projects/hyperframes-demo/rendered/01.mp4",
    "/workspace/projects/hyperframes-demo/rendered/02.mp4",
    "/workspace/projects/hyperframes-demo/rendered/03.mp4",
    "/workspace/projects/hyperframes-demo/rendered/04.mp4",
    "/workspace/projects/hyperframes-demo/rendered/05.mp4",
    "/workspace/projects/hyperframes-demo/rendered/06.mp4",
    "/workspace/projects/hyperframes-demo/rendered/07.mp4",
]

durations = [6.0, 6.0, 7.0, 6.0, 6.0, 6.0, 6.0]
fade_dur = 0.5
output = "/workspace/projects/hyperframes-demo/hyperframes-demo-reel.mp4"

# Build xfade chain
# Each xfade: offset = cumulative_duration - fade_dur
# After each xfade, cumulative += dur - fade_dur
filter_parts = []
inputs = []
for i, seg in enumerate(segments):
    inputs.extend(["-i", seg])

# First: scale all to 1920x1080, 30fps, yuv420p
prev_label = "0:v"
cumulative = durations[0]

for i in range(1, len(segments)):
    offset = cumulative - fade_dur
    label = f"x{i}"
    transition = "fade" if i % 2 == 1 else "wipeleft"
    filter_parts.append(
        f"[{prev_label}][{i}:v]xfade=transition={transition}:duration={fade_dur}:offset={offset}[{label}]"
    )
    prev_label = label
    cumulative += durations[i] - fade_dur

filter_complex = ";".join(filter_parts)

cmd = [
    "ffmpeg", "-y",
    *inputs,
    "-filter_complex", filter_complex,
    "-map", f"[{prev_label}]",
    "-c:v", "libx264",
    "-crf", "23",
    "-preset", "medium",
    "-pix_fmt", "yuv420p",
    "-r", "30",
    "-movflags", "+faststart",
    output,
]

print(f"Total duration: {cumulative:.1f}s")
print(f"Running ffmpeg with {len(segments)} segments, {len(segments)-1} transitions...")
result = subprocess.run(cmd, capture_output=True, text=True)
if result.returncode != 0:
    print(f"FFmpeg failed: {result.stderr[-2000:]}")
    sys.exit(1)
print(f"Done: {output}")