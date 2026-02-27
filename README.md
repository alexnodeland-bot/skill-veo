# 🎬 Veo — Video Generation Skill for OpenClaw

Generate videos with Google's [Veo 3](https://deepmind.google/technologies/veo/) via the Gemini API. Supports text-to-video, image-to-video, reference images for elements and style, and last-frame guidance.

## Features

- **Text-to-video** — generate from a prompt
- **Image-to-video** — animate from a starting image
- **Last-frame** — guide the video toward a specific ending frame
- **Element references** — provide assets (objects, characters, scenes) to appear in the video
- **Style references** — provide aesthetic references (color palette, lighting, texture)
- **Veo 2 + Veo 3** — model selection
- **Audio generation** — Veo 3 generates audio by default
- **720p / 1080p**, **16:9 / 9:16**, **5–8 second** duration

## Install

```bash
clawhub install veo
```

Or manually: copy `SKILL.md` and `scripts/generate_video.py` into your OpenClaw skills directory.

**Requirements:** [`uv`](https://github.com/astral-sh/uv) (Python package runner)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Usage

```bash
~/.local/bin/uv run /path/to/skills/veo/scripts/generate_video.py \
  --prompt "your video description" \
  --filename "output.mp4" \
  --api-key YOUR_GEMINI_API_KEY
```

## Examples

### Text-to-video
```bash
uv run scripts/generate_video.py \
  --prompt "A golden sunset over the ocean, waves gently crashing on the shore" \
  --filename "sunset.mp4" \
  --resolution 1080p \
  --duration 8
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
  --prompt "The red vase sits on the table, camera slowly zooms in" \
  --element red-vase.png \
  --style painterly-style.png \
  --last-frame final-closeup.png \
  --filename "vase-zoom.mp4" \
  --resolution 1080p
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
| `--prompt` | required | Text description of the video |
| `--filename` | required | Output path (`.mp4`) |
| `--model` | `veo-3-generate-001` | `veo-2-generate-001` or `veo-3-generate-001` |
| `--duration` | `8` | Duration in seconds (5–8) |
| `--aspect-ratio` | `16:9` | `16:9` or `9:16` |
| `--resolution` | `720p` | `720p` or `1080p` |
| `--negative-prompt` | — | What to avoid |
| `--seed` | — | Reproducibility seed |
| `--no-audio` | off | Disable audio (Veo 3 only) |
| `--count` | `1` | Number of videos to generate |
| `--input-image` | — | Starting frame for image-to-video |
| `--last-frame` | — | Target ending frame |
| `--element` | — | Asset reference image (repeatable) |
| `--style` | — | Style reference image (repeatable) |
| `--api-key` | — | Gemini API key (or set `GEMINI_API_KEY`) |

## API Key

Get a Gemini API key at [aistudio.google.com](https://aistudio.google.com). Pass via `--api-key` or set the `GEMINI_API_KEY` environment variable.

## Notes

- Generation is async — the script polls until complete (typically 2–5 minutes)
- `--count > 1` saves as `name-1.mp4`, `name-2.mp4`, etc.
- Veo 3 generates audio by default; use `--no-audio` to disable
- `--element` and `--style` can each be used multiple times

## License

MIT
