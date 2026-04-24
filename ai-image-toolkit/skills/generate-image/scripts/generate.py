#!/usr/bin/env python3
"""Generate or edit images via RunPod serverless Qwen Image endpoints."""

import argparse
import base64
import json
import os
import sys
import time
from pathlib import Path

import urllib.request
import urllib.error
import random

ASPECT_RATIOS = {
    "1:1":  (1328, 1328),
    "16:9": (1664, 928),
    "9:16": (928, 1664),
    "4:3":  (1472, 1104),
    "3:4":  (1104, 1472),
    "3:2":  (1584, 1056),
    "2:3":  (1056, 1584),
}


def load_env_file(path=None):
    """Load KEY=VALUE pairs from a .env file into os.environ. Skips comments and blank lines."""
    env_path = Path(path) if path else Path.cwd() / ".env"
    if not env_path.is_file():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("'\"")
        if key and key not in os.environ:
            os.environ[key] = value


def call_runpod(endpoint_id, api_key, payload, timeout=300):
    """Call RunPod runsync endpoint and return the response."""
    url = f"https://api.runpod.ai/v2/{endpoint_id}/runsync"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"HTTP {e.code}: {body}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Connection error: {e.reason}", file=sys.stderr)
        sys.exit(1)


def call_runpod_async(endpoint_id, api_key, payload, timeout=300):
    """Submit async job and poll until completion."""
    url = f"https://api.runpod.ai/v2/{endpoint_id}/run"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"HTTP {e.code}: {body}", file=sys.stderr)
        sys.exit(1)

    job_id = result.get("id")
    if not job_id:
        print(f"No job ID in response: {result}", file=sys.stderr)
        sys.exit(1)

    status = result.get("status")
    print(f"Job submitted: {job_id} (status: {status})")

    status_url = f"https://api.runpod.ai/v2/{endpoint_id}/status/{job_id}"
    while status in ("IN_QUEUE", "IN_PROGRESS"):
        time.sleep(3)
        req = urllib.request.Request(status_url, headers={"Authorization": f"Bearer {api_key}"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        status = result.get("status")
        print(f"  Status: {status}")

    return result


def save_image(image_data, filename, output_dir):
    """Decode base64 image data and save to disk."""
    raw = base64.b64decode(image_data)
    out_path = Path(output_dir) / filename
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(raw)
    return str(out_path)


def make_filename(prompt, seed=None):
    """Generate a filename from the prompt."""
    slug = "".join(c if c.isalnum() or c in "-_" else "_" for c in prompt[:40]).rstrip("_")
    if not slug:
        slug = "image"
    ts = time.strftime("%Y%m%d_%H%M%S")
    return f"{slug}_{ts}.png"


def load_image_base64(path):
    """Read an image file and return base64-encoded string."""
    p = Path(path)
    if not p.exists():
        print(f"Error: image file not found: {path}", file=sys.stderr)
        sys.exit(1)
    if p.stat().st_size > 20 * 1024 * 1024:
        print(f"Error: image file too large ({p.stat().st_size // 1024 // 1024}MB, max 20MB)", file=sys.stderr)
        sys.exit(1)
    return base64.b64encode(p.read_bytes()).decode("utf-8")


def cmd_generate(args):
    """Handle text-to-image generation via 2512 endpoint."""
    endpoint_id = os.environ.get("RUNPOD_2512_ENDPOINT_ID")
    api_key = os.environ.get("RUNPOD_API_KEY")

    if not endpoint_id:
        print("Error: RUNPOD_2512_ENDPOINT_ID environment variable not set", file=sys.stderr)
        sys.exit(1)
    if not api_key:
        print("Error: RUNPOD_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)

    seed = args.seed if args.seed is not None else random.randint(0, 2**32 - 1)

    width = args.width
    height = args.height

    payload = {
        "input": {
            "prompt": args.prompt,
            "width": width,
            "height": height,
            "steps": args.steps,
            "seed": seed,
            "negative_prompt": args.negative_prompt,
            "batch_size": args.batch_size,
        }
    }

    print(f"Generating image: \"{args.prompt}\"")
    print(f"  Size: {width}x{height}, Steps: {args.steps}, Seed: {seed}")

    if args.sync_mode:
        result = call_runpod(endpoint_id, api_key, payload)
    else:
        result = call_runpod_async(endpoint_id, api_key, payload)

    return result


def cmd_edit(args):
    """Handle image editing via edit-2511 endpoint."""
    endpoint_id = os.environ.get("RUNPOD_EDIT_ENDPOINT_ID")
    api_key = os.environ.get("RUNPOD_API_KEY")

    if not endpoint_id:
        print("Error: RUNPOD_EDIT_ENDPOINT_ID environment variable not set", file=sys.stderr)
        sys.exit(1)
    if not api_key:
        print("Error: RUNPOD_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)
    if not args.image:
        print("Error: --image is required for edit mode", file=sys.stderr)
        sys.exit(1)

    image_b64 = load_image_base64(args.image)

    seed = args.seed if args.seed is not None else random.randint(0, 2**32 - 1)

    payload = {
        "input": {
            "prompt": args.prompt,
            "image": image_b64,
            "steps": args.steps,
            "seed": seed,
            "negative_prompt": args.negative_prompt,
        }
    }

    if args.reference_image:
        payload["input"]["reference_image"] = load_image_base64(args.reference_image)

    print(f"Editing image: \"{args.prompt}\"")
    print(f"  Source: {args.image}, Steps: {args.steps}, Seed: {seed}")
    if args.reference_image:
        print(f"  Reference: {args.reference_image}")

    if args.sync_mode:
        result = call_runpod(endpoint_id, api_key, payload)
    else:
        result = call_runpod_async(endpoint_id, api_key, payload)

    return result


def extract_images(result):
    """Extract image list from RunPod response."""
    output = result.get("output", {})
    if isinstance(output, dict) and "error" in output:
        print(f"Handler error: {output['error']}", file=sys.stderr)
        sys.exit(1)

    images = []
    if isinstance(output, dict) and "images" in output:
        images = output["images"]
    elif isinstance(output, list):
        images = output
    return images, output


def main():
    load_env_file()
    parser = argparse.ArgumentParser(description="Generate or edit images via RunPod Qwen Image endpoints")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Generate subcommand
    gen = subparsers.add_parser("generate", help="Text-to-image (Qwen 2512)")
    gen.add_argument("prompt", help="Image generation prompt")
    gen.add_argument("--seed", type=int, default=None)
    gen.add_argument("--width", type=int, default=None)
    gen.add_argument("--height", type=int, default=None)
    gen.add_argument("--aspect-ratio", default=None, choices=list(ASPECT_RATIOS.keys()),
                     help="Preset aspect ratio (overrides --width/--height)")
    gen.add_argument("--steps", type=int, default=4)
    gen.add_argument("--negative-prompt", default="")
    gen.add_argument("--batch-size", type=int, default=1)
    gen.add_argument("--output-dir", default=".")
    gen.add_argument("--filename", default=None)
    gen.add_argument("--sync", dest="sync_mode", action="store_true", help="Use synchronous mode (faster when worker is warm)")

    # Edit subcommand
    edit = subparsers.add_parser("edit", help="Image editing (Qwen Edit 2511)")
    edit.add_argument("prompt", help="Edit instruction")
    edit.add_argument("--image", required=True, help="Source image file path")
    edit.add_argument("--reference-image", default=None, help="Reference image file path")
    edit.add_argument("--seed", type=int, default=None)
    edit.add_argument("--steps", type=int, default=4)
    edit.add_argument("--negative-prompt", default="")
    edit.add_argument("--output-dir", default=".")
    edit.add_argument("--filename", default=None)
    edit.add_argument("--sync", dest="sync_mode", action="store_true", help="Use synchronous mode (faster when worker is warm)")

    args = parser.parse_args()

    if args.command == "generate":
        if args.aspect_ratio:
            args.width, args.height = ASPECT_RATIOS[args.aspect_ratio]
        elif args.width is not None and args.height is None:
            args.height = args.width
        elif args.height is not None and args.width is None:
            args.width = args.height
        elif args.width is None and args.height is None:
            args.width = 1328
            args.height = 1328

    if args.command == "generate":
        result = cmd_generate(args)
    else:
        result = cmd_edit(args)

    status = result.get("status")
    if status == "FAILED":
        error = result.get("error", "Unknown error")
        print(f"Generation failed: {error}", file=sys.stderr)
        sys.exit(1)

    images, output = extract_images(result)
    if not images:
        print(f"No images in response. Raw output: {json.dumps(output, indent=2)[:500]}", file=sys.stderr)
        sys.exit(1)

    saved = []
    for i, img in enumerate(images):
        data = img.get("data", "") if isinstance(img, dict) else ""
        if not data:
            continue

        if args.filename and len(images) == 1:
            filename = args.filename
        else:
            base = args.filename or make_filename(args.prompt, args.seed)
            if len(images) > 1:
                stem = Path(base).stem
                ext = Path(base).suffix or ".png"
                filename = f"{stem}_{i}{ext}"
            else:
                filename = base

        path = save_image(data, filename, args.output_dir)
        saved.append(path)
        print(f"Saved: {path}")

    if saved:
        print(f"\nGenerated {len(saved)} image(s)")


if __name__ == "__main__":
    main()
