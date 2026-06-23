#!/usr/bin/env python3
"""Build the q15 v3 video — using screenwriting, art-direction, and video-director skills.

Character: "Maya" — consistent across all 15 images
Story: amnesia → discovery → prompt injection attack → proxy solution → ownership
Visual progression: cold blue → warming amber → red danger → golden resolution

Key directing decisions:
- Varied clip durations (10s-18s) matching the emotional arc
- Varied Ken Burns effects per beat
- 2 Kuleshov hard cuts: beat 7→8 (tension→alarm), beat 10→11 (despair→turn)
- 3 near-still clips at key moments (beats 3, 8, 10, 15)
- 5 text overlays at structural beats
- Two-pass EBU R128 loudnorm
"""
import subprocess
import os
import sys
import json
import re

# Paths
PROJECT = "/workspace/projects/q15-video-v3"
IMG_DIR = os.path.join(PROJECT, "img")
CLIPS_DIR = os.path.join(PROJECT, "clips")
AUDIO_FILE = os.path.join(PROJECT, "audio", "narration.mp3")
OUTPUT = os.path.join(PROJECT, "output-v3.mp4")

# Video params
OUT_W = 1920
OUT_H = 1080
FPS = 30

# Shot plan: (image, duration, ken_burns_effect, transition_type, transition_dur, text_overlay)
# Ken Burns: (z_start, z_end, x_start, y_start, x_end, y_end) — x,y are 0-1 normalized center
# transition_type: "cut", "xfade", "dissolve"
# text_overlay: (text, start_sec, duration_sec, fontsize) or None

SHOTS = [
    # ACT 1: THE AMNESIA PROBLEM (cold, blue, flat)
    # 1. Frustrated — cold screen glow, slow drift, fade from black
    ("beat_01.jpg", 18,
     (1.0, 1.08, 0.48, 0.52, 0.52, 0.48),  # slight drift
     "xfade", 1.5,
     ("The Amnesia Problem", 4, 4, 64)),

    # 2. Weary — cold, repeating, slow pan right
    ("beat_02.jpg", 15,
     (1.1, 1.1, 0.3, 0.5, 0.7, 0.5),  # pan right
     "xfade", 1.5, None),

    # 3. Realizing — cold, moment of clarity, NEAR-STILL
    ("beat_03.jpg", 12,
     (1.0, 1.02, 0.5, 0.5, 0.5, 0.5),  # near-still
     "xfade", 1.5, None),

    # ACT 1→2: DISCOVERY (warming amber)
    # 4. Curious — desk lamp turns on, slow zoom in
    ("beat_04.jpg", 16,
     (1.0, 1.15, 0.5, 0.5, 0.5, 0.5),  # zoom in
     "xfade", 1.5, None),

    # 5. Engaged — warm, agent knows her, zoom in
    ("beat_05.jpg", 14,
     (1.0, 1.12, 0.5, 0.5, 0.5, 0.5),  # zoom in
     "xfade", 1.5, None),

    # 6. Awe — memory visualization, zoom out (revealing scale)
    ("beat_06.jpg", 18,
     (1.2, 1.0, 0.5, 0.5, 0.5, 0.5),  # zoom out
     "xfade", 1.5,
     ("Five Memory Systems", 6, 5, 64)),

    # ACT 2: THE ATTACK (cooling, red, high contrast)
    # 7. Tense — light hardening, pan left → HARD CUT (Kuleshov)
    ("beat_07.jpg", 12,
     (1.1, 1.1, 0.7, 0.5, 0.3, 0.5),  # pan left
     "cut", 0.05,  # KULESHOV: hard cut to alarm
     None),

    # 8. Alarmed — injection on screen, NEAR-STILL (weight)
    ("beat_08.jpg", 10,
     (1.0, 1.02, 0.5, 0.5, 0.5, 0.5),  # near-still
     "xfade", 1.0,
     ("Prompt Injection", 3, 4, 60)),

    # 9. Fear — agent obeys, zoom in (approaching danger)
    ("beat_09.jpg", 10,
     (1.0, 1.18, 0.5, 0.5, 0.5, 0.5),  # zoom in
     "xfade", 1.0, None),

    # 10. Despair — darkest moment, NEAR-STILL → HARD CUT (Kuleshov)
    ("beat_10.jpg", 13,
     (1.0, 1.01, 0.5, 0.5, 0.5, 0.5),  # near-still
     "cut", 0.05,  # KULESHOV: hard cut to the turn
     None),

    # ACT 2→3: THE PROXY (warming begins)
    # 11. Turn — proxy intercepting, zoom in (approaching solution)
    ("beat_11.jpg", 16,
     (1.0, 1.15, 0.5, 0.5, 0.5, 0.5),  # zoom in
     "xfade", 1.5,
     ("The Proxy", 5, 4, 64)),

    # 12. Relief — proxy blocks, pan right (surveying the safety)
    ("beat_12.jpg", 13,
     (1.1, 1.1, 0.3, 0.5, 0.7, 0.5),  # pan right
     "xfade", 1.5, None),

    # ACT 3: OWNERSHIP (warm, golden)
    # 13. Understanding — warm clarity, zoom in (contemplation)
    ("beat_13.jpg", 15,
     (1.0, 1.12, 0.5, 0.5, 0.5, 0.5),  # zoom in
     "xfade", 1.5, None),

    # 14. Empowered — golden hour, zoom out (seeing the whole world)
    ("beat_14.jpg", 18,
     (1.15, 1.0, 0.5, 0.5, 0.5, 0.5),  # zoom out
     "xfade", 1.5, None),

    # 15. Resolution — smile, NEAR-STILL, fade to black
    ("beat_15.jpg", 13,
     (1.0, 1.02, 0.5, 0.5, 0.5, 0.5),  # near-still
     "dissolve", 2.0,  # long dissolve to end
     ("The agent is yours.", 4, 6, 68)),
]


