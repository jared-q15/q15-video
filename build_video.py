#!/usr/bin/env python3
"""Build the q15 Two Minute Papers style documentary video.

14 images, Ken Burns effects, crossfade transitions, synced to 5.2 min TTS narration.
"""
import subprocess
import os
import sys
import json
import re
import glob

# Paths
PROJECT = "/workspace/projects/q15-tmp-video"
IMG_DIR = os.path.join(PROJECT, "img")
CLIPS_DIR = os.path.join(PROJECT, "clips")
AUDIO_FILE = os.path.join(PROJECT, "audio", "audio.mp3")
OUTPUT_FILE = os.path.join(PROJECT, "output.mp4")
OUTPUT_SM = os.path.join(PROJECT, "output-sm.mp4")

# Video params
OUT_W = 1920
OUT_H = 1080
FPS = 30
FADE_DUR = 1.5  # seconds

# Images in order (matching narration flow)
IMAGES = [
    "01-amnesia-office.jpg",
    "02-blank-screens.jpg",
    "03-sticky-note.jpg",
    "04-blueprint.jpg",
    "05-geological-layers.jpg",
    "06-zettelkasten.jpg",
    "07-markdown-stack.jpg",
    "08-building-blocks.jpg",
    "09-parallel-paths.jpg",
    "10-growth-vs-decay.jpg",
    "11-construction.jpg",
    "12-source-code.jpg",
    "13-open-hands.jpg",
    "14-sunrise-servers.jpg",
]

# Ken Burns effects: (z_start, z_end, x_start, y_start, x_end, y_end)
# Alternating zoom in/out, varied pan directions
EFFECTS = [
    (1.0, 1.25, 0.5, 0.5, 0.5, 0.5),    # 01: slow zoom in, center
    (1.2, 1.0, 0.5, 0.5, 0.5, 0.5),    # 02: slow zoom out, center
    (1.0, 1.2, 0.5, 0.4, 0.5, 0.6),    # 03: slow zoom in, vertical pan down
    (1.0, 1.15, 0.3, 0.5, 0.7, 0.5),   # 04: diagonal pan right
    (1.0, 1.25, 0.5, 0.3, 0.5, 0.7),   # 05: zoom in, vertical pan
    (1.15, 1.0, 0.7, 0.5, 0.3, 0.5),   # 06: zoom out, pan left
    (1.0, 1.2, 0.5, 0.5, 0.5, 0.5),    # 07: zoom in, center
    (1.1, 1.0, 0.4, 0.4, 0.6, 0.6),    # 08: zoom out, diagonal pan
    (1.0, 1.2, 0.3, 0.5, 0.7, 0.5),   # 09: zoom in, pan right
    (1.0, 1.15, 0.5, 0.3, 0.5, 0.7),   # 10: zoom in, vertical pan
    (1.15, 1.0, 0.5, 0.5, 0.5, 0.5),   # 11: zoom out, center
    (1.0, 1.25, 0.5, 0.4, 0.5, 0.6),   # 12: zoom in, slight vertical pan
    (1.0, 1.2, 0.4, 0.5, 0.6, 0.5),    # 13: zoom in, pan right
    (1.0, 1.3, 0.5, 0.5, 0.5, 0.5),    # 14: slow zoom in, center (closing)
]

def make_zoompan(z_start, z_end, x_start, y_start, x_end, y_end, total_frames,
                out_w=OUT_W, out_h=OUT_H, fps=FPS):
    """Generate ffmpeg zoompan filter with inlined z expression (avoiding the z bug)."""
    z_expr = f"{z_start}+({z_end}-{z_start})*on/{total_frames}"
    x_expr = f"iw*({x_start}+({x_end}-{x_start})*on/{total_frames})-iw/(2*({z_expr}))"
    y_expr = f"ih*({y_start}+({y_end}-{y_start})*on/{total_frames})-ih/(2*({z_expr}))"
    return (
        f"zoompan=z='{z_expr}':d={total_frames}:"
        f"x='{x_expr}':y='{y_expr}':"
        f"s={out_w}x{out_h}:fps={fps}"
    )

def run(cmd, check=True):
    """Run a command, streaming output."""
    print(f"  Running: {' '.join(cmd[:6])}...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"  FAILED (exit {result.returncode})")
        if result.stderr:
            print(f"  stderr: {result.stderr[-500:]}")
        sys.exit(1)
    return result

def get_audio_duration(path):
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration",
           "-of", "default=noprint_wrappers=1:nokey=1", path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())

def generate_clip(img_path, effect, duration, clip_path):
    """Generate a single Ken Burns clip."""
    total_frames = int(duration * FPS)
    z_start, z_end, x_start, y_start, x_end, y_end = effect
    zp = make_zoompan(z_start, z_end, x_start, y_start, x_end, y_end, total_frames)
    
    vf = f"scale={OUT_W}:{OUT_H}:force_original_aspect_ratio=increase,{zp},format=yuv420p"
    
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", img_path,
        "-vf", vf,
        "-t", str(duration),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-preset", "medium", "-crf", "23",
        "-r", str(FPS),
        clip_path
    ]
    run(cmd)

