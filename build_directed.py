#!/usr/bin/env python3
"""Build the q15 documentary video — DIRECTED version using video-director skill principles.

Key improvements over v1:
- Varied clip durations (14s to 40s) matching the emotional arc
- Varied Ken Burns effects (still, slow zoom, fast zoom, pan, drift) per beat
- Varied transitions (hard cuts, crossfades, long dissolves)
- Text overlays at 4 key moments
- 2 Kuleshov juxtapositions (hard cuts between beats 2→3 and 12→13)
- Near-still clips at the two most important beats (8 and 14)
- Visual progression: cool/flat opening → warm/deep middle → cool/still resolution
"""
import subprocess
import os
import sys
import json
import re

# Paths
PROJECT = "/workspace/projects/q15-tmp-video"
IMG_DIR = os.path.join(PROJECT, "img2")
CLIPS_DIR = os.path.join(PROJECT, "clips2")
AUDIO_FILE = os.path.join(PROJECT, "audio", "audio.mp3")
OUTPUT_SM = os.path.join(PROJECT, "output-directed.mp4")

# Video params
OUT_W = 1920
OUT_H = 1080
FPS = 30

# Shot plan: (image, duration, ken_burns_effect, transition_type, transition_dur, text_overlay)
# Ken Burns: (z_start, z_end, x_start, y_start, x_end, y_end)
# transition_type: "cut", "xfade", "dissolve"
# text_overlay: (text, start_sec, duration_sec, fontsize) or None

