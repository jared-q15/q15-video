# q15 — The AI Agent That Remembers

A ~5 minute documentary video about [q15](https://github.com/q15co/q15), the open-source AI agent runtime with durable memory, produced in the style of [Two Minute Papers](https://www.youtube.com/@TwoMinutePapers).

## Watch

The video is included as `q15-video.mp4` in this repo (32.6 MB, 1920x1080, 5:09).

## What It Covers

- The amnesia problem: most AI assistants forget everything between conversations
- q15's five-layer memory architecture (core, working, semantic, history, zettelkasten)
- Skills as composable markdown files
- Subagent delegation with per-task model routing
- Multi-provider design (local Ollama, cloud providers, your choice)
- The shift from disposable AI chats to an accumulative agent
- Honest limitations: it's infrastructure, not intelligence, and it's early
- Open source as a power-distribution decision

## How It Was Made

| Component | Tool | Cost |
|-----------|------|------|
| Script | Written in Two Minute Papers style (analogy-first, honest about limitations) | - |
| Narration TTS | Kokoro-82M (local, `bm_fable` voice, speed 0.97) | $0 |
| Images (14) | fal.ai flux/schnell, landscape 16:9 | ~$0.02 |
| Directing | Applied video-director skill: beat-by-beat shot plan, varied visual registers, Ken Burns, Kuleshov cuts, text overlays | - |
| Ken Burns + assembly | ffmpeg zoompan, xfade crossfades, two-pass EBU R128 loudnorm | - |
| Compression | libx264 CRF 27, preset slow | - |

### Directing Decisions (v2)

This version was reworked using film directing principles (Mamet, Lumet, Murch, Block, Eisenstein, Kuleshov):

- **Varied clip durations** (12s to 40s) matching the emotional arc instead of uniform 23.6s clips
- **Near-still holds** at the two most important beats (Five Memory Systems: 40s, The Agent Is Yours: 29s) for weight and reflection
- **Kuleshov juxtapositions** via hard cuts at beats 2→3 (blank screens → sticky note = the gap) and 13→14 (limits → conviction = honest → yours)
- **Visual progression**: cool/flat opening → warm/deep middle → cool/still resolution
- **Text overlays** at 5 key moments: "The Amnesia Problem", "Five Memory Systems", "Skills = Markdown", "Disposable → Accumulative", "The agent is yours."
- **Varied Ken Burns**: zoom-in, zoom-out, diagonal pan, horizontal pan, near-still, vertical pan
- **Varied transitions**: 4 hard cuts, 8 crossfades, 3 long dissolves

### Reproduce

```bash
# 1. Generate TTS from script
nix-shell -p python3 ffmpeg --run "python3 generate_tts.py"

# 2. Build the directed video (requires 14 images in img2/ — generate with fal.ai flux/schnell)
nix-shell -p python3 ffmpeg --run "python3 build_directed.py"
```

See `script.md` for the full narration text and `build_directed.py` / `generate_tts.py` for the production pipeline. The original uniform build is preserved as `build_video.py`.

## Credits

- Presentation style inspired by [Two Minute Papers](https://www.youtube.com/@TwoMinutePapers) by Dr. Károly Zsolnai Féhér
- Subject: [q15](https://github.com/q15co/q15) by Adriaan van der Bergh
- Voice: Kokoro-82M (`bm_fable`)
- Images: fal.ai flux/schnell
- Directing: video-director skill (Mamet, Lumet, Murch, Block, Eisenstein, Kuleshov)

## License

MIT