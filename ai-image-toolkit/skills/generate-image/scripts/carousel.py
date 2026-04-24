#!/usr/bin/env python3
"""Generate multi-slide carousels with visual consistency via RunPod Qwen Image endpoints."""

import argparse
import os
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from generate import (
    ASPECT_RATIOS,
    call_runpod,
    call_runpod_async,
    extract_images,
    load_env_file,
    load_image_base64,
    save_image,
)


def parse_spec(spec_path):
    """Parse a carousel markdown spec into structured data."""
    text = Path(spec_path).read_text(encoding="utf-8")
    lines = text.splitlines()

    title = ""
    config = {}
    slides = []
    current_slide = None

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("# ") and not stripped.startswith("## "):
            title = stripped[2:].strip()
            continue

        if stripped.startswith("## "):
            if current_slide:
                slides.append(current_slide)
            current_slide = {"heading": stripped[3:].strip(), "prompt": "", "assets": []}
            continue

        if current_slide is None:
            if ":" in stripped and not stripped.startswith("#"):
                key, _, value = stripped.partition(":")
                config[key.strip()] = value.strip()
            continue

        if stripped.lower().startswith("asset:"):
            asset_path = stripped[6:].strip()
            if asset_path:
                current_slide["assets"].append(asset_path)
            continue

        if stripped and current_slide is not None:
            if current_slide["prompt"]:
                current_slide["prompt"] += " "
            current_slide["prompt"] += stripped

    if current_slide:
        slides.append(current_slide)

    return title, config, slides


def resolve_dimensions(config):
    """Resolve output dimensions from config."""
    if "aspect-ratio" in config:
        ar = config["aspect-ratio"]
        if ar in ASPECT_RATIOS:
            return ASPECT_RATIOS[ar]

    width = int(config.get("width", 0))
    height = int(config.get("height", 0))
    if width and height:
        return (width, height)
    if width:
        return (width, width)
    if height:
        return (height, height)
    return (1328, 1328)


def generate_slide_1(prompt, width, height, steps, seed, negative_prompt, sync_mode):
    """Generate the first slide via the 2512 text-to-image endpoint."""
    endpoint_id = os.environ.get("RUNPOD_2512_ENDPOINT_ID")
    api_key = os.environ.get("RUNPOD_API_KEY")

    if not endpoint_id:
        print("Error: RUNPOD_2512_ENDPOINT_ID not set", file=sys.stderr)
        sys.exit(1)
    if not api_key:
        print("Error: RUNPOD_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    payload = {
        "input": {
            "prompt": prompt,
            "width": width,
            "height": height,
            "steps": steps,
            "seed": seed,
            "negative_prompt": negative_prompt,
            "batch_size": 1,
        }
    }

    print(f"  Generating via 2512 endpoint...")
    if sync_mode:
        return call_runpod(endpoint_id, api_key, payload)
    return call_runpod_async(endpoint_id, api_key, payload)


def edit_slide(prompt, source_path, reference_path, steps, seed, negative_prompt, sync_mode):
    """Edit an image via the 2511 edit endpoint."""
    endpoint_id = os.environ.get("RUNPOD_EDIT_ENDPOINT_ID")
    api_key = os.environ.get("RUNPOD_API_KEY")

    if not endpoint_id:
        print("Error: RUNPOD_EDIT_ENDPOINT_ID not set", file=sys.stderr)
        sys.exit(1)
    if not api_key:
        print("Error: RUNPOD_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    payload = {
        "input": {
            "prompt": prompt,
            "image": load_image_base64(source_path),
            "steps": steps,
            "seed": seed,
            "negative_prompt": negative_prompt,
        }
    }
    if reference_path:
        payload["input"]["reference_image"] = load_image_base64(reference_path)

    print(f"  Editing via 2511 endpoint...")
    if sync_mode:
        return call_runpod(endpoint_id, api_key, payload)
    return call_runpod_async(endpoint_id, api_key, payload)


def save_result(result, filename, output_dir):
    """Extract image from result and save. Returns saved path or None."""
    status = result.get("status")
    if status == "FAILED":
        error = result.get("error", "Unknown error")
        print(f"  FAILED: {error}", file=sys.stderr)
        return None

    images, output = extract_images(result)
    if not images:
        print(f"  No images in response", file=sys.stderr)
        return None

    data = images[0].get("data", "") if isinstance(images[0], dict) else ""
    if not data:
        return None

    return save_image(data, filename, output_dir)


