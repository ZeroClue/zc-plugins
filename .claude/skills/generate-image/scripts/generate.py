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


def call_runpod_async(endpoint_id, api_key, payload, timeout=120):
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

    payload = {
        "input": {
            "prompt": args.prompt,
            "width": args.width,
            "height": args.height,
            "steps": args.steps,
            "negative_prompt": args.negative_prompt,
            "batch_size": args.batch_size,
        }
    }
    if args.seed is not None:
        payload["input"]["seed"] = args.seed

    print(f"Generating image: \"{args.prompt}\"")
    print(f"  Size: {args.width}x{args.height}, Steps: {args.steps}")

    if args.async_mode:
        result = call_runpod_async(endpoint_id, api_key, payload)
    else:
        result = call_runpod(endpoint_id, api_key, payload)

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

    payload = {
        "input": {
            "prompt": args.prompt,
            "image": image_b64,
            "steps": args.steps,
            "negative_prompt": args.negative_prompt,
        }
    }
    if args.seed is not None:
        payload["input"]["seed"] = args.seed

    if args.reference_image:
        payload["input"]["reference_image"] = load_image_base64(args.reference_image)

    print(f"Editing image: \"{args.prompt}\"")
    print(f"  Source: {args.image}, Steps: {args.steps}")
    if args.reference_image:
        print(f"  Reference: {args.reference_image}")

    if args.async_mode:
        result = call_runpod_async(endpoint_id, api_key, payload)
    else:
        result = call_runpod(endpoint_id, api_key, payload)

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
    parser = argparse.ArgumentParser(description="Generate or edit images via RunPod Qwen Image endpoints")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Generate subcommand
    gen = subparsers.add_parser("generate", help="Text-to-image (Qwen 2512)")
    gen.add_argument("prompt", help="Image generation prompt")
    gen.add_argument("--seed", type=int, default=None)
    gen.add_argument("--width", type=int, default=1328)
    gen.add_argument("--height", type=int, default=1328)
    gen.add_argument("--steps", type=int, default=4)
    gen.add_argument("--negative-prompt", default="")
    gen.add_argument("--batch-size", type=int, default=1)
    gen.add_argument("--output-dir", default=".")
    gen.add_argument("--filename", default=None)
    gen.add_argument("--async", dest="async_mode", action="store_true")

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
    edit.add_argument("--async", dest="async_mode", action="store_true")

    args = parser.parse_args()

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
