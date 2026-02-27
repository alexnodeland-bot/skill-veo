# 🎬 Veo — Video Generation Skill for OpenClaw

Generate videos with Google's Veo via the Gemini API. Default model is **Veo 3.1 Fast** — great quality with fast turnaround. Switch to `quality` for maximum output.

## Features

- **Text-to-video** — generate from a prompt
- **Image-to-video** — animate from a starting image
- **Element references** — provide assets (objects, characters, scenes) to appear in the video
- **Style references** — provide aesthetic references (lighting, texture, color palette)
- **Model aliases** — `fast`, `quality`, `3.1`, `3.0`, `2.0` for easy switching
- **16:9 / 9:16** aspect ratios, **5–8 second** duration

## Install

```bash
clawhub install veo
```

**Requirements:** [`uv`](https://github.com/astral-sh/uv)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Quick Start

```bash
uv run scripts/generate_video.py \
  --prompt "A golden sunset over the ocean, waves gently crashing" \
  --filename "sunset.mp4" \
  --api-key YOUR_GEMINI_API_KEY
```

## Models

| Alias | Model | Notes |
|-------|-------|-------|
| `fast` *(default)* | `veo-3.1-fast-generate-preview` | Fastest, great quality |
| `quality` | `veo-3.1-generate-preview` | Highest quality, slower |
| `3.0` | `veo-3.0-generate-001` | Veo 3.0 quality |
| `3.0fast` | `veo-3.0-fast-generate-001` | Veo 3.0 fast |
| `2.0` | `veo-2.0-generate-001` | Most compatible |

```bash
# Fast (default)
--model fast

# Highest quality
--model quality

# Or use full model name
--model veo-3.1-generate-preview

# List all available models
--list-models
```

## Examples

### Text-to-video
```bash
uv run scripts/generate_video.py \
  --prompt "A golden sunset over the ocean" \
  --filename "sunset.mp4"
```

### High quality
```bash
uv run scripts/generate_video.py \
  --prompt "A golden sunset over the ocean" \
  --model quality \
  --filename "sunset-hq.mp4"
```

### Image-to-video
```bash
uv run scripts/generate_video.py \
  --prompt "The character slowly turns to face the camera" \
  --input-image character.png \
  --filename "character-turn.mp4"
```

### With element + style references
```bash
uv run scripts/generate_video.py \
  --prompt "The red vase sits on the table" \
  --element red-vase.png \
  --style painterly-style.png \
  --filename "vase.mp4"
```

### Vertical video (social)
```bash
uv run scripts/generate_video.py \
  --prompt "Close up of coffee being poured, slow motion" \
  --aspect-ratio 9:16 \
  --filename "coffee-pour.mp4"
```

## Options

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
| `--input-image` | — | Starting frame (image-to-video) |
| `--element` | — | Asset reference image (repeatable) |
| `--style` | — | Style reference image (repeatable) |
| `--api-key` | — | Gemini API key (or `GEMINI_API_KEY` env) |
| `--list-models` | — | List available Veo models and exit |

## Gemini API Limitations

These features require **Vertex AI** and are not available on the standard Gemini API:
- `--last-frame` — **workaround:** generate two clips and stitch with `ffmpeg`
- `--resolution` — API controls this automatically
- `--fps` / `--generate-audio`

## API Key

Get a Gemini API key at [aistudio.google.com](https://aistudio.google.com). Pass via `--api-key` or set `GEMINI_API_KEY`.

## Notes

- Generation takes **2–5 minutes** (async polling)
- `--count > 1` saves as `name-1.mp4`, `name-2.mp4`, etc.
- Videos download from a temporary URI after generation

## License

MIT
