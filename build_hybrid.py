#!/usr/bin/env python3
"""Build the q15 hybrid video — Typst layouts + HyperFrames animations + FAL images + ffmpeg assembly.

This is the hybrid pipeline test:
- 3 HyperFrames animated segments (title card, prompt injection, closing card)
- 2 Typst architecture diagrams (memory systems, proxy architecture)
- 14 FAL AI-generated character images (Maya story beats)
- Kokoro TTS narration
- ffmpeg for Ken Burns, crossfades, assembly, loudnorm, compression
"""
import subprocess
import os
import sys
import json
import re

PROJECT = "/workspace/projects/q15-video-v3"
IMG_DIR = os.path.join(PROJECT, "img")
TYPST_DIR = os.path.join(PROJECT, "typst")
HF_DIR = os.path.join(PROJECT, "hf_segments")
CLIPS_DIR = os.path.join(PROJECT, "clips_hybrid")
AUDIO_FILE = os.path.join(PROJECT, "audio", "narration_v31.mp3")
OUTPUT = os.path.join(PROJECT, "output-hybrid.mp4")

OUT_W = 1920
OUT_H = 1080
FPS = 30

# Shot plan: (type, source, duration, ken_burns, transition, trans_dur, text_overlay)
# type: "image" (FAL/Typst, needs Ken Burns) or "video" (HF pre-rendered MP4, use directly)
# For "video" type, ken_burns is ignored.

SHOTS = [
    # 1. HF title card (8s) — animated opening
    ("video", os.path.join(HF_DIR, "title_card.mp4"), 8,
     None, "xfade", 1.5, None),

    # 2. FAL — frustrated, drift, drawtext "The Amnesia Problem"
    ("image", "beat_01.jpg", 20,
     (1.0, 1.08, 0.48, 0.52, 0.52, 0.48), "xfade", 1.5,
     ("The Amnesia Problem", 4, 4, 64)),

    # 3. FAL — weary, pan right
    ("image", "beat_02.jpg", 16,
     (1.1, 1.1, 0.3, 0.5, 0.7, 0.5), "xfade", 1.5, None),

    # 4. FAL — realizing, near-still
    ("image", "beat_03.jpg", 12,
     (1.0, 1.02, 0.5, 0.5, 0.5, 0.5), "xfade", 1.5, None),

    # 5. FAL — curious, zoom in
    ("image", "beat_04.jpg", 18,
     (1.0, 1.15, 0.5, 0.5, 0.5, 0.5), "xfade", 1.5, None),

    # 6. FAL — engaged, zoom in
    ("image", "beat_05.jpg", 15,
     (1.0, 1.12, 0.5, 0.5, 0.5, 0.5), "xfade", 1.5, None),

    # 7. TYPST — Five Memory Systems architecture diagram (22s, near-still)
    ("image", os.path.join(TYPST_DIR, "memory_systems-1.png"), 22,
     (1.0, 1.04, 0.5, 0.5, 0.5, 0.5), "xfade", 1.5, None),

    # 8. FAL — skills, zoom in, drawtext "Skills = Markdown"
    ("image", "beat_07b.jpg", 16,
     (1.0, 1.15, 0.5, 0.5, 0.5, 0.5), "xfade", 1.5,
     ("Skills = Markdown", 5, 4, 56)),

    # 9. FAL — subagents, pan right
    ("image", "beat_08b.jpg", 15,
     (1.1, 1.1, 0.3, 0.5, 0.7, 0.5), "xfade", 1.5, None),

    # 10. FAL — multi-provider, near-still
    ("image", "beat_09b.jpg", 14,
     (1.0, 1.02, 0.5, 0.5, 0.5, 0.5), "xfade", 1.5, None),

    # 11. FAL — tense, pan left → HARD CUT (Kuleshov)
    ("image", "beat_07.jpg", 13,
     (1.1, 1.1, 0.7, 0.5, 0.3, 0.5), "cut", 0.05, None),

    # 12. HF — Prompt Injection animated segment (6s)
    ("video", os.path.join(HF_DIR, "prompt_injection.mp4"), 6,
     None, "xfade", 1.0, None),

    # 13. FAL — fear, zoom in
    ("image", "beat_09.jpg", 12,
     (1.0, 1.18, 0.5, 0.5, 0.5, 0.5), "xfade", 1.0, None),

    # 14. FAL — despair, near-still → HARD CUT (Kuleshov)
    ("image", "beat_10.jpg", 16,
     (1.0, 1.01, 0.5, 0.5, 0.5, 0.5), "cut", 0.05, None),

    # 15. TYPST — Proxy Architecture diagram (18s, near-still)
    ("image", os.path.join(TYPST_DIR, "proxy_architecture-1.png"), 18,
     (1.0, 1.04, 0.5, 0.5, 0.5, 0.5), "xfade", 1.5, None),

    # 16. FAL — relief, pan right
    ("image", "beat_12.jpg", 14,
     (1.1, 1.1, 0.3, 0.5, 0.7, 0.5), "xfade", 1.5, None),

    # 17. FAL — understanding, zoom in
    ("image", "beat_13.jpg", 16,
     (1.0, 1.12, 0.5, 0.5, 0.5, 0.5), "xfade", 1.5, None),

    # 18. FAL — empowered, zoom out
    ("image", "beat_14.jpg", 20,
     (1.15, 1.0, 0.5, 0.5, 0.5, 0.5), "xfade", 1.5, None),

    # 19. HF — Closing card animated (10s)
    ("video", os.path.join(HF_DIR, "closing_card.mp4"), 10,
     None, "dissolve", 2.0, None),
]


