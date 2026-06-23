#!/usr/bin/env python3
"""Generate all 15 images for the q15 v3 video using flux-pro/kontext."""

import json
import subprocess
import sys
import os
import time
from pathlib import Path

IMG_DIR = "/workspace/projects/q15-video-v3/img"
GEN_SCRIPT = "/skills/gen-media/scripts/generate.sh"
DL_SCRIPT = "/skills/gen-media/scripts/download.sh"
MODEL = "fal-ai/flux/dev"

CHAR = "a woman in her early thirties with short dark brown hair, wearing a charcoal knit sweater, sitting at a light oak wooden desk with a laptop, slim build, fair skin"
STYLE = "cinematic photography, shot on Arri Alexa, anamorphic lens, shallow depth of field, film grain, naturalistic color grade"

BEATS = [
    # 1: Frustrated - cold
    (f"{CHAR}, frustrated expression, rubbing her temples, the laptop screen casting cold cyan light on her face, dominant cool blue-gray palette, desaturated, cold screen glow lighting, flat low contrast, medium shot centered composition, flat space, {STYLE}"),
    # 2: Weary - cold, repeating
    (f"{CHAR}, weary expression, typing on the laptop, cold fluorescent overhead lighting, dominant cool blue palette, flat desaturated tones, medium-wide shot off-center composition, flat space, {STYLE}"),
    # 3: Realizing - cold, moment of clarity
    (f"{CHAR}, a moment of realization on her face, eyes widening slightly, cold screen glow with a faint warm light beginning to appear, close-up rule of thirds composition, shallow depth of field, {STYLE}"),
    # 4: Curious - warming, discovery
    (f"{CHAR}, curious expression leaning forward toward the screen, a warm desk lamp just turned on casting amber pool of light, warm amber tones entering the cool frame, medium saturation, medium shot centered, limited depth, {STYLE}"),
    # 5: Engaged - warm, agent knows her
    (f"{CHAR}, engaged expression, smiling slightly, warm desk lamp and warm laptop screen glow on her face, dominant warm amber palette, medium contrast, medium close-up rule of thirds, shallow depth of field, {STYLE}"),
    # 6: Awe - warm, memory visualization
    (f"{CHAR}, expression of awe and wonder looking at her laptop screen, the screen showing a glowing abstract visualization of interconnected memory nodes and flowing data streams, warm desk lamp lighting, rich warm amber tones, medium contrast, wide shot with her in lower third, deep space with strong perspective, {STYLE}"),
    # 7: Tense - cooling, tension
    (f"{CHAR}, tense expression, posture stiffening, the lighting hardening and cooling, tension building, cooling color palette with decreasing warmth, rising contrast, medium shot asymmetrical composition, limited depth, {STYLE}"),
    # 8: Alarmed - red, injection on screen
    (f"a laptop screen on a light oak wooden desk, the screen showing ominous abstract red warning elements and threatening data patterns, red-tinted high contrast lighting, hard red key light casting deep shadows, threatening atmosphere, {CHAR} visible out of focus in the background behind the screen, shallow depth of field, {STYLE}"),
    # 9: Fear - dark, alarmed
    (f"{CHAR}, alarmed frightened expression, eyes wide, the laptop screen casting harsh light on her face, dark shadows surrounding her, deep shadows, selective cold light from screen, red accent glow, close-up of her face, shallow depth of field, {STYLE}"),
    # 10: Despair - darkest
    (f"{CHAR}, expression of despair and defeat, head in hands, the darkest moment, low-key lighting, single cold blue light source from the laptop screen, heavy shadows dominating the frame, minimal color, medium shot centered, flat space, {STYLE}"),
    # 11: Turn - proxy, warming begins
    (f"{CHAR} visible in the foreground out of focus, the laptop screen in sharp focus showing an abstract visualization of a luminous gateway intercepting a dark data flow, warm light beginning to return to the scene, amber tones emerging from the darkness, warming color palette, medium contrast, wide shot with deep space, {STYLE}"),
    # 12: Relief - proxy blocks, warm
    (f"{CHAR}, expression of relief, shoulders relaxing, warm amber light clearing the darkness, the laptop screen showing an abstract blocked barrier visualization, warm directional light returning, warm amber palette, medium shot, limited depth, {STYLE}"),
    # 13: Understanding - warm, clarity
    (f"{CHAR}, expression of understanding and calm relief, warm desk lamp light soft and steady, warm color palette with medium saturation, soft warm lighting, medium close-up rule of thirds, shallow depth of field, {STYLE}"),
    # 14: Empowered - golden, working peacefully
    (f"{CHAR}, calm peaceful expression working confidently, golden-hour sunlight streaming through a window behind her casting warm golden light across the desk, dominant golden amber and warm gold palette, rich saturated warm tones, medium-wide shot centered, deep space, {STYLE}"),
    # 15: Resolution - golden, smile
    (f"{CHAR}, looking up from her laptop screen with a small genuine smile, warm golden-hour light flooding through the window behind her, golden saturated warm tones, warm flood lighting, close-up centered composition, shallow depth of field, {STYLE}"),
]


