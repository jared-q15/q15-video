# q15 — The AI Agent That Remembers

A documentary video about [q15](https://github.com/q15co/q15), the open-source AI agent runtime with durable memory and a proxy that solves prompt injection.

## Versions

| Version | File | Duration | Size | Focus |
|---------|------|----------|------|-------|
| v1 | `q15-video.mp4` | 5:09 | 32.6 MB | Original Two Minute Papers style |
| v2 | `q15-video.mp4` (directed) | 5:09 | 32.6 MB | Reworked with directing principles |
| **v3** | **`q15-video-v3.mp4`** | **3:12** | **17.9 MB** | **Character-driven story + proxy/prompt injection** |
| **v3.1** | **`q15-video-v3_1.mp4`** | **4:15** | **23.1 MB** | **Blended: story + full q15 explanation + proxy** |

**v3.1 is the current version.** It blends the character-driven story from v3 with the explanatory content from v2. Maya discovers q15, explores its capabilities (memory, skills, subagents, multi-provider), encounters prompt injection, and is saved by the proxy. Produced using the full three-skill stack: screenwriting, art direction, and video directing.

## What v3.1 Covers

- The amnesia problem: most AI assistants forget everything between conversations
- q15's five memory systems (core, working, episodic, semantic) with what each one does
- Skills as composable markdown files — no app store, no lock-in
- Subagent delegation with per-task model routing
- Multi-provider design (local Ollama, cloud APIs, your choice)
- **Prompt injection**: how malicious instructions in untrusted data can hijack an AI agent
- **The q15 proxy**: how opaque placeholders and egress filtering prevent secret exfiltration even under full prompt injection
- Open source as a power-distribution decision: no telemetry, no data harvesting
- Honest limitations: it's infrastructure, not intelligence, and it's early
- The shift from being a user of a platform to owning your agent

## How v3.1 Was Made

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
| Images (18) | fal.ai flux/dev, landscape 16:9, seed 42 for character consistency | ~$0.45 |
| Ken Burns + assembly | ffmpeg zoompan, xfade, two-pass EBU R128 loudnorm | - |
| Compression | libx264 CRF 27, preset slow | - |

### Directing Decisions (v3.1)

- **Recurring character**: "Maya" — a woman at her desk, consistent across all 18 images (same hair, sweater, desk, style modifier, seed)
- **Story arc**: amnesia (cold) → discovery (warming) → memory + skills + subagents + providers (warm) → prompt injection attack (red danger) → proxy solution (warming) → ownership (golden)
- **Visual progression**: cold blue-gray → warming amber → red-tinted high contrast → warm golden-hour
- **Kuleshov hard cuts**: beat 10→11 (tension → alarm), beat 13→14 (despair → the turn)
- **Near-still clips** at 5 key moments: realization (beat 3), provider choice (beat 9), injection (beat 11), despair (beat 13), resolution (beat 18)
- **Text overlays** at 6 structural beats: "The Amnesia Problem", "Five Memory Systems", "Skills = Markdown", "Prompt Injection", "The Proxy", "The agent is yours."
- **Varied Ken Burns**: zoom-in, zoom-out, pan right, pan left, near-still, drift
- **Varied clip durations**: 12s to 20s (matching the emotional arc, not uniform)
- **Three lighting states**: cold screen glow → warm desk lamp → golden-hour window light

### Reproduce v3.1

```bash
# 1. Generate images (requires FAL_KEY)
nix-shell -p python3 curl jq --run "python3 generate_images_v3.py"
nix-shell -p python3 curl jq --run "python3 generate_new_images.py"

# 2. Generate TTS (requires Kokoro venv)
nix-shell -p python3 ffmpeg --run "python3 generate_tts_v31.py"

# 3. Build the video (requires images in img/ and audio/narration_v31.mp3)
nix-shell -p python3 ffmpeg --run "python3 build_v31.py"
```

See `script-v3_1.md` for the narration, `lookbook-v3.md` for the visual identity, and `build_v31.py` for the production pipeline.

## Credits

- Subject: [q15](https://github.com/q15co/q15) by Adriaan van der Bergh
- Voice: Kokoro-82M (`bm_fable`)
- Images: fal.ai flux/dev
- Production skills: screenwriting, art-direction, video-director

## License

MIT