def make_zoompan(z_start, z_end, x_start, y_start, x_end, y_end, total_frames):
    """Generate ffmpeg zoompan filter with inlined z expression."""
    z_expr = f"{z_start}+({z_end}-{z_start})*on/{total_frames}"
    x_expr = f"iw*({x_start}+({x_end}-{x_start})*on/{total_frames})-iw/(2*({z_expr}))"
    y_expr = f"ih*({y_start}+({y_end}-{y_start})*on/{total_frames})-ih/(2*({z_expr}))"
    return f"zoompan=z='{z_expr}':d={total_frames}:x='{x_expr}':y='{y_expr}':s={OUT_W}x{OUT_H}:fps={FPS}"


def run(cmd, check=True):
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


def generate_clip(img_path, effect, duration, clip_path, text_overlay=None,
                  fade_in=False, fade_out=False):
    """Generate a single clip with Ken Burns effect, optional text overlay and fades."""
    total_frames = int(duration * FPS)
    z_start, z_end, x_start, y_start, x_end, y_end = effect
    zp = make_zoompan(z_start, z_end, x_start, y_start, x_end, y_end, total_frames)

    filters = [
        f"scale={OUT_W}:{OUT_H}:force_original_aspect_ratio=increase",
        "crop=1920:1080",  # ensure exact dimensions
        zp,
        "format=yuv420p",
    ]

    # Add text overlay
    if text_overlay:
        text_str, start_s, dur_s, fontsize = text_overlay
        textfile = f"/tmp/overlay_{os.path.basename(clip_path)}.txt"
        with open(textfile, 'w') as f:
            f.write(text_str)
        tf = (f"drawtext=textfile={textfile}:fontsize={fontsize}:fontcolor=white:"
              f"x=(w-text_w)/2:y=(h-text_h)/2:"
              f"box=1:boxcolor=black@0.5:boxborderw=20:"
              f"alpha='if(lt(t,{start_s}),0,if(lt(t,{start_s}+0.5),(t-{start_s})/0.5,"
              f"if(lt(t,{start_s}+{dur_s}-0.5),1,"
              f"max(0,1-(t-({start_s}+{dur_s}-0.5))/0.5)))')")
        filters.append(tf)

    if fade_in:
        filters.append("fade=t=in:st=0:d=2.0")

    if fade_out:
        filters.append(f"fade=t=out:st={duration-2.0}:d=2.0")

    vf = ",".join(filters)

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", img_path,
        "-vf", vf,
        "-t", str(duration),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-preset", "medium", "-crf", "23",
        "-r", str(FPS),
        clip_path,
    ]
    run(cmd)


