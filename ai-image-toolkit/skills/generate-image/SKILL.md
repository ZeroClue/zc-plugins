---
name: generate-image
description: This skill should be used when the user asks to "generate an image", "create a picture", "draw", "render", "illustrate", "make AI art", "edit an image", "modify this photo", "change the background", "remove the background", "style transfer", "produce a visual", or wants to create or edit images from text descriptions. Supports text-to-image (Qwen Image 2512) and image editing (Qwen Image Edit 2511) via RunPod serverless endpoints.
---

# Generate Image

Generate or edit images using Qwen Image models via RunPod serverless endpoints.

**Two modes:**
- **generate** (default) — text-to-image via Qwen Image 2512 (4-step Lightning, ~2s/image, up to 4096x4096)
- **edit** — image editing via Qwen Image Edit 2511 (edit an existing image with text instructions, 4-step Lightning or 40-step full)

## Prerequisites

This plugin requires a [RunPod](https://runpod.io?ref=lnnwdl3q) account with two serverless endpoints deployed. Three environment variables must be set:
- `RUNPOD_2512_ENDPOINT_ID` — RunPod serverless endpoint ID for text-to-image
- `RUNPOD_EDIT_ENDPOINT_ID` — RunPod serverless endpoint ID for image editing
- `RUNPOD_API_KEY` — RunPod API key (shared across both endpoints)

If any are missing, tell the user they need to configure RunPod and direct them to the setup guide: **`references/setup.md`** — covers creating a RunPod account, deploying the required endpoints, and finding credentials.

## Before calling the script

### Parse the mode

Determine whether the user wants to **generate** a new image or **edit** an existing one:
- "generate", "create", "make a picture" → generate mode (default)
- "edit this image", "change the background", "modify" + provides an image → edit mode

### Parse dimensions (generate mode only)

Users often include size info naturally — extract dimensions and pass as `--width` and `--height`. Strip dimensions from the prompt to avoid confusing the model.

| User says | Prompt sent to model | Flags |
|-----------|---------------------|-------|
| "generate a 1024x1024 image of a cat" | `a cat` | `--width 1024 --height 1024` |
| "make a 1920x1080 landscape" | `a landscape` | `--width 1920 --height 1080` |
| "2048x2048 neon city" | `neon city` | `--width 2048 --height 2048` |
| "make it 2K wide" | prompt only | `--width 2048` (height auto-set to 2048) |

Patterns: `WxH`, `W×H`, `W by H`, `W X H`. Numbers between 256 and 4096.
If only one dimension specified, the other matches it (1:1 aspect ratio).
If no dimensions specified, omit flags — defaults are 1328x1328.
A seed is always included in the request — auto-generated if not specified — and printed in the output for reproducibility.

### Extract other params if mentioned

- Seed: "with seed 42" → `--seed 42`
- Negative prompt: "no text, no watermark" → `--negative-prompt "text, watermark"`
- Output location: "save to /tmp/output" → `--output-dir /tmp/output`
- Steps: "full quality" → `--steps 50` (generate) or `--steps 40` (edit)

### Edit mode specifics

Edit mode requires a source image. Extract file paths provided by the user:
- Source image: "edit this image: /path/to/image.png" → `--image /path/to/image.png`
- Reference image (optional): "using this reference: /path/to/ref.png" → `--reference-image /path/to/ref.png`

Edit mode does NOT support width/height — output inherits source image dimensions.

## Calling the script

```bash
# Generate mode (text-to-image)
python3 skills/generate-image/scripts/generate.py generate "<prompt>" [--width W --height H] [flags]

# Edit mode (image editing)
python3 skills/generate-image/scripts/generate.py edit "<prompt>" --image <path> [--reference-image <path>] [flags]
```

### Common flags

| Flag | Default | Description |
|------|---------|-------------|
| `--seed` | random | Random seed |
| `--steps` | 4 | Sampling steps (4=Lightning fast, 50=full quality for generate, 40 for edit) |
| `--negative-prompt` | "" | Negative prompt text |
| `--output-dir` | . | Output directory |
| `--filename` | auto | Output filename |
| `--async` | off | Use async mode (poll for result) |

### Generate-only flags

| Flag | Default | Description |
|------|---------|-------------|
| `--width` | 1328 | Image width (256-4096) |
| `--height` | 1328 | Image height (256-4096) |
| `--batch-size` | 1 | Number of images |

### Edit-only flags

| Flag | Default | Description |
|------|---------|-------------|
| `--image` | required | Source image file path |
| `--reference-image` | none | Optional reference image for multi-image edits |

## Error handling

If the script fails, check the error message:

| Error | Fix |
|-------|-----|
| `RUNPOD_* not set` | Instruct user to set the env var |
| `HTTP 401/403` | Invalid API key — check RunPod dashboard |
| `HTTP 404` | Wrong endpoint ID |
| `Connection error` | Network/endpoint down — retry |
| `No images in response` | May be cold start — retry once |
| `timeout` | Use `--async` mode |
| `image file not found` | Check the file path |
| `image file too large` | Compress or resize the image first |

For transient errors (timeout, no images), retry once before reporting failure.

## After generation

1. Confirm the image was saved and show the file path
2. Mention dimensions and seed used (for reproducibility)
3. For edits, note the source image used
4. If the user requests adjustments, suggest modifying prompt, seed, steps, or dimensions

## Limits

- Default resolution: 1328x1328 (generate mode only)
- Max resolution: 4096x4096
- Steps locked to 4 for Lightning (sweet spot), up to 50 for generate full quality, 40 for edit full quality
- Images saved as PNG
- Script uses only stdlib — no pip install needed

## Additional Resources

- **`references/setup.md`** — Step-by-step RunPod setup: account, endpoint deployment, credentials, GPU requirements
- **`references/endpoints.md`** — Detailed RunPod API schemas, async polling, cold start behavior, ComfyUI workflow node mapping
- **`examples/generate-examples.md`** — End-to-end usage scenarios for both generate and edit modes
