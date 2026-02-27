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
Supports text-to-video, image-to-video, and reference image (elements/frames) inputs.
"""

import argparse
import base64
import os
import sys
import time
from pathlib import Path


def load_image(path: str):
    """Load an image from path and return as google.genai Image."""
    from google import genai
    from google.genai import types

    with open(path, "rb") as f:
        data = f.read()

    ext = Path(path).suffix.lower()
    mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}
    mime_type = mime_map.get(ext, "image/png")

    return types.Image(image_bytes=data, mime_type=mime_type)


def main():
    parser = argparse.ArgumentParser(description="Generate video with Veo via Gemini API")
    parser.add_argument("--prompt", required=True, help="Text prompt for video generation")
    parser.add_argument("--filename", required=True, help="Output filename (e.g. output.mp4)")
    parser.add_argument("--model", default="veo-3-generate-001", help="Veo model (default: veo-3-generate-001)")
    parser.add_argument("--duration", type=int, default=8, help="Duration in seconds (default: 8, range: 5-8)")
    parser.add_argument("--aspect-ratio", default="16:9", choices=["16:9", "9:16"], help="Aspect ratio")
    parser.add_argument("--resolution", default="720p", choices=["720p", "1080p"], help="Resolution")
    parser.add_argument("--fps", type=int, default=24, choices=[24], help="Frames per second")
    parser.add_argument("--negative-prompt", help="What to avoid in the video")
    parser.add_argument("--seed", type=int, help="Random seed for reproducibility")
    parser.add_argument("--no-audio", action="store_true", help="Disable audio generation (Veo 3)")
    parser.add_argument("--count", type=int, default=1, help="Number of videos to generate (default: 1)")

    # Input sources
    parser.add_argument("--input-image", help="Starting image for image-to-video generation")
    parser.add_argument("--last-frame", help="Image to use as the last frame")

    # Reference images (elements)
    parser.add_argument("--element", action="append", metavar="PATH",
                        help="Reference image for asset/element (can use multiple times)")
    parser.add_argument("--style", action="append", metavar="PATH",
                        help="Reference image for style (can use multiple times)")

    parser.add_argument("--api-key", help="Gemini API key (or set GEMINI_API_KEY env var)")
    args = parser.parse_args()

    # Resolve API key
    api_key = args.api_key or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: No API key provided. Use --api-key or set GEMINI_API_KEY.", file=sys.stderr)
        sys.exit(1)

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)

    # Build source
    source_kwargs = {"prompt": args.prompt}
    if args.input_image:
        print(f"Loading input image: {args.input_image}")
        source_kwargs["image"] = load_image(args.input_image)
    source = types.GenerateVideosSource(**source_kwargs)

    # Build config
    config_kwargs = {
        "number_of_videos": args.count,
        "duration_seconds": args.duration,
        "aspect_ratio": args.aspect_ratio,
        "resolution": args.resolution,
        "fps": args.fps,
        "enhance_prompt": True,
        "generate_audio": not args.no_audio,
    }

    if args.negative_prompt:
        config_kwargs["negative_prompt"] = args.negative_prompt
    if args.seed is not None:
        config_kwargs["seed"] = args.seed
    if args.last_frame:
        print(f"Loading last frame: {args.last_frame}")
        config_kwargs["last_frame"] = load_image(args.last_frame)

    # Reference images (elements + styles)
    reference_images = []
    for elem_path in (args.element or []):
        print(f"Loading element reference: {elem_path}")
        reference_images.append(types.VideoGenerationReferenceImage(
            image=load_image(elem_path),
            reference_type=types.VideoGenerationReferenceType.ASSET,
        ))
    for style_path in (args.style or []):
        print(f"Loading style reference: {style_path}")
        reference_images.append(types.VideoGenerationReferenceImage(
            image=load_image(style_path),
            reference_type=types.VideoGenerationReferenceType.STYLE,
        ))
    if reference_images:
        config_kwargs["reference_images"] = reference_images

    config = types.GenerateVideosConfig(**config_kwargs)

    # Submit generation
    print(f"Submitting video generation with {args.model}...")
    print(f"  Prompt: {args.prompt}")
    print(f"  Duration: {args.duration}s | Aspect: {args.aspect_ratio} | Resolution: {args.resolution}")
    if reference_images:
        print(f"  Reference images: {len(reference_images)} (elements: {len(args.element or [])}, styles: {len(args.style or [])})")

    operation = client.models.generate_videos(
        model=args.model,
        prompt=source,
        config=config,
    )

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

    # Save output(s)
    output_path = Path(args.filename)
    saved = []
    for i, video in enumerate(operation.response.generated_videos):
        if args.count > 1:
            stem = output_path.stem
            suffix = output_path.suffix or ".mp4"
            out = output_path.parent / f"{stem}-{i+1}{suffix}"
        else:
            out = output_path if output_path.suffix else output_path.with_suffix(".mp4")

        with open(out, "wb") as f:
            f.write(video.video.video_bytes)
        saved.append(str(out))
        print(f"Video saved: {out}")

    if len(saved) == 1:
        print(f"\nOutput: {saved[0]}")
    else:
        print(f"\nOutputs: {', '.join(saved)}")


if __name__ == "__main__":
    main()