SHOTS = [
    # 1. Amnesia — unease, cool, ambiguous, slow drift, fade from black
    ("beat-01-amnesia.jpg", 32,
     (1.0, 1.08, 0.48, 0.52, 0.52, 0.48),  # slight drift, unease
     "xfade", 1.0, None),
    
    # 2. Blank screens — frustration, cold, high contrast, STILL (weight)
    ("beat-02-blank.jpg", 15,
     (1.0, 1.01, 0.5, 0.5, 0.5, 0.5),  # near-still
     "cut", 0.01,  # KULESHOV: hard cut to 3
     ("The Amnesia Problem", 4, 4, 64)),
    
    # 3. Sticky note — dismissal, flat, intimate, slow zoom in
    ("beat-03-sticky.jpg", 12,
     (1.0, 1.15, 0.5, 0.5, 0.5, 0.5),  # slow zoom in (looking closer at inadequacy)
     "xfade", 1.5, None),
    
    # 4. Door opening — curiosity→revelation, deep, warming, zoom out
    ("beat-04-question.jpg", 22,
     (1.2, 1.0, 0.5, 0.5, 0.5, 0.5),  # zoom out (revealing context)
     "xfade", 1.5, None),
    
    # 5. Revelation — deep, warm, high contrast, zoom in
    ("beat-05-revelation.jpg", 18,
     (1.0, 1.2, 0.5, 0.5, 0.5, 0.5),  # slow zoom in (approaching truth)
     "xfade", 1.5, None),
    
    # 6. Runtime — limited space, balanced, diagonal pan
    ("beat-06-runtime.jpg", 18,
     (1.0, 1.12, 0.3, 0.5, 0.7, 0.5),  # diagonal pan (structural)
     "xfade", 1.5, None),
    
    # 7. Memory layers — deep, warming, slow zoom in (deepening wonder)
    ("beat-07-memory.jpg", 35,
     (1.0, 1.2, 0.5, 0.3, 0.5, 0.7),  # zoom in + vertical pan
     "xfade", 1.5, None),
    
    # 8. Five systems — KEY MOMENT, awe, NEAR-STILL, long dissolve
    ("beat-08-five-systems.jpg", 40,
     (1.0, 1.02, 0.5, 0.5, 0.5, 0.5),  # NEAR-STILL (weight, importance)
     "dissolve", 3.0,  # long dissolve (reflection)
     ("Five Memory Systems", 8, 5, 72)),
    
    # 9. Skills — flat, warm, horizontal pan
    ("beat-09-skills.jpg", 24,
     (1.0, 1.1, 0.3, 0.5, 0.7, 0.5),  # horizontal pan (scanning)
     "xfade", 1.5,
     ("Skills = Markdown", 5, 3, 56)),
    
    # 10. Delegation — deep, energetic, FAST zoom in, hard cut
    ("beat-10-delegation.jpg", 14,
     (1.0, 1.25, 0.5, 0.5, 0.5, 0.5),  # fast zoom in (urgency)
     "cut", 0.01,  # hard cut (energy shift)
     None),
    
    # 11. Provider — deep, mixed warm/cool, zoom out
    ("beat-11-provider.jpg", 26,
     (1.2, 1.0, 0.5, 0.5, 0.5, 0.5),  # zoom out (seeing the whole)
     "xfade", 1.5, None),
    
    # 12. Result — limited, cooling, slow zoom in, long dissolve
    ("beat-12-result.jpg", 26,
     (1.0, 1.15, 0.5, 0.5, 0.5, 0.5),  # slow zoom in (contemplation)
     "dissolve", 3.0,  # long dissolve (reflection)
     ("Disposable → Accumulative", 6, 4, 56)),
    
    # 13. Limits — limited, cooler, slow pan, hard cut (KULESHOV with 14)
    ("beat-13-limits.jpg", 18,
     (1.0, 1.1, 0.5, 0.3, 0.5, 0.7),  # vertical pan (honest survey)
     "cut", 0.01,  # KULESHOV: hard cut to 14
     None),
    
    # 14. Conviction — deep, still, warm, NEAR-STILL, fade to black
    ("beat-14-conviction.jpg", 29,
     (1.0, 1.02, 0.5, 0.5, 0.5, 0.5),  # NEAR-STILL (weight, finality)
     "dissolve", 3.0,  # long dissolve to end
     ("The agent is yours.", 8, 5, 68)),
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

def generate_clip(img_path, effect, duration, clip_path, text_overlay=None, fade_in=False, fade_out=False):
    """Generate a single clip with Ken Burns effect, optional text overlay and fades."""
    total_frames = int(duration * FPS)
    z_start, z_end, x_start, y_start, x_end, y_end = effect
    zp = make_zoompan(z_start, z_end, x_start, y_start, x_end, y_end, total_frames)
    
    filters = [f"scale={OUT_W}:{OUT_H}:force_original_aspect_ratio=increase", zp, "format=yuv420p"]
    
    # Add text overlay
    if text_overlay:
        text_str, start_s, dur_s, fontsize = text_overlay
        textfile = f"/tmp/overlay_{os.path.basename(clip_path)}.txt"
        with open(textfile, 'w') as f:
            f.write(text_str)
        # Fade in/out the text: enable between start_s and start_s+dur_s
        tf = (f"drawtext=textfile={textfile}:fontsize={fontsize}:fontcolor=white:"
              f"x=(w-text_w)/2:y=(h-text_h)/2:"
              f"box=1:boxcolor=black@0.4:boxborderw=16:"
              f"alpha='if(lt(t,{start_s}),0,if(lt(t,{start_s}+0.5),(t-{start_s})/0.5,"
              f"if(lt(t,{start_s}+{dur_s}-0.5),1,"
              f"max(0,1-(t-({start_s}+{dur_s}-0.5))/0.5)))')")
        filters.append(tf)
    
    # Add fade in from black at start of video
    if fade_in:
        filters.append(f"fade=t=in:st=0:d=2.0")
    
    # Add fade out to black at end of video
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
        clip_path
    ]
    run(cmd)

def crossfade_clips(clip_paths, shot_data, output_path):
    """Concatenate clips with varied transitions using xfade.
    
    The xfade offset for transition i is:
      offset_i = accumulated_duration - transition_duration_i
    where accumulated_duration grows as:
      accumulated = d0
      after transition i: accumulated += d_{i+1} - trans_dur_i
    """
    n = len(clip_paths)
    inputs = []
    for clip in clip_paths:
        inputs.extend(["-i", clip])
    
    filter_parts = []
    accumulated = shot_data[0][1]  # duration of first clip
    
    for i in range(n - 1):
        img, dur, effect, trans_type, trans_dur, text = shot_data[i]
        
        # Actual transition duration
        if trans_type == "cut":
            actual_trans = 0.05  # minimal overlap for "hard cut"
        else:
            actual_trans = trans_dur
        
        offset = accumulated - actual_trans
        
        in1 = "[0:v]" if i == 0 else f"[v{i}]"
        out_label = f"[v{i+1}]" if i < n - 2 else "[outv]"
        
        filter_parts.append(
            f"{in1}[{i+1}:v]xfade=transition=fade:duration={actual_trans:.2f}:offset={offset:.2f}{out_label}"
        )
        
        # Update accumulated duration
        next_dur = shot_data[i + 1][1]
        accumulated = accumulated + next_dur - actual_trans
    
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
    cmd = ["ffmpeg", "-hide_banner", "-i", path,
           "-af", "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json",
           "-f", "null", "-"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    matches = re.findall(r'\{[^{}]+\}', result.stderr)
    if not matches:
        print(f"No loudnorm JSON found")
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
        output_path
    ]
    run(cmd)

