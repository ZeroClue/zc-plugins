#!/usr/bin/env python3
"""Generate multi-slide carousels with visual consistency via RunPod Qwen Image endpoints."""

import argparse
import json
import os
import random
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from generate import (
    ASPECT_RATIOS,
    call_runpod,
    call_runpod_async,
    check_endpoint_health,
    extract_images,
    load_env_file,
    load_image_base64,
    save_image,
    _log_prompt,
)


def parse_spec(spec_path):
    """Parse a carousel markdown spec into structured data.

    Supports extended syntax for typed slides:
      type: checklist
      items:
        - Item one
        - Item two
      accent: "#FF4500"
      icon: X
    """
    text = Path(spec_path).read_text(encoding="utf-8")
    lines = text.splitlines()

    title = ""
    config = {}
    slides = []
    current_slide = None
    in_items = False

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("# ") and not stripped.startswith("## "):
            title = stripped[2:].strip()
            continue

        if stripped.startswith("## "):
            if current_slide:
                slides.append(current_slide)
            current_slide = {"heading": stripped[3:].strip(), "prompt": "", "assets": [],
                             "type": "", "items": [], "columns": [], "steps": [],
                             "number": "", "text": "", "left": "", "right": "",
                             "action_text": "", "url": "", "accent": "", "icon": "",
                             "contrast": ""}
            in_items = False
            continue

        if current_slide is None:
            if ":" in stripped and not stripped.startswith("#"):
                key, _, value = stripped.partition(":")
                config[key.strip()] = value.strip()
            continue

        # Handle items: list block
        if in_items:
            if stripped.startswith("- "):
                item_text = stripped[2:].strip()
                current_slide["items"].append(item_text)
                continue
            elif stripped.startswith("* "):
                item_text = stripped[2:].strip()
                current_slide["items"].append(item_text)
                continue
            else:
                in_items = False

        if stripped.lower().startswith("asset:"):
            asset_path = stripped[6:].strip()
            if asset_path:
                current_slide["assets"].append(asset_path)
            continue

        # Typed slide directives
        if ":" in stripped and not stripped.startswith("#"):
            key, _, value = stripped.partition(":")
            key = key.strip().lower()
            value = value.strip()
            if key == "type":
                current_slide["type"] = value
                continue
            elif key == "items":
                in_items = True
                if value:
                    current_slide["items"].append(value)
                continue
            elif key == "icon":
                current_slide["icon"] = value
                continue
            elif key == "accent":
                current_slide["accent"] = value
                continue
            elif key == "columns":
                current_slide["columns"] = [c.strip() for c in value.split("|")]
                continue
            elif key == "steps":
                current_slide["steps"] = [s.strip() for s in value.replace("→", "->").split("->")]
                continue
            elif key == "number":
                current_slide["number"] = value
                continue
            elif key == "left":
                current_slide["left"] = value
                continue
            elif key == "right":
                current_slide["right"] = value
                continue
            elif key == "text":
                current_slide["text"] = value
                continue
            elif key == "action_text" or key == "action":
                current_slide["action_text"] = value
                continue
            elif key == "contrast":
                current_slide["contrast"] = value
                continue
            elif key == "url":
                current_slide["url"] = value
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
        print(f"  Raw result: {json.dumps(result, indent=2)[:500]}", file=sys.stderr)
        return None

    if status in ("IN_QUEUE", "IN_PROGRESS"):
        job_id = result.get("id", "unknown")
        print(f"  Job {job_id} still {status} — runsync may have timed out", file=sys.stderr)
        print(f"  Raw result: {json.dumps(result, indent=2)[:500]}", file=sys.stderr)
        return None

    images, output = extract_images(result)
    if not images:
        print(f"  No images in response. Raw output: {json.dumps(output, indent=2)[:500]}", file=sys.stderr)
        return None

    data = images[0].get("data", "") if isinstance(images[0], dict) else ""
    if not data:
        print(f"  Image entry has no data. Raw entry: {json.dumps(images[0], indent=2)[:300]}", file=sys.stderr)
        return None

    return save_image(data, filename, output_dir)


