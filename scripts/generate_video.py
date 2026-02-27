#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "google-genai>=1.0.0",
#   "pillow",
# ]
# ///
"""
Veo video generation script.
Supports text-to-video, image-to-video, element/style reference images.

Available models (Gemini API):
  veo-3.1-fast-generate-preview  — fastest, good quality (default)
  veo-3.1-generate-preview       — highest quality, slower
  veo-3.0-fast-generate-001      — Veo 3.0 fast
  veo-3.0-generate-001           — Veo 3.0 quality
  veo-2.0-generate-001           — Veo 2.0 (most compatible)

Gemini API limitations vs Vertex AI:
  - --last-frame not supported (Vertex only)
  - --resolution not supported (Vertex only)
  - --fps not supported (Vertex only)
  - --generate-audio not supported (Vertex only)
"""

import argparse
import os
import sys
import time
import urllib.request
from pathlib import Path


# Model aliases for convenience
MODEL_ALIASES = {
    "fast":    "veo-3.1-fast-generate-preview",
    "quality": "veo-3.1-generate-preview",
    "3.1":     "veo-3.1-generate-preview",
    "3.1fast": "veo-3.1-fast-generate-preview",
    "3.0":     "veo-3.0-generate-001",
    "3.0fast": "veo-3.0-fast-generate-001",
    "2.0":     "veo-2.0-generate-001",
    "2":       "veo-2.0-generate-001",
}


def resolve_model(name: str) -> str:
    return MODEL_ALIASES.get(name.lower(), name)


def load_image(path: str):
    """Load an image from path and return as google.genai Image."""
    from google.genai import types

    with open(path, "rb") as f:
        data = f.read()

    ext = Path(path).suffix.lower()
    mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}
    mime_type = mime_map.get(ext, "image/png")

    return types.Image(image_bytes=data, mime_type=mime_type)