def main():
    os.makedirs(CLIPS_DIR, exist_ok=True)
    
    audio_dur = get_audio_duration(AUDIO_FILE)
    
    n = len(SHOTS)
    total_dur = sum(s[1] for s in SHOTS)
    total_trans = sum(s[4] if s[3] != "cut" else 0.05 for s in SHOTS[:-1])
    total_after = total_dur - total_trans
    
    print(f"=== DIRECTED VIDEO BUILD ===")
    print(f"Audio duration: {audio_dur:.1f}s ({audio_dur/60:.1f} min)")
    print(f"Clips: {n}")
    print(f"Total clip duration: {total_dur:.1f}s")
    print(f"Transition loss: {total_trans:.1f}s")
    print(f"Total after transitions: {total_after:.1f}s")
    print()
    
    # Print shot plan
    for i, (img, dur, effect, trans, trans_dur, text) in enumerate(SHOTS):
        z = f"z={effect[0]:.2f}→{effect[1]:.2f}"
        if abs(effect[1] - effect[0]) < 0.05:
            motion = "NEAR-STILL"
        elif effect[1] > effect[0] + 0.05 and effect[2] != effect[5]:
            motion = "pan+zoom"
        elif effect[1] > effect[0] + 0.05:
            motion = "zoom-in"
        elif effect[0] > effect[1] + 0.05:
            motion = "zoom-out"
        else:
            motion = "pan"
        text_str = f' +text "{text[0]}""' if text else ""
        print(f"  {i+1:2d}. {img:30s} {dur:3d}s  {motion:10s}  {trans:8s}  {trans_dur:.1f}s{text_str}")
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
    video_no_audio = os.path.join(PROJECT, "directed_no_audio.mp4")
    crossfade_clips(clip_paths, SHOTS, video_no_audio)
    
    # Merge audio
    print(f"\nMerging audio...")
    merged = os.path.join(PROJECT, "directed_merged.mp4")
    merge_audio(video_no_audio, AUDIO_FILE, merged)
    
    # Two-pass loudnorm
    print(f"\nPass 1: Measuring loudness...")
    m = measure_loudness(merged)
    print(f"  Measured: I={m['input_i']}, TP={m['input_tp']}, LRA={m['input_lra']}")
    
    print(f"\nPass 2: Applying loudnorm...")
    normalized = os.path.join(PROJECT, "directed_normalized.mp4")
    apply_loudnorm(merged, normalized, m)
    
    # Compress
    print(f"\nCompressing final output...")
    compress_video(normalized, OUTPUT_SM, crf=27)
    
    # Stats
    final_dur = get_audio_duration(OUTPUT_SM)
    final_size = os.path.getsize(OUTPUT_SM)
    print(f"\n=== DIRECTED VIDEO COMPLETE ===")
    print(f"Output: {OUTPUT_SM}")
    print(f"Duration: {final_dur:.1f}s ({final_dur/60:.1f} min)")
    print(f"Size: {final_size / 1024 / 1024:.1f} MB")
    print(f"Resolution: {OUT_W}x{OUT_H}")
    
    # Directing summary
    print(f"\n=== Directing Decisions ===")
    print(f"  Kuleshov moments: beats 2→3 (blank→sticky = the gap), 13→14 (construction→ocean = honest→yours)")
    print(f"  Near-still clips: beat 8 (five systems, 40s hold), beat 14 (conviction, 29s hold)")
    print(f"  Text overlays: 'The Amnesia Problem', 'Five Memory Systems', 'Skills = Markdown', 'Disposable → Accumulative', 'The agent is yours.'")
    print(f"  Varied transitions: 4 hard cuts, 8 crossfades, 3 long dissolves")
    print(f"  Duration range: {min(s[1] for s in SHOTS)}s to {max(s[1] for s in SHOTS)}s")

if __name__ == "__main__":
    main()