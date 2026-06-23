# q15 — The AI Agent That Remembers

A documentary video about [q15](https://github.com/q15co/q15), the open-source AI agent runtime with durable memory and a proxy that solves prompt injection.

## Versions

| Version | File | Duration | Size | Focus |
|---------|------|----------|------|-------|
| v1 | `q15-video.mp4` | 5:09 | 32.6 MB | Original Two Minute Papers style |
| v2 | `q15-video.mp4` (directed) | 5:09 | 32.6 MB | Reworked with directing principles |
| **v3** | **`q15-video-v3.mp4`** | **3:12** | **17.9 MB** | **Character-driven story + proxy/prompt injection** |

**v3 is the current version.** It uses a recurring character (Maya), explains the q15 proxy and how it prevents prompt injection, and was produced using the full three-skill stack: screenwriting, art direction, and video directing.

## What v3 Covers

- The amnesia problem: most AI assistants forget everything between conversations
- q15's memory architecture (working, episodic, semantic, core)
- **Prompt injection**: how malicious instructions in untrusted data can hijack an AI agent
- **The q15 proxy**: how opaque placeholders and egress filtering prevent secret exfiltration even under full prompt injection
- The shift from being a user of a platform to owning your agent

## How v3 Was Made

Produced using three custom skills:

| Skill | Role | Sources |
|-------|------|---------|
| **screenwriting** | Story structure (premise, turning points, adaptation) | McKee, Field, Yorke, Snyder, Gulino, Egri |
| **art-direction** | Visual identity (lookbook, palette, lighting, prompt encoding) | Itten, Alton, Block, Mercado, Preston |
| **video-director** | Pacing, montage, shot design, emotional arc | Mamet, Lumet, Murch, Eisenstein, Kuleshov |

| Component | Tool | Cost |
|-----------|------|------|
| Script | Written using screenwriting skill (controlling idea, 8-sequence structure) | - |
| Lookbook | Art-direction skill (color progression, lighting design, character design) | - |
| Narration TTS | Kokoro-82M (local, `bm_fable` voice, speed 0.93) | $0 |
| Images (15) | fal.ai flux/dev, landscape 16:9, seed 42 for character consistency | ~$0.38 |
| Ken Burns + assembly | ffmpeg zoompan, xfade, two-pass EBU R128 loudnorm | - |
| Compression | libx264 CRF 27, preset slow | - |

### Directing Decisions (v3)

- **Recurring character**: "Maya" — a woman at her desk, consistent across all 15 images (same hair, sweater, desk, style modifier, seed)
- **Story arc**: amnesia (cold) → discovery (warming) → prompt injection attack (red danger) → proxy solution (warming) → ownership (golden)
- **Visual progression**: cold blue-gray → warming amber → red-tinted high contrast → warm golden-hour
- **Kuleshov hard cuts**: beat 7→8 (tension → alarm), beat 10→11 (despair → the turn)
- **Near-still clips** at 4 key moments: realization (beat 3), injection (beat 8), despair (beat 10), resolution (beat 15)
- **Text overlays** at 5 structural beats: "The Amnesia Problem", "Five Memory Systems", "Prompt Injection", "The Proxy", "The agent is yours."
- **Varied Ken Burns**: zoom-in, zoom-out, pan right, pan left, near-still, drift
- **Varied clip durations**: 10s to 18s (matching the emotional arc, not uniform)
- **Three lighting states**: cold screen glow → warm desk lamp → golden-hour window light

### Reproduce v3

```bash
# 1. Generate images (requires FAL_KEY)
nix-shell -p python3 curl jq --run "python3 generate_images_v3.py"

# 2. Generate TTS (requires Kokoro venv)
nix-shell -p python3 ffmpeg --run "python3 generate_tts_v3.py"

# 3. Build the video (requires images in img/ and audio/narration.mp3)
nix-shell -p python3 ffmpeg --run "python3 build_v3.py"
```

See `script-v3.md` for the narration, `lookbook-v3.md` for the visual identity, and `build_v3.py` for the production pipeline.

## Credits

- Subject: [q15](https://github.com/q15co/q15) by Adriaan van der Bergh
- Voice: Kokoro-82M (`bm_fable`)
- Images: fal.ai flux/dev
- Production skills: screenwriting, art-direction, video-director

## License

MIT