def crossfade_clips(clip_paths, shot_data, output_path):
    """Concatenate clips with varied transitions using xfade."""
    n = len(clip_paths)
    inputs = []
    for clip in clip_paths:
        inputs.extend(["-i", clip])

    filter_parts = []
    accumulated = shot_data[0][1]  # duration of first clip

    for i in range(n - 1):
        img, dur, effect, trans_type, trans_dur, text = shot_data[i]

        if trans_type == "cut":
            actual_trans = 0.05
        else:
            actual_trans = trans_dur

        offset = accumulated - actual_trans

        in1 = "[0:v]" if i == 0 else f"[v{i}]"
        out_label = f"[v{i+1}]" if i < n - 2 else "[outv]"

        filter_parts.append(
            f"{in1}[{i+1}:v]xfade=transition=fade:duration={actual_trans:.2f}"
            f":offset={offset:.2f}{out_label}"
        )

        next_dur = shot_data[i + 1][1]
        accumulated = accumulated + next_dur - actual_trans

    filter_complex = ";".join(filter_parts)

    cmd = ["ffmpeg", "-y"] + inputs + [
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-preset", "medium", "-crf", "23",
        "-r", str(FPS),
        output_path,
    ]
    run(cmd)


def merge_audio(video_path, audio_path, output_path):
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        "-movflags", "+faststart",
        output_path,
    ]
    run(cmd)


def measure_loudness(path):
    cmd = ["ffmpeg", "-hide_banner", "-i", path,
           "-af", "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json",
           "-f", "null", "-"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    matches = re.findall(r'\{[^{}]+\}', result.stderr)
    if not matches:
        print("No loudnorm JSON found")
        sys.exit(1)
    return json.loads(matches[-1])


def apply_loudnorm(input_path, output_path, m):
    af = (f"loudnorm=I=-16:TP=-1.5:LRA=11"
          f":measured_I={m['input_i']}:measured_TP={m['input_tp']}"
          f":measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}"
          f":offset={m['target_offset']}:linear=true")
    cmd = ["ffmpeg", "-y", "-i", input_path, "-af", af,
           "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
           "-ar", "48000", "-movflags", "+faststart", output_path]
    run(cmd)


def compress_video(input_path, output_path, crf=27):
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-c:v", "libx264", "-preset", "slow", "-crf", str(crf),
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        output_path,
    ]
    run(cmd)


