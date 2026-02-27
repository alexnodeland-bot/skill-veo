---
name: veo
description: "Generate videos with Google Veo 3 (or Veo 2) via Gemini API. Supports text-to-video, image-to-video, last-frame, element references (ASSET), and style references. Use for any video generation request. Requires GEMINI_API_KEY."
metadata:
  {
    "openclaw":
      {
        "emoji": "🎬",
        "requires": { "bins": ["uv"] },
        "install":
          [
            {
              "id": "uv",
              "kind": "shell",
              "label": "Install uv (Python package runner)",
              "command": "curl -LsSf https://astral.sh/uv/install.sh | sh"
            }
          ]
      }
  }
---

# Veo Video Generation

Generate videos using Google's Veo 3 model via the Gemini API.

## Usage

```bash
~/.local/bin/uv run ~/.openclaw/workspace/skills/veo/scripts/generate_video.py \
  --prompt "your video description" \
  --filename "yyyy-mm-dd-hh-mm-ss-name.mp4" \
  [options]
```

**Important:** Always run from the user's working directory so videos are saved where expected.

## Core Options

| Flag | Default | Description |
|------|---------|-------------|
| `--prompt` | required | Text description of the video |
| `--filename` | required | Output path (timestamped, e.g. `2026-02-27-14-00-00-sunset.mp4`) |
| `--model` | `veo-3-generate-001` | Model to use (`veo-2-generate-001` or `veo-3-generate-001`) |
| `--duration` | `8` | Duration in seconds (5–8) |
| `--aspect-ratio` | `16:9` | `16:9` (landscape) or `9:16` (portrait/vertical) |
| `--resolution` | `720p` | `720p` or `1080p` |
| `--negative-prompt` | — | What to avoid |
| `--seed` | — | Reproducibility seed |
| `--no-audio` | off | Disable audio (Veo 3 generates audio by default) |
| `--count` | `1` | Number of videos to generate |

## Input Sources

### Image-to-Video (starting frame)
```bash
--input-image path/to/image.png
```
Animate from a starting image.

### Last Frame
```bash
--last-frame path/to/end-frame.png
```
Guide the video toward a specific ending frame.
**Note:** `--last-frame` is only supported on Vertex AI, not the Gemini API. If using the Gemini API (default), omit this flag. Workaround: generate two clips and stitch with ffmpeg.

## Reference Images

### Elements (asset references)
Provide real-world objects, characters, or scenes to appear in the video:
```bash
--element path/to/object.png
--element path/to/another-object.png   # multiple allowed
```

### Style references
Provide aesthetic/visual style to apply:
```bash
--style path/to/style-ref.png
```

Elements and style can be combined freely.

## API Key

Checked in order:
1. `--api-key KEY`
2. `GEMINI_API_KEY` env var

## Default Workflow

1. **Draft** — quick test at 720p, 5s, veo-2 if fast iteration needed
2. **Refine** — adjust prompt, add references
3. **Final** — 1080p, veo-3, full duration

## Filename Convention

`yyyy-mm-dd-hh-mm-ss-descriptive-name.mp4`

Examples:
- `2026-02-27-14-00-00-sunset-timelapse.mp4`
- `2026-02-27-15-30-00-robot-walks.mp4`

## Examples

**Basic text-to-video:**
```bash
~/.local/bin/uv run ~/.openclaw/workspace/skills/veo/scripts/generate_video.py \
  --prompt "A golden sunset over the ocean, waves gently crashing" \
  --filename "2026-02-27-14-00-00-sunset.mp4" \
  --api-key YOUR_KEY
```

**Image-to-video with style:**
```bash
~/.local/bin/uv run ~/.openclaw/workspace/skills/veo/scripts/generate_video.py \
  --prompt "The character walks forward slowly" \
  --input-image character.png \
  --style painterly-style.png \
  --filename "2026-02-27-14-00-00-character-walk.mp4" \
  --api-key YOUR_KEY
```

**With element references and last frame:**
```bash
~/.local/bin/uv run ~/.openclaw/workspace/skills/veo/scripts/generate_video.py \
  --prompt "The red vase sits on the table, camera slowly zooms in" \
  --element red-vase.png \
  --last-frame final-close-up.png \
  --duration 8 \
  --resolution 1080p \
  --filename "2026-02-27-14-00-00-vase-zoom.mp4" \
  --api-key YOUR_KEY
```

**Vertical video (social):**
```bash
~/.local/bin/uv run ~/.openclaw/workspace/skills/veo/scripts/generate_video.py \
  --prompt "Close up of coffee being poured, slow motion" \
  --aspect-ratio 9:16 \
  --filename "2026-02-27-14-00-00-coffee-pour.mp4" \
  --api-key YOUR_KEY
```

## Notes
- Veo generation is async — the script polls until complete (typically 2–5 min)
- Veo 3 generates audio by default; use `--no-audio` to disable
- `--count > 1` saves as `name-1.mp4`, `name-2.mp4`, etc.
- Videos are saved as MP4