def make_zoompan(z_start, z_end, x_start, y_start, x_end, y_end, total_frames):
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


def get_duration(path):
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration",
           "-of", "default=noprint_wrappers=1:nokey=1", path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())


def generate_image_clip(img_path, effect, duration, clip_path, text_overlay=None,
                        fade_in=False, fade_out=False):
    """Generate a Ken Burns clip from a static image."""
    total_frames = int(duration * FPS)
    z_start, z_end, x_start, y_start, x_end, y_end = effect
    zp = make_zoompan(z_start, z_end, x_start, y_start, x_end, y_end, total_frames)

    filters = [
        f"scale={OUT_W}:{OUT_H}:force_original_aspect_ratio=increase",
        "crop=1920:1080",
        zp,
        "format=yuv420p",
    ]

    if text_overlay:
        text_str, start_s, dur_s, fontsize = text_overlay
        textfile = f"/tmp/overlay_hybrid_{os.path.basename(clip_path)}.txt"
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
    cmd = ["ffmpeg", "-y", "-loop", "1", "-i", img_path, "-vf", vf,
           "-t", str(duration), "-c:v", "libx264", "-pix_fmt", "yuv420p",
           "-preset", "medium", "-crf", "23", "-r", str(FPS), clip_path]
    run(cmd)


def prepare_video_clip(video_path, target_duration, clip_path):
    """Prepare a pre-rendered HF video clip: trim/pad to target duration, ensure format."""
    actual_dur = get_duration(video_path)

    if abs(actual_dur - target_duration) < 0.1:
        # Duration matches — just re-encode to ensure consistent format
        cmd = ["ffmpeg", "-y", "-i", video_path,
               "-c:v", "libx264", "-pix_fmt", "yuv420p",
               "-r", str(FPS), "-preset", "medium", "-crf", "23",
               clip_path]
        run(cmd)
    elif actual_dur > target_duration:
        # Trim to target duration
        cmd = ["ffmpeg", "-y", "-i", video_path,
               "-t", str(target_duration),
               "-c:v", "libx264", "-pix_fmt", "yuv420p",
               "-r", str(FPS), "-preset", "medium", "-crf", "23",
               clip_path]
        run(cmd)
    else:
        # Pad with last frame (freeze) — extend the video
        cmd = ["ffmpeg", "-y", "-i", video_path,
               "-vf", f"tpad=stop_mode=clone:stop_duration={target_duration - actual_dur}",
               "-c:v", "libx264", "-pix_fmt", "yuv420p",
               "-r", str(FPS), "-preset", "medium", "-crf", "23",
               clip_path]
        run(cmd)