def main():
    os.makedirs(CLIPS_DIR, exist_ok=True)

    audio_dur = get_audio_duration(AUDIO_FILE)

    n = len(SHOTS)
    total_dur = sum(s[1] for s in SHOTS)
    total_trans = sum(s[4] if s[3] != "cut" else 0.05 for s in SHOTS[:-1])
    total_after = total_dur - total_trans

    print("=== q15 VIDEO v3 BUILD ===")
    print(f"Audio duration: {audio_dur:.1f}s ({audio_dur/60:.1f} min)")
    print(f"Clips: {n}")
    print(f"Total clip duration: {total_dur:.1f}s")
    print(f"Transition loss: {total_trans:.1f}s")
    print(f"Total after transitions: {total_after:.1f}s")
    print()

    # Print shot plan
    for i, (img, dur, effect, trans, trans_dur, text) in enumerate(SHOTS):
        z = f"z={effect[0]:.2f}->{effect[1]:.2f}"
        if abs(effect[1] - effect[0]) < 0.05 and abs(effect[2] - effect[4]) < 0.05:
            motion = "NEAR-STILL"
        elif abs(effect[1] - effect[0]) < 0.05:
            motion = "pan"
        elif effect[1] > effect[0] + 0.05:
            motion = "zoom-in"
        elif effect[0] > effect[1] + 0.05:
            motion = "zoom-out"
        else:
            motion = "drift"
        text_str = f' +text "{text[0]}"' if text else ""
        print(f"  {i+1:2d}. {img:18s} {dur:3d}s  {motion:10s}  {trans:8s}  {trans_dur:.1f}s{text_str}")
    print()

    # Generate clips
    clip_paths = []
    for i, (img_name, dur, effect, trans, trans_dur, text) in enumerate(SHOTS):
        img_path = os.path.join(IMG_DIR, img_name)
        clip_path = os.path.join(CLIPS_DIR, f"clip_{i:03d}.mp4")
        fade_in = (i == 0)
        fade_out = (i == n - 1)
        print(f"Generating clip {i:03d} ({img_name}, {dur}s)...")
        generate_clip(img_path, effect, dur, clip_path, text_overlay=text,
                      fade_in=fade_in, fade_out=fade_out)
        clip_paths.append(clip_path)

    # Crossfade with varied transitions
    print(f"\nAssembling with varied transitions...")
    video_no_audio = os.path.join(PROJECT, "v3_no_audio.mp4")
    crossfade_clips(clip_paths, SHOTS, video_no_audio)

    # Merge audio
    print(f"\nMerging audio...")
    merged = os.path.join(PROJECT, "v3_merged.mp4")
    merge_audio(video_no_audio, AUDIO_FILE, merged)

    # Two-pass loudnorm
    print(f"\nPass 1: Measuring loudness...")
    m = measure_loudness(merged)
    print(f"  Measured: I={m['input_i']}, TP={m['input_tp']}, LRA={m['input_lra']}")

    print(f"\nPass 2: Applying loudnorm...")
    normalized = os.path.join(PROJECT, "v3_normalized.mp4")
    apply_loudnorm(merged, normalized, m)

    # Compress
    print(f"\nCompressing final output...")
    compress_video(normalized, OUTPUT, crf=27)

    # Stats
    final_dur = get_audio_duration(OUTPUT)
    final_size = os.path.getsize(OUTPUT)
    print(f"\n=== q15 VIDEO v3 COMPLETE ===")
    print(f"Output: {OUTPUT}")
    print(f"Duration: {final_dur:.1f}s ({final_dur/60:.1f} min)")
    print(f"Size: {final_size / 1024 / 1024:.1f} MB")
    print(f"Resolution: {OUT_W}x{OUT_H}")

    # Directing summary
    print(f"\n=== Directing Decisions ===")
    print(f"  Character: Maya (consistent across all 15 images)")
    print(f"  Story: amnesia -> discovery -> prompt injection -> proxy -> ownership")
    print(f"  Kuleshov cuts: beat 7->8 (tension->alarm), beat 10->11 (despair->turn)")
    print(f"  Near-still clips: beats 3, 8, 10, 15 (weight at key moments)")
    print(f"  Text overlays: 'The Amnesia Problem', 'Five Memory Systems', "
          f"'Prompt Injection', 'The Proxy', 'The agent is yours.'")
    print(f"  Visual progression: cold blue -> warming amber -> red danger -> golden resolution")
    print(f"  Duration range: {min(s[1] for s in SHOTS)}s to {max(s[1] for s in SHOTS)}s")


if __name__ == "__main__":
    main()