def crossfade_clips(clip_paths, clip_durations, output_path):
    """Concatenate clips with crossfade transitions."""
    n = len(clip_paths)
    
    # Build filter complex
    inputs = []
    for clip in clip_paths:
        inputs.extend(["-i", clip])
    
    filter_parts = []
    offset = clip_durations[0] - FADE_DUR
    
    for i in range(n - 1):
        in1 = "[0:v]" if i == 0 else f"[v{i}]"
        out_label = f"[v{i+1}]" if i < n - 2 else "[outv]"
        filter_parts.append(
            f"{in1}[{i+1}:v]xfade=transition=fade:duration={FADE_DUR}:offset={offset:.2f}{out_label}"
        )
        if i < n - 2:
            offset += clip_durations[i + 1] - FADE_DUR
    
    filter_complex = ";".join(filter_parts)
    
    cmd = ["ffmpeg", "-y"] + inputs + [
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-preset", "medium", "-crf", "23",
        "-r", str(FPS),
        output_path
    ]
    run(cmd)

def merge_audio(video_path, audio_path, output_path):
    """Merge audio onto video."""
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        "-movflags", "+faststart",
        output_path
    ]
    run(cmd)

def measure_loudness(path):
    """Pass 1: measure integrated loudness."""
    cmd = ["ffmpeg", "-hide_banner", "-i", path,
           "-af", "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json",
           "-f", "null", "-"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    matches = re.findall(r'\{[^{}]+\}', result.stderr)
    if not matches:
        print(f"No loudnorm JSON found for {path}")
        sys.exit(1)
    return json.loads(matches[-1])

def apply_loudnorm(input_path, output_path, m):
    """Pass 2: apply linear gain normalization."""
    af = (f"loudnorm=I=-16:TP=-1.5:LRA=11"
          f":measured_I={m['input_i']}:measured_TP={m['input_tp']}"
          f":measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}"
          f":offset={m['target_offset']}:linear=true")
    cmd = ["ffmpeg", "-y", "-i", input_path, "-af", af,
           "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
           "-ar", "48000", "-movflags", "+faststart", output_path]
    run(cmd)

def compress_video(input_path, output_path, crf=27):
    """Compress for final output."""
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-c:v", "libx264", "-preset", "slow", "-crf", str(crf),
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        output_path
    ]
    run(cmd)

def main():
    os.makedirs(CLIPS_DIR, exist_ok=True)
    
    # Get audio duration
    audio_dur = get_audio_duration(AUDIO_FILE)
    print(f"Audio duration: {audio_dur:.1f}s ({audio_dur/60:.1f} min)")
    
    n = len(IMAGES)
    # Calculate clip durations to fill audio with crossfades
    # total_after_xfade = sum(durations) - FADE_DUR * (n-1) >= audio_dur
    # Use equal durations
    target_total = audio_dur + FADE_DUR * (n - 1) + 2  # +2s buffer
    clip_dur = target_total / n
    clip_durations = [clip_dur] * n
    
    total_after_xfade = sum(clip_durations) - FADE_DUR * (n - 1)
    print(f"Clip duration: {clip_dur:.1f}s each")
    print(f"Total after xfade: {total_after_xfade:.1f}s (audio: {audio_dur:.1f}s)")
    
    # Generate clips
    clip_paths = []
    for i, (img_name, effect) in enumerate(zip(IMAGES, EFFECTS)):
        img_path = os.path.join(IMG_DIR, img_name)
        clip_path = os.path.join(CLIPS_DIR, f"clip_{i:03d}.mp4")
        print(f"\nGenerating clip {i:03d} ({img_name})...")
        generate_clip(img_path, effect, clip_durations[i], clip_path)
        clip_paths.append(clip_path)
    
    # Crossfade
    print(f"\nCrossfading {n} clips...")
    video_no_audio = os.path.join(PROJECT, "video_no_audio.mp4")
    crossfade_clips(clip_paths, clip_durations, video_no_audio)
    
    # Merge audio
    print(f"\nMerging audio...")
    merged = os.path.join(PROJECT, "merged.mp4")
    merge_audio(video_no_audio, AUDIO_FILE, merged)
    
    # Two-pass loudnorm
    print(f"\nPass 1: Measuring loudness...")
    m = measure_loudness(merged)
    print(f"  Measured: I={m['input_i']}, TP={m['input_tp']}, LRA={m['input_lra']}")
    
    print(f"\nPass 2: Applying loudnorm...")
    normalized = os.path.join(PROJECT, "normalized.mp4")
    apply_loudnorm(merged, normalized, m)
    
    # Compress
    print(f"\nCompressing final output...")
    compress_video(normalized, OUTPUT_SM, crf=27)
    
    # Get final stats
    final_dur = get_audio_duration(OUTPUT_SM)
    final_size = os.path.getsize(OUTPUT_SM)
    print(f"\n=== Video Build Complete ===")
    print(f"Output: {OUTPUT_SM}")
    print(f"Duration: {final_dur:.1f}s ({final_dur/60:.1f} min)")
    print(f"Size: {final_size / 1024 / 1024:.1f} MB")
    print(f"Resolution: {OUT_W}x{OUT_H}")

if __name__ == "__main__":
    main()