def generate_image(beat_idx, prompt, seed=42):
    """Generate one image and return the URL."""
    input_json = json.dumps({
        "prompt": prompt,
        "image_size": "landscape_16_9",
        "num_images": 1,
        "seed": seed,
        "output_format": "jpeg",
    })
    output_file = f"{IMG_DIR}/beat_{beat_idx:02d}_response.json"

    cmd = [
        "bash", GEN_SCRIPT,
        "--model", MODEL,
        "--input", input_json,
        "--output", output_file,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        print(f"  ERROR generating beat {beat_idx}: {result.stderr[:200]}")
        return None

    # Parse the output JSON to get the image URL
    try:
        with open(output_file, 'r') as f:
            data = json.load(f)
        urls = data.get("images", [])
        if urls and len(urls) > 0:
            return urls[0].get("url")
    except Exception as e:
        print(f"  ERROR parsing beat {beat_idx} response: {e}")
        # Try to find URL in stdout
        for line in result.stdout.split('\n'):
            if '"url"' in line:
                try:
                    idx = line.index('"url"')
                    rest = line[idx+6:]
                    start = rest.index('"') + 1
                    end = rest.index('"', start)
                    return rest[start:end]
                except:
                    pass
    return None


def download_image(url, filepath):
    """Download an image from a URL."""
    cmd = ["bash", DL_SCRIPT, url, filepath]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    return result.returncode == 0


def main():
    os.makedirs(IMG_DIR, exist_ok=True)

    print(f"Generating {len(BEATS)} images with {MODEL}")
    print(f"Estimated cost: ${len(BEATS) * 0.04:.2f}")
    print()

    results = []
    for i, prompt in enumerate(BEATS, 1):
        print(f"[{i}/{len(BEATS)}] Generating beat {i}...")
        url = generate_image(i, prompt, seed=42)
        if url:
            filepath = f"{IMG_DIR}/beat_{i:02d}.jpg"
            print(f"  Downloading to {filepath}...")
            if download_image(url, filepath):
                size = os.path.getsize(filepath)
                print(f"  OK: {size} bytes")
                results.append((i, True, filepath))
            else:
                print(f"  DOWNLOAD FAILED")
                results.append((i, False, url))
        else:
            print(f"  GENERATION FAILED")
            results.append((i, False, None))

        # Small delay between requests
        if i < len(BEATS):
            time.sleep(1)

    print()
    print("=== Summary ===")
    success = sum(1 for _, ok, _ in results if ok)
    print(f"Success: {success}/{len(BEATS)}")
    for i, ok, info in results:
        status = "OK" if ok else "FAIL"
        print(f"  Beat {i:02d}: {status} {info or ''}")

    if success < len(BEATS):
        print(f"\n{len(BEATS) - success} images failed. Re-run for missing beats.")
        sys.exit(1)


if __name__ == "__main__":
    main()