def main():
    parser = argparse.ArgumentParser(
        description="Generate video with Veo via Gemini API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Model aliases:
  fast     → veo-3.1-fast-generate-preview  (default)
  quality  → veo-3.1-generate-preview
  3.1      → veo-3.1-generate-preview
  3.0      → veo-3.0-generate-001
  2.0      → veo-2.0-generate-001

Examples:
  generate_video.py --prompt "sunset" --filename out.mp4
  generate_video.py --prompt "sunset" --model quality --filename out.mp4
  generate_video.py --prompt "animate" --input-image photo.png --filename out.mp4
  generate_video.py --prompt "style it" --element obj.png --style ref.png --filename out.mp4
        """
    )

    parser.add_argument("--prompt", required=True, help="Text prompt describing the video")
    parser.add_argument("--filename", required=True, help="Output filename (e.g. output.mp4)")
    parser.add_argument("--model", default="fast",
                        help="Model name or alias: fast (default), quality, 3.1, 3.0, 2.0, or full model name")
    parser.add_argument("--duration", type=int, default=8,
                        help="Duration in seconds (5–8, default: 8)")
    parser.add_argument("--aspect-ratio", default="16:9", choices=["16:9", "9:16"],
                        help="Aspect ratio (default: 16:9)")
    parser.add_argument("--negative-prompt", help="Things to avoid in the video")
    parser.add_argument("--seed", type=int, help="Random seed for reproducibility")
    parser.add_argument("--count", type=int, default=1,
                        help="Number of videos to generate (default: 1)")

    # Input sources
    parser.add_argument("--input-image", metavar="PATH",
                        help="Starting image for image-to-video")
    parser.add_argument("--last-frame", metavar="PATH",
                        help="Target last frame (Vertex AI only — not supported on Gemini API)")

    # Reference images
    parser.add_argument("--element", action="append", metavar="PATH",
                        help="Asset/element reference image (repeatable)")
    parser.add_argument("--style", action="append", metavar="PATH",
                        help="Style reference image (repeatable)")

    parser.add_argument("--api-key", help="Gemini API key (or set GEMINI_API_KEY env var)")
    parser.add_argument("--list-models", action="store_true", help="List available Veo models and exit")

    args = parser.parse_args()

    # Resolve API key
    api_key = args.api_key or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: No API key provided. Use --api-key or set GEMINI_API_KEY.", file=sys.stderr)
        sys.exit(1)

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)

    # List models mode
    if args.list_models:
        print("Available Veo models:")
        for m in client.models.list():
            if "veo" in m.name.lower():
                print(f"  {m.name}")
        print("\nAliases:")
        for alias, model in MODEL_ALIASES.items():
            print(f"  {alias:10s} → {model}")
        return

    model = resolve_model(args.model)

    # Warn about Gemini API limitations
    if args.last_frame:
        print("Warning: --last-frame is not supported on the Gemini API (Vertex AI only). Ignoring.", file=sys.stderr)

    # Input image
    input_image = None
    if args.input_image:
        print(f"Loading input image: {args.input_image}")
        input_image = load_image(args.input_image)

    # Build config — only Gemini-supported params
    config_kwargs = {
        "number_of_videos": args.count,
        "duration_seconds": args.duration,
        "aspect_ratio": args.aspect_ratio,
        "enhance_prompt": True,
    }
    if args.negative_prompt:
        config_kwargs["negative_prompt"] = args.negative_prompt
    if args.seed is not None:
        config_kwargs["seed"] = args.seed

    # Reference images (elements + styles)
    reference_images = []
    for path in (args.element or []):
        print(f"Loading element reference: {path}")
        reference_images.append(types.VideoGenerationReferenceImage(
            image=load_image(path),
            reference_type=types.VideoGenerationReferenceType.ASSET,
        ))
    for path in (args.style or []):
        print(f"Loading style reference: {path}")
        reference_images.append(types.VideoGenerationReferenceImage(
            image=load_image(path),
            reference_type=types.VideoGenerationReferenceType.STYLE,
        ))
    if reference_images:
        config_kwargs["reference_images"] = reference_images

    config = types.GenerateVideosConfig(**config_kwargs)

    # Print summary
    print(f"Submitting video generation...")
    print(f"  Model:    {model}")
    print(f"  Prompt:   {args.prompt}")
    print(f"  Duration: {args.duration}s | Aspect: {args.aspect_ratio}")
    if input_image:
        print(f"  Input image: {args.input_image}")
    if reference_images:
        print(f"  References: {len(args.element or [])} elements, {len(args.style or [])} styles")

    generate_kwargs = {"model": model, "prompt": args.prompt, "config": config}
    if input_image:
        generate_kwargs["image"] = input_image

    operation = client.models.generate_videos(**generate_kwargs)

    # Poll until done
    print("Waiting for generation to complete", end="", flush=True)
    while not operation.done:
        time.sleep(5)
        operation = client.operations.get(operation)
        print(".", end="", flush=True)
    print(" done.")

    if not operation.response or not operation.response.generated_videos:
        print("Error: No videos generated.", file=sys.stderr)
        sys.exit(1)

    # Save outputs
    output_path = Path(args.filename)
    saved = []
    for i, video in enumerate(operation.response.generated_videos):
        if args.count > 1:
            out = output_path.parent / f"{output_path.stem}-{i+1}{output_path.suffix or '.mp4'}"
        else:
            out = output_path if output_path.suffix else output_path.with_suffix(".mp4")

        v = video.video
        if v.video_bytes:
            with open(out, "wb") as f:
                f.write(v.video_bytes)
        elif v.uri:
            print(f"Downloading from URI...")
            url = f"{v.uri}&key={api_key}" if "?" in v.uri else f"{v.uri}?key={api_key}"
            urllib.request.urlretrieve(url, out)
        else:
            print(f"Error: no video data for output {i+1}", file=sys.stderr)
            continue

        saved.append(str(out))
        print(f"Video saved: {out}")

    print(f"\nOutput: {saved[0]}" if len(saved) == 1 else f"\nOutputs: {', '.join(saved)}")


if __name__ == "__main__":
    main()
