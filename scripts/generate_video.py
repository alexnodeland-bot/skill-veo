#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "google-genai>=1.0.0",
#   "pillow",
# ]
# ///
"""
Veo video generation via Google Gemini API.

Available models:
  veo-3.1-fast-generate-preview  — fastest (default)
  veo-3.1-generate-preview       — highest quality
  veo-3.0-fast-generate-001
  veo-3.0-generate-001
  veo-2.0-generate-001

Gemini API notes:
  - Duration must be even: 4, 6, or 8 seconds
  - Resolution: 720p or 1080p
  - last_frame, seed, fps, generate_audio not supported (Vertex AI only)
  - enhance_prompt not supported on veo-3.x models
"""

import argparse
import os
import sys
import time
import urllib.request
from pathlib import Path

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

VALID_DURATIONS = {4, 6, 8}


def resolve_model(name: str) -> str:
    return MODEL_ALIASES.get(name.lower(), name)


def nearest_valid_duration(d: int) -> int:
    return min(VALID_DURATIONS, key=lambda x: abs(x - d))


def load_image(path: str):
    from google.genai import types
    with open(path, "rb") as f:
        data = f.read()
    ext = Path(path).suffix.lower()
    mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}
    return types.Image(image_bytes=data, mime_type=mime_map.get(ext, "image/png"))


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

Duration must be even: 4, 6, or 8 seconds. Odd values are rounded automatically.

Examples:
  generate_video.py --prompt "sunset" --filename out.mp4
  generate_video.py --prompt "sunset" --model quality --filename out.mp4 --resolution 1080p
  generate_video.py --prompt "animate" --input-image photo.png --filename out.mp4
  generate_video.py --prompt "stylise" --element obj.png --style ref.png --filename out.mp4
  generate_video.py --list-models
        """
    )

    parser.add_argument("--prompt", required=True, help="Text description of the video")
    parser.add_argument("--filename", required=True, help="Output filename (e.g. output.mp4)")
    parser.add_argument("--model", default="fast",
                        help="Model alias or full name (default: fast = veo-3.1-fast-generate-preview)")
    parser.add_argument("--duration", type=int, default=8,
                        help="Duration in seconds — must be 4, 6, or 8 (default: 8; odd values rounded)")
    parser.add_argument("--aspect-ratio", default="16:9", choices=["16:9", "9:16"],
                        help="Aspect ratio (default: 16:9)")
    parser.add_argument("--resolution", default=None, choices=["720p", "1080p"],
                        help="Resolution: 720p or 1080p (default: API decides)")
    parser.add_argument("--negative-prompt", help="Things to avoid in the video")
    parser.add_argument("--count", type=int, default=1,
                        help="Number of videos to generate (default: 1)")
    parser.add_argument("--person-generation", choices=["allow_adult", "allow_all", "dont_allow"],
                        help="Person generation policy")

    # Input sources
    parser.add_argument("--input-image", metavar="PATH",
                        help="Starting image for image-to-video")

    # Reference images
    parser.add_argument("--element", action="append", metavar="PATH",
                        help="Asset/element reference image (repeatable)")
    parser.add_argument("--style", action="append", metavar="PATH",
                        help="Style reference image (repeatable)")

    parser.add_argument("--api-key", help="Gemini API key (or set GEMINI_API_KEY env var)")
    parser.add_argument("--list-models", action="store_true",
                        help="List available Veo models from the API and exit")

    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("GEMINI_API_KEY")
    if not api_key and not args.list_models:
        print("Error: No API key. Use --api-key or set GEMINI_API_KEY.", file=sys.stderr)
        sys.exit(1)

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)

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

    # Snap duration to valid value
    duration = nearest_valid_duration(args.duration)
    if duration != args.duration:
        print(f"Note: duration {args.duration}s rounded to {duration}s (valid: 4, 6, 8)")

    # Input image
    input_image = None
    if args.input_image:
        print(f"Loading input image: {args.input_image}")
        input_image = load_image(args.input_image)

    # Build config
    config_kwargs = {
        "number_of_videos": args.count,
        "duration_seconds": duration,
        "aspect_ratio": args.aspect_ratio,
    }

    # enhance_prompt not supported on veo-3.x
    if model.startswith("veo-2"):
        config_kwargs["enhance_prompt"] = True

    if args.resolution:
        config_kwargs["resolution"] = args.resolution
    if args.negative_prompt:
        config_kwargs["negative_prompt"] = args.negative_prompt
    if args.person_generation:
        config_kwargs["person_generation"] = args.person_generation

    # Reference images
    reference_images = []
    for path in (args.element or []):
        print(f"Loading element: {path}")
        reference_images.append(types.VideoGenerationReferenceImage(
            image=load_image(path),
            reference_type=types.VideoGenerationReferenceType.ASSET,
        ))
    for path in (args.style or []):
        print(f"Loading style: {path}")
        reference_images.append(types.VideoGenerationReferenceImage(
            image=load_image(path),
            reference_type=types.VideoGenerationReferenceType.STYLE,
        ))
    if reference_images:
        config_kwargs["reference_images"] = reference_images

    config = types.GenerateVideosConfig(**config_kwargs)

    # Summary
    print(f"Generating video...")
    print(f"  Model:    {model}")
    print(f"  Prompt:   {args.prompt}")
    print(f"  Duration: {duration}s | Aspect: {args.aspect_ratio}" +
          (f" | Resolution: {args.resolution}" if args.resolution else ""))
    if input_image:
        print(f"  Input:    {args.input_image}")
    if reference_images:
        print(f"  Refs:     {len(args.element or [])} elements, {len(args.style or [])} styles")

    generate_kwargs = {"model": model, "prompt": args.prompt, "config": config}
    if input_image:
        generate_kwargs["image"] = input_image

    operation = client.models.generate_videos(**generate_kwargs)

    print("Waiting", end="", flush=True)
    while not operation.done:
        time.sleep(5)
        operation = client.operations.get(operation)
        print(".", end="", flush=True)
    print(" done.")

    if not operation.response or not operation.response.generated_videos:
        print("Error: No videos generated.", file=sys.stderr)
        sys.exit(1)

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
            url = f"{v.uri}&key={api_key}" if "?" in v.uri else f"{v.uri}?key={api_key}"
            urllib.request.urlretrieve(url, out)
        else:
            print(f"Error: no video data for output {i+1}", file=sys.stderr)
            continue

        saved.append(str(out))
        print(f"Saved: {out}")

    print(f"\nOutput: {saved[0]}" if len(saved) == 1 else f"\nOutputs: {', '.join(saved)}")


if __name__ == "__main__":
    main()
