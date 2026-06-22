#!/usr/bin/env python3
"""Generate TTS audio chunks from the q15 script using Kokoro local TTS."""
import subprocess
import os
import sys
import json
import re

SCRIPT_FILE = "/workspace/projects/q15-tmp-video/monologue-q15.md"
AUDIO_DIR = "/workspace/projects/q15-tmp-video/audio"
TTS_SCRIPT = "/skills/gen-media/scripts/tts-local.sh"
VOICE = "bm_fable"
SPEED = 0.97  # slightly faster for energy

def extract_narration(md_path):
    """Extract spoken narration from markdown, stripping headers and metadata."""
    with open(md_path, 'r') as f:
        text = f.read()
    lines = text.split('\n')
    start = None
    for i, line in enumerate(lines):
        if '## Script' in line:
            start = i + 1
            break
    if start is None:
        start = 0
    narration_lines = lines[start:]
    narration = '\n'.join(l for l in narration_lines if not l.strip().startswith('#') and l.strip() != '---')
    narration = narration.strip()
    narration = re.sub(r'\n{3,}', '\n\n', narration)
    return narration

def chunk_text(text, target=1500):
    """Split text into chunks at paragraph boundaries."""
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    chunks = []
    current = ""
    for para in paragraphs:
        if len(current) + len(para) + 2 > target and current:
            chunks.append(current.strip())
            current = para
        else:
            if current:
                current += '\n\n' + para
            else:
                current = para
    if current.strip():
        chunks.append(current.strip())
    return chunks

def generate_tts(text, output_json_path):
    """Generate TTS using Kokoro local TTS."""
    input_json = json.dumps({
        "text": text,
        "voice": VOICE,
        "speed": SPEED
    })
    cmd = ["bash", TTS_SCRIPT, "--model", "local/kokoro",
           "--input", input_json,
           "--output", output_json_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ERROR generating TTS: {result.stderr}", file=sys.stderr)
        return None
    # Read the output JSON to get the audio URL
    with open(output_json_path, 'r') as f:
        data = json.load(f)
    audio_url = data.get('audio', {}).get('url', '')
    return audio_url

def download_audio(url, output_path):
    """Download the audio file."""
    cmd = ["bash", "/skills/gen-media/scripts/download.sh", url, output_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0

def main():
    os.makedirs(AUDIO_DIR, exist_ok=True)
    
    # Extract narration
    narration = extract_narration(SCRIPT_FILE)
    print(f"Extracted {len(narration)} chars of narration")
    
    # Chunk
    chunks = chunk_text(narration, target=1400)
    print(f"Split into {len(chunks)} chunks")
    for i, chunk in enumerate(chunks):
        print(f"  Chunk {i:02d}: {len(chunk)} chars, first 60: {chunk[:60]}...")
    
    # Generate TTS for each chunk
    chunk_files = []
    for i, chunk in enumerate(chunks):
        json_path = os.path.join(AUDIO_DIR, f"chunk_{i:02d}.json")
        mp3_path = os.path.join(AUDIO_DIR, f"chunk_{i:02d}.mp3")
        print(f"\nGenerating TTS for chunk {i:02d}...")
        audio_url = generate_tts(chunk, json_path)
        if audio_url is None:
            print(f"FAILED on chunk {i:02d}")
            sys.exit(1)
        print(f"  Audio URL: {audio_url}")
        # tts-local.sh already writes the MP3 next to the JSON output
        if os.path.exists(mp3_path) and os.path.getsize(mp3_path) > 1000:
            chunk_files.append(mp3_path)
            print(f"  MP3 ready at {mp3_path} ({os.path.getsize(mp3_path)} bytes)")
        else:
            # Fallback: try downloading
            if download_audio(audio_url, mp3_path):
                chunk_files.append(mp3_path)
                print(f"  Downloaded to {mp3_path}")
            else:
                print(f"  DOWNLOAD FAILED")
                sys.exit(1)
    
    # Concatenate with ffmpeg
    concat_list = os.path.join(AUDIO_DIR, "concat_list.txt")
    with open(concat_list, 'w') as f:
        for mp3 in chunk_files:
            f.write(f"file '{mp3}'\n")
    
    audio_out = os.path.join(AUDIO_DIR, "audio.mp3")
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list,
           "-c:a", "libmp3lame", "-b:a", "128k", audio_out]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"FFMPEG concat failed: {result.stderr}")
        sys.exit(1)
    
    # Get duration
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration",
           "-of", "default=noprint_wrappers=1:nokey=1", audio_out]
    result = subprocess.run(cmd, capture_output=True, text=True)
    duration = float(result.stdout.strip())
    
    print(f"\n=== TTS Generation Complete ===")
    print(f"Audio file: {audio_out}")
    print(f"Duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")
    print(f"Chunks: {len(chunk_files)}")

if __name__ == "__main__":
    main()