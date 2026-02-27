---
name: veo
description: "Generate videos with Google Veo via Gemini API. Default model: veo-3.1-fast-generate-preview. Supports aliases: fast, quality, 3.1, 3.0, 2.0. Text-to-video, image-to-video, element/style references. Requires GEMINI_API_KEY."
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

Generate videos using Google Veo via the Gemini API.

## Usage

```bash
~/.local/bin/uv run /path/to/skills/veo/scripts/generate_video.py \
  --prompt "your video description" \
  --filename "output.mp4" \
  --api-key YOUR_GEMINI_API_KEY
```

## Models

| Alias | Full name | Notes |
|-------|-----------|-------|
| `fast` *(default)* | `veo-3.1-fast-generate-preview` | Fastest, great quality |
| `quality` | `veo-3.1-generate-preview` | Highest quality, slower |
| `3.0` | `veo-3.0-generate-001` | Veo 3.0 quality |
| `3.0fast` | `veo-3.0-fast-generate-001` | Veo 3.0 fast |
| `2.0` | `veo-2.0-generate-001` | Most compatible |

Use `--list-models` to see all available models from the API.

## Core Options

| Flag | Default | Description |
|------|---------|-------------|
| `--prompt` | required | Text description |
| `--filename` | required | Output path (`.mp4`) |
| `--model` | `fast` | Model alias or full name |
| `--duration` | `8` | Seconds (5–8) |
| `--aspect-ratio` | `16:9` | `16:9` or `9:16` |
| `--negative-prompt` | — | What to avoid |
| `--seed` | — | Reproducibility seed |
| `--count` | `1` | Number of videos |

## Input Sources

### Image-to-video
```bash
--input-image path/to/image.png
```

### Element references (assets)
```bash
--element path/to/object.png   # repeatable
```

### Style references
```bash
--style path/to/style.png      # repeatable
```

## Gemini API Limitations

These flags are **Vertex AI only** — not supported on the Gemini API:
- `--last-frame` (workaround: generate two clips and stitch with ffmpeg)
- `--resolution` (API uses its own default)
- `--fps`
- `--generate-audio`

## Filename Convention

`yyyy-mm-dd-hh-mm-ss-descriptive-name.mp4`

## Examples

```bash
# Fast generation (default)
generate_video.py --prompt "sunset over ocean" --filename out.mp4 --api-key KEY

# Highest quality
generate_video.py --prompt "sunset over ocean" --model quality --filename out.mp4 --api-key KEY

# Image-to-video
generate_video.py --prompt "slowly zoom in" --input-image photo.png --filename out.mp4 --api-key KEY

# With element + style references
generate_video.py --prompt "the vase sits on the table" --element vase.png --style watercolor.png --filename out.mp4 --api-key KEY

# Vertical (social)
generate_video.py --prompt "coffee pour, slow motion" --aspect-ratio 9:16 --filename out.mp4 --api-key KEY

# List available models
generate_video.py --list-models --api-key KEY
```