def crossfade_clips(clip_paths, shot_data, output_path, final_fade_out=True):
    """Concatenate clips with varied transitions using xfade."""
    n = len(clip_paths)
    inputs = []
    for clip in clip_paths:
        inputs.extend(["-i", clip])

    filter_parts = []
    accumulated = shot_data[0][2]  # duration of first clip

    for i in range(n - 1):
        clip_type, source, dur, effect, trans_type, trans_dur, text = shot_data[i]
        actual_trans = 0.05 if trans_type == "cut" else trans_dur
        offset = accumulated - actual_trans
        in1 = "[0:v]" if i == 0 else f"[v{i}]"
        out_label = f"[v{i+1}]" if i < n - 2 else "[outv]"
        filter_parts.append(
            f"{in1}[{i+1}:v]xfade=transition=fade:duration={actual_trans:.2f}"
            f":offset={offset:.2f}{out_label}")
        next_dur = shot_data[i + 1][2]
        accumulated = accumulated + next_dur - actual_trans

    # Add final fade-out to black if requested
    if final_fade_out:
        filter_parts.append(f"[outv]fade=t=out:st={accumulated-2.0}:d=2.0[outvf]")
        map_label = "[outvf]"
    else:
        map_label = "[outv]"

    filter_complex = ";".join(filter_parts)
    cmd = ["ffmpeg", "-y"] + inputs + [
        "-filter_complex", filter_complex, "-map", map_label,
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-preset", "medium", "-crf", "23", "-r", str(FPS), output_path]
    run(cmd)


def merge_audio(video_path, audio_path, output_path):
    cmd = ["ffmpeg", "-y", "-i", video_path, "-i", audio_path,
           "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
           "-shortest", "-movflags", "+faststart", output_path]
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
    cmd = ["ffmpeg", "-y", "-i", input_path,
           "-c:v", "libx264", "-preset", "slow", "-crf", str(crf),
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
           "-movflags", "+faststart", output_path]
    run(cmd)


def main():
    os.makedirs(CLIPS_DIR, exist_ok=True)
    audio_dur = get_duration(AUDIO_FILE)

    n = len(SHOTS)
    total_dur = sum(s[2] for s in SHOTS)
    total_trans = sum(s[5] if s[4] != "cut" else 0.05 for s in SHOTS[:-1])
    total_after = total_dur - total_trans

    print("=== q15 HYBRID VIDEO BUILD ===")
    print(f"Audio: {audio_dur:.1f}s ({audio_dur/60:.1f} min)")
    print(f"Clips: {n} (mix of HF video, Typst images, FAL images)")
    print(f"Total clip duration: {total_dur:.1f}s")
    print(f"Transition loss: {total_trans:.1f}s")
    print(f"After transitions: {total_after:.1f}s")
    print()

    for i, (ctype, source, dur, effect, trans, trans_dur, text) in enumerate(SHOTS):
        name = os.path.basename(source)
        if ctype == "video":
            label = f"HF VIDEO  {name:30s}"
            motion = "animated"
        elif "typst" in source.lower() or "memory" in name or "proxy" in name:
            label = f"TYPST     {name:30s}"
            motion = "near-still" if abs(effect[1] - effect[0]) < 0.05 else "slight zoom"
        else:
            label = f"FAL IMAGE {name:30s}"
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
        print(f"  {i+1:2d}. {label} {dur:3d}s  {motion:10s}  {trans:8s}  {trans_dur:.1f}s{text_str}")
    print()

    # Generate/prepare clips
    clip_paths = []
    for i, (ctype, source, dur, effect, trans, trans_dur, text) in enumerate(SHOTS):
        clip_path = os.path.join(CLIPS_DIR, f"clip_{i:03d}.mp4")

        if ctype == "video":
            print(f"Clip {i:03d} (HF video: {os.path.basename(source)}, {dur}s)...")
            prepare_video_clip(source, dur, clip_path)
        else:
            # Resolve image path
            if os.path.isabs(source):
                img_path = source
            else:
                img_path = os.path.join(IMG_DIR, source)

            print(f"Clip {i:03d} (image: {os.path.basename(img_path)}, {dur}s)...")
            generate_image_clip(img_path, effect, dur, clip_path,
                                text_overlay=text, fade_in=False, fade_out=False)

        clip_paths.append(clip_path)

    # Assemble with transitions
    print("\nAssembling with varied transitions...")
    video_no_audio = os.path.join(PROJECT, "hybrid_no_audio.mp4")
    crossfade_clips(clip_paths, SHOTS, video_no_audio)

    # Merge audio
    print("Merging audio...")
    merged = os.path.join(PROJECT, "hybrid_merged.mp4")
    merge_audio(video_no_audio, AUDIO_FILE, merged)

    # Two-pass loudnorm
    print("Loudnorm pass 1...")
    m = measure_loudness(merged)
    print(f"  I={m['input_i']}, TP={m['input_tp']}, LRA={m['input_lra']}")

    print("Loudnorm pass 2...")
    normalized = os.path.join(PROJECT, "hybrid_normalized.mp4")
    apply_loudnorm(merged, normalized, m)

    # Compress
    print("Compressing...")
    compress_video(normalized, OUTPUT, crf=27)

    # Stats
    final_dur = get_duration(OUTPUT)
    final_size = os.path.getsize(OUTPUT)
    print(f"\n=== HYBRID VIDEO COMPLETE ===")
    print(f"Output: {OUTPUT}")
    print(f"Duration: {final_dur:.1f}s ({final_dur/60:.1f} min)")
    print(f"Size: {final_size/1024/1024:.1f} MB")
    print(f"Resolution: {OUT_W}x{OUT_H}")

    # Summary
    hf_count = sum(1 for s in SHOTS if s[0] == "video")
    typst_count = sum(1 for s in SHOTS if s[0] == "image" and
                      ("typst" in s[1].lower() or "memory" in os.path.basename(s[1]) or
                       "proxy" in os.path.basename(s[1])))
    fal_count = n - hf_count - typst_count
    print(f"\n=== Pipeline Summary ===")
    print(f"  HyperFrames animated segments: {hf_count}")
    print(f"  Typst architecture diagrams: {typst_count}")
    print(f"  FAL AI-generated images: {fal_count}")
    print(f"  Total clips: {n}")


if __name__ == "__main__":
    main()