def _edit_with_fallback(prompt, source_path, reference_path, steps, seed,
                        negative_prompt, sync_mode, max_retries, no_fallback,
                        width, height, filename, output_dir):
    """Try edit endpoint with retry + backoff, fall back to generate on failure."""
    for attempt in range(max_retries):
        result = edit_slide(
            prompt, source_path, reference_path, steps, seed,
            negative_prompt, sync_mode,
        )
        path = save_result(result, filename, output_dir)
        if path:
            return path
        if attempt < max_retries - 1:
            delay = 5 * (attempt + 1)
            print(f"  Retry {attempt + 1}/{max_retries} in {delay}s...", file=sys.stderr)
            time.sleep(delay)

    if no_fallback:
        print(f"  Edit failed after {max_retries} attempts, fallback disabled", file=sys.stderr)
        return None

    print(f"  Edit failed after {max_retries} attempts — falling back to 2512 generate", file=sys.stderr)
    result = generate_slide_1(
        prompt, width, height, steps, seed,
        negative_prompt, sync_mode,
    )
    path = save_result(result, filename, output_dir)
    if path:
        print(f"  Fallback succeeded (reduced consistency)", file=sys.stderr)
    return path


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
    parser.add_argument("--generate-all", dest="generate_all", action="store_true",
                        help="Use generate (2512) endpoint for all slides instead of edit-based consistency")
    parser.add_argument("--edit-retries", type=int, default=3, help="Retries for edit endpoint before fallback (default: 3)")
    parser.add_argument("--no-fallback", dest="no_fallback", action="store_true",
                        help="Disable automatic fallback to generate on edit failure")
    parser.add_argument("--optimize", action="store_true",
                        help="Expand prompts via LLM for better results")
    parser.add_argument("--optimizer-model", default="haiku", choices=["haiku", "sonnet", "opus"],
                        help="Model for prompt expansion (default: haiku)")
    parser.add_argument("--max-words", type=int, default=500, help="Max words for optimized prompts (default: 500)")
    parser.add_argument("--brand-config", default=None, help="Path to .image-brand.json")
    args = parser.parse_args()

    title, config, slides = parse_spec(args.spec)
    if not slides:
        print("Error: no slides found in spec", file=sys.stderr)
        sys.exit(1)

    width, height = resolve_dimensions(config)
    try:
        steps = args.steps or int(config.get("steps", 4))
    except (ValueError, TypeError):
        steps = args.steps or 4
    base_seed = args.seed if args.seed is not None else random.randint(0, 2**32 - 1)
    output_dir = args.output_dir or make_slug(title)

    # Load brand config, templates, optimizer
    brand = None
    if args.optimize or args.brand_config:
        from brand import BrandConfig
        from optimize import optimize_prompt
        from templates import expand_template
        brand = BrandConfig(args.brand_config)
        if brand.data:
            print(f"  Brand config loaded: {len(brand.data)} properties")
            dims = brand.canvas_dimensions()
            if dims and "width" not in config and "aspect-ratio" not in config:
                width, height = dims
                print(f"  Canvas from brand: {width}x{height}")
    elif any(s.get("type") for s in slides):
        from templates import expand_template

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    print(f"Carousel: {title}")
    print(f"  Slides: {len(slides)}, Size: {width}x{height}, Steps: {steps}, Base seed: {base_seed}")

    api_key = os.environ.get("RUNPOD_API_KEY")
    gen_endpoint = os.environ.get("RUNPOD_2512_ENDPOINT_ID")
    edit_endpoint = os.environ.get("RUNPOD_EDIT_ENDPOINT_ID")
    if gen_endpoint and api_key:
        warm = check_endpoint_health(gen_endpoint, api_key)
        if warm is False:
            print(f"  Note: generate endpoint is cold, expecting cold start delay")
    if edit_endpoint and api_key:
        warm = check_endpoint_health(edit_endpoint, api_key)
        if warm is False:
            print(f"  Note: edit endpoint is cold, expecting cold start delay")
    print()

    saved_paths = []
    slide_1_path = None
    prompts = []

    # Pass 1: expand templates
    for slide in slides:
        p = slide["prompt"]
        if slide.get("type"):
            p = expand_template(slide, brand=brand)
            if not p:
                print(f"  WARNING: empty prompt for typed slide", file=sys.stderr)
        prompts.append(p)

    # Pass 2: batch optimize (single API call for all slides)
    if args.optimize and any(prompts):
        from optimize import batch_optimize
        optimized = batch_optimize(
            prompts, brand=brand, model=args.optimizer_model,
            max_words=args.max_words,
        )
        if len(optimized) == len(prompts):
            prompts = optimized
        else:
            # Batch returned wrong count, fall back to individual
            prompts = [
                optimize_prompt(p, brand=brand, model=args.optimizer_model,
                                max_words=args.max_words) if p else p
                for p in prompts
            ]
        # Log all expanded prompts
        log_path = Path(output_dir) / "_prompts.jsonl"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        for i, (orig, exp) in enumerate(zip(slides, prompts)):
            entry = {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "slide": i + 1,
                "heading": slides[i]["heading"],
                "original_prompt": slides[i].get("prompt", ""),
                "expanded_prompt": exp,
            }
            if slides[i].get("type"):
                entry["template_type"] = slides[i]["type"]
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        print(f"  Prompts logged to {log_path}", file=sys.stderr)

    for i, slide in enumerate(slides):
        slide_num = i + 1
        seed = base_seed + i
        heading = slide["heading"]
        prompt = prompts[i]
        assets = slide["assets"]
        filename = f"slide_{slide_num:02d}_{make_slug(heading)}.png"

        print(f"Slide {slide_num}: {heading}")
        print(f"  Seed: {seed}, Assets: {len(assets)}, Prompt: {len(prompt)} chars")

        if slide_num == 1 or args.generate_all:
            result = generate_slide_1(
                prompt, width, height, steps, seed,
                args.negative_prompt, args.sync_mode,
            )
            path = save_result(result, filename, output_dir)
        elif not assets:
            path = _edit_with_fallback(
                prompt, slide_1_path, slide_1_path, steps, seed,
                args.negative_prompt, args.sync_mode, args.edit_retries,
                args.no_fallback, width, height, filename, output_dir,
            )
        else:
            # Style pass — use slide 1 as reference, prompt describes everything except assets
            style_prompt = prompt
            path = _edit_with_fallback(
                style_prompt, slide_1_path, slide_1_path, steps, seed,
                args.negative_prompt, args.sync_mode, args.edit_retries,
                args.no_fallback, width, height, filename, output_dir,
            )

            # Asset passes — composite each asset onto the result
            for j, asset_path in enumerate(assets):
                if not path:
                    break
                asset_seed = seed + 1000 + j
                asset_prompt = f"Add the visual element from the reference image to the appropriate location in this image. Maintain the existing style and composition."
                temp_filename = f"slide_{slide_num:02d}_{make_slug(heading)}_pass{j+2}.png"
                new_path = _edit_with_fallback(
                    asset_prompt, path, asset_path, steps, asset_seed,
                    args.negative_prompt, args.sync_mode, args.edit_retries,
                    args.no_fallback, width, height, temp_filename, output_dir,
                )
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
