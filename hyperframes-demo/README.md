# HyperFrames Demo Reel

A showcase of animation techniques rendered with [HyperFrames](https://github.com/heygen-com/hyperframes) (HTML → video via headless Chromium + FFmpeg).

## Video

**File:** `hyperframes-demo-reel.mp4` (1.5 MB, 40s, 1920x1080, 30fps, H.264)

## Segments

| # | Segment | Technique | Duration |
|---|---------|-----------|----------|
| 01 | Kinetic Title | Letter-by-letter text reveal with gradient background | 6s |
| 02 | Text Morph | Word-to-word kinetic typography transitions | 6s |
| 03 | Code Typing | Simulated IDE code typing with syntax highlighting | 7s |
| 04 | Data Bars | Animated bar chart with staggered growth | 6s |
| 05 | 3D Cards | GSAP-powered 3D card transforms with perspective | 6s |
| 06 | Particle Network | Dynamic particle system with pulsing rings | 6s |
| 07 | Closing Card | Gradient text, feature badges, repo link | 6s |

Transitions: alternating `fade` and `wipeleft` xfades (0.5s each).

## How It Works

Each segment is a standalone HTML file using:
- Plain HTML + CSS (no React, no build step)
- [GSAP](https://gsap.com/) timeline animations (paused, seeked frame-by-frame by HyperFrames)
- `data-composition-id`, `data-start`, `data-duration`, `data-track-index` attributes for HyperFrames timeline control

### Render a single segment

```bash
cd segments/01-kinetic-title
nix-shell -p nodejs_22 ffmpeg chromium --run \
  "npx --yes hyperframes@0.7.3 render --output segment.mp4"
```

### Stitch all segments

```bash
nix-shell -p python311 ffmpeg --run "python3 stitch.py"
```

## Tech Stack

- **HyperFrames** v0.7.3 (Apache 2.0) — HTML-to-video rendering
- **GSAP** 3.14.2 — animation timeline engine
- **Chromium** 145 — headless frame capture
- **FFmpeg** — H.264 encoding + xfade transitions
- **Nix** — reproducible environment