def make_slug(text):
    """Convert text to a filesystem-safe slug."""
    slug = "".join(c if c.isalnum() or c in "-_" else "_" for c in text[:50]).strip("_")
    return slug or "output"


def main():
    load_env_file()
    parser = argparse.ArgumentParser(description="Generate multi-slide carousels with visual consistency")
    parser.add_argument("spec", help="Path to carousel markdown spec file")
    parser.add_argument("--output-dir", default=None, help="Output directory (default: ./<title-slug>)")
    parser.add_argument("--seed", type=int, default=None, help="Base seed (each slide gets base + index)")
    parser.add_argument("--steps", type=int, default=None, help="Override steps from spec")
    parser.add_argument("--negative-prompt", default="", help="Negative prompt for all slides")
    parser.add_argument("--sync", dest="sync_mode", action="store_true", help="Use synchronous mode (faster when worker is warm)")
    args = parser.parse_args()

    title, config, slides = parse_spec(args.spec)
    if not slides:
        print("Error: no slides found in spec", file=sys.stderr)
        sys.exit(1)

    width, height = resolve_dimensions(config)
    steps = args.steps or int(config.get("steps", 4))
    base_seed = args.seed if args.seed is not None else random.randint(0, 2**32 - 1)
    output_dir = args.output_dir or make_slug(title)

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    print(f"Carousel: {title}")
    print(f"  Slides: {len(slides)}, Size: {width}x{height}, Steps: {steps}, Base seed: {base_seed}")
    print()

    saved_paths = []
    slide_1_path = None

    for i, slide in enumerate(slides):
        slide_num = i + 1
        seed = base_seed + i
        heading = slide["heading"]
        prompt = slide["prompt"]
        assets = slide["assets"]
        filename = f"slide_{slide_num:02d}_{make_slug(heading)}.png"

        print(f"Slide {slide_num}: {heading}")
        print(f"  Seed: {seed}, Assets: {len(assets)}")

        if slide_num == 1:
            result = generate_slide_1(
                prompt, width, height, steps, seed,
                args.negative_prompt, args.sync_mode,
            )
            path = save_result(result, filename, output_dir)
        elif not assets:
            result = edit_slide(
                prompt, slide_1_path, slide_1_path, steps, seed,
                args.negative_prompt, args.sync_mode,
            )
            path = save_result(result, filename, output_dir)
        else:
            # Style pass — use slide 1 as reference, prompt describes everything except assets
            style_prompt = prompt
            result = edit_slide(
                style_prompt, slide_1_path, slide_1_path, steps, seed,
                args.negative_prompt, args.sync_mode,
            )
            path = save_result(result, filename, output_dir)

            # Asset passes — composite each asset onto the result
            for j, asset_path in enumerate(assets):
                if not path:
                    break
                asset_seed = seed + 1000 + j
                asset_prompt = f"Add the visual element from the reference image to the appropriate location in this image. Maintain the existing style and composition."
                temp_filename = f"slide_{slide_num:02d}_{make_slug(heading)}_pass{j+2}.png"
                result = edit_slide(
                    asset_prompt, path, asset_path, steps, asset_seed,
                    args.negative_prompt, args.sync_mode,
                )
                new_path = save_result(result, temp_filename, output_dir)
                if new_path:
                    # Remove intermediate pass file, keep final
                    if j < len(assets) - 1:
                        Path(path).unlink(missing_ok=True)
                    elif j == len(assets) - 1:
                        Path(path).unlink(missing_ok=True)
                        # Rename final pass to clean filename
                        final_path = Path(output_dir) / filename
                        Path(new_path).rename(final_path)
                        new_path = str(final_path)
                    path = new_path

        if path:
            print(f"  Saved: {path}")
            saved_paths.append(path)
            if slide_num == 1:
                slide_1_path = path
        else:
            print(f"  FAILED — slide {slide_num} could not be generated", file=sys.stderr)

        print()

    print(f"Done: {len(saved_paths)}/{len(slides)} slides saved to {output_dir}/")
    print(f"Base seed: {base_seed} (reuse for reproducibility)")


if __name__ == "__main__":
    main()
