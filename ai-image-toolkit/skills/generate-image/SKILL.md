---
name: generate-image
description: This skill should be used when the user asks to "generate an image", "create a picture", "draw", "render", "illustrate", "make AI art", "edit an image", "modify this photo", "change the background", "remove the background", "style transfer", "produce a visual", "create a carousel", "make a slide deck", "generate multiple images with consistent style", or wants to create or edit images from text descriptions. Supports text-to-image (Qwen Image 2512), image editing (Qwen Image Edit 2511), and multi-image carousels via RunPod serverless endpoints.
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

Users often include size info naturally — extract dimensions and pass as `--width` and `--height`, or map natural language to `--aspect-ratio`. Strip dimensions from the prompt to avoid confusing the model.

**Aspect ratio mapping** — prefer `--aspect-ratio` when the user specifies a ratio or orientation:

| User says | Flag |
|-----------|------|
| "landscape", "widescreen", "16:9" | `--aspect-ratio 16:9` |
| "portrait", "vertical", "9:16" | `--aspect-ratio 9:16` |
| "square", "1:1" | `--aspect-ratio 1:1` |

Supported aspect ratios and their resolutions:

| Ratio | Resolution | Ratio | Resolution |
|-------|-----------|-------|-----------|
| 1:1 | 1328x1328 | 4:3 | 1472x1104 |
| 16:9 | 1664x928 | 3:4 | 1104x1472 |
| 9:16 | 928x1664 | 3:2 | 1584x1056 |
| | | 2:3 | 1056x1584 |

**Explicit dimensions** — when the user specifies exact pixels:

| User says | Prompt sent to model | Flags |
|-----------|---------------------|-------|
| "generate a 1024x1024 image of a cat" | `a cat` | `--width 1024 --height 1024` |
| "make a 1920x1080 landscape" | `a landscape` | `--width 1920 --height 1080` |
| "2048x2048 neon city" | `neon city` | `--width 2048 --height 2048` |
| "make it 2K wide" | prompt only | `--width 2048` (height auto-set to 2048) |

Patterns: `WxH`, `W×H`, `W by H`, `W X H`. Numbers between 256 and 4096.
`--aspect-ratio` takes precedence over `--width`/`--height`.
If only one dimension specified, the other matches it (1:1 aspect ratio).
If no dimensions specified, defaults are 1328x1328 (1:1).
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
| `--sync` | off | Use synchronous mode (faster when worker is warm) |
| `--brand-config` | auto | Path to `.image-brand.json` (auto-searches CWD if not specified) |

### Generate-only flags

| Flag | Default | Description |
|------|---------|-------------|
| `--aspect-ratio` | 1:1 | Preset aspect ratio (1:1, 16:9, 9:16, 4:3, 3:4, 3:2, 2:3). Overrides --width/--height |
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
| `Connection error` | Network/endpoint down |
| `No images in response` | Cold start — do NOT retry, the job may still be processing |
| `timeout` | Do NOT retry — remove `--sync` flag and use default async mode |
| `image file not found` | Check the file path |
| `image file too large` | Compress or resize the image first |

**Do not retry on timeout or "no images" errors.** RunPod serverless jobs continue processing even if the script times out. Retrying creates duplicate jobs and wastes GPU time. Report the error to the user instead.

## Prompt optimization

When the user provides a short or vague prompt, or asks for "optimized", "detailed", or "high quality" output, expand the prompt into a detailed image generation spec **before calling the script**. Do NOT pass `--optimize` to generate.py or carousel.py — handle the expansion yourself.

**How to expand prompts:**

Use the Agent tool with `model: haiku` to expand the prompt. This keeps the expansion cost minimal.

```
Agent(
  description="Expand image prompt",
  model="haiku",
  prompt="""You are an image generation prompt engineer for the Qwen Image model. Expand the user's short prompt into a detailed prompt optimized for Qwen Image's capabilities.

Qwen Image strengths: exceptional text rendering, complex multi-element layouts, infographic-style compositions, realistic photography.

Rules:
- Text/layout prompts (cards, infographics, stats, UI): expand with exact spatial positioning, font family/weight/size, hex colors for every element, element dimensions, spacing rules, background treatment. Use brand colors and fonts unless the prompt specifies otherwise.
- Photo/illustration prompts: add style, lighting, composition, mood details. If no style specified, default to realistic photography. Apply brand style notes if relevant.
- For edit instructions: keep descriptions direct and specific. Preserve the original image's core intention, only enhance clarity and visual feasibility.
- Enclose all text content in double quotes. Specify position and font style for each text element. Never alter or translate the user's text.
- Do NOT add any text the user did not explicitly request. Qwen renders text accurately — hallucinated text will appear in the image.
- Do NOT use negation words. Instead of "no text", just don't mention text. Instead of "no watermark", omit it entirely.
- You may use weighted attention syntax: (element:1.5) to emphasize, (element:0.8) to de-emphasize.
- Output ONLY the expanded prompt — no explanations, no markdown, no prefix.
- Keep the expanded prompt under 500 words.
- Be specific with colors (hex codes), sizes (pixels relative to canvas), and positions (top-left, center, etc.).
- Always end the prompt with: Ultra HD, 4K, cinematic composition

{brand_section}

Expand this prompt: <USER_PROMPT>"""
)
```

**Brand config injection:**

If a `.image-brand.json` file exists (see Brand config section below), read it and inject brand defaults into the Agent prompt. Replace `{brand_section}` with:

```
Brand config (apply these defaults):
- background: #050506
- accent: #32CD32
- text_primary: #FFFFFF
... etc from the file
```

If no brand config file exists, remove the `{brand_section}` line entirely.

The user can override the auto-discovered file by specifying a path: "use brand config /path/to/custom-brand.json" — in that case, read that file instead.

**When to expand:**
- User gives a short prompt (<20 words) for a complex layout
- User describes an infographic, card, or text-heavy image
- User explicitly asks for "optimized" or "detailed" output
- User wants consistent brand styling across multiple images
- Carousel slides with typed templates (type: checklist, stat-hook, etc.)

**When NOT to expand:**
- User provides a fully detailed prompt (300+ words with positioning, colors, fonts)
- User explicitly says "use my prompt as-is"

**Fallback:** If invoking the script directly outside Claude Code (e.g., CLI), use `--optimize` — the script has its own SDK/CLI/template optimizer.

## Brand config

Create a `.image-brand.json` file in your project root or CWD to define brand defaults. Read this file and inject its values into every optimized prompt.

```json
{
  "background": "#050506",
  "accent": "#32CD32",
  "text_primary": "#FFFFFF",
  "text_secondary": "#999999",
  "font_family": "Inter",
  "font_weight_heading": "Bold",
  "font_weight_body": "Regular",
  "canvas_size": "1080x1080",
  "style_notes": "Minimal, dark, professional infographic. No photos, no illustrations."
}
```

Look for `.image-brand.json` in CWD, project root, or the plugin directory. When found, include all key-value pairs in the brand_section of the prompt expansion request. The user can override auto-discovery by specifying a path with `--brand-config /path/to/file.json`.

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

## Multi-image carousels

For projects requiring visual consistency across multiple images (Instagram carousels, presentation slides, brand assets), use the carousel workflow. Paste a markdown spec into `/generate-image` — the command auto-detects `## Slide` headers and routes to the carousel script:

```
/generate-image
# Carousel Title
aspect-ratio: 1:1

## Slide 1 — Hook
Prompt text...

## Slide 2 — Problem
Prompt text...
```

Or invoke the script directly:

```bash
python3 skills/generate-image/scripts/carousel.py carousel-spec.md [--output-dir ./output] [--seed N] [--steps N]
```

Slide 1 is generated via text-to-image, subsequent slides use slide 1 as a style reference via the edit endpoint. Slides with `asset:` lines get multi-pass treatment — a style pass followed by asset compositing passes.

**Carousel flags:**

| Flag | Default | Description |
|------|---------|-------------|
| `--output-dir` | auto | Output directory (default: `./<title-slug>`) |
| `--seed` | random | Base seed (each slide gets base + index) |
| `--steps` | 4 | Override steps from spec |
| `--sync` | off | Synchronous mode (warm workers only) |
| `--generate-all` | off | Use generate endpoint for all slides (no edit consistency) |
| `--edit-retries` | 3 | Retries per slide before fallback |
| `--no-fallback` | off | Disable automatic edit→generate fallback |
| `--brand-config` | auto | Path to `.image-brand.json` |

**Spec format (full prompts):**
```markdown
# Carousel Title
aspect-ratio: 1:1
steps: 4

## Slide 1 — Hook
Prompt text describing the first slide...

## Slide 5 — CTA
asset: /path/to/logo.png
Prompt describing the slide, referencing the asset location...
```

**Spec format (typed templates):**
```markdown
# Carousel Title
aspect-ratio: 1:1

## Slide 1 — The Problem
type: stat-hook
number: 53%
text: of websites fail to convert visitors

## Slide 2 — What's Broken
type: checklist
icon: X
items:
  - Title tags missing or generic
  - Meta descriptions empty
  - Images at 5MB each
accent: "#FF4500"

## Slide 3 — Before vs After
type: split
left: Broken mobile form
right: Clean tappable button

## Slide 4 — The Fix
type: flow
steps: Audit → Prioritize → Implement → Measure

## Slide 5 — Get Started
type: cta
action_text: Free website audit
url: example.com/audit
```

**Built-in templates:** `stat-hook`, `checklist`, `comparison`, `flow`, `split`, `cta`. Templates auto-expand into full prompts with brand config colors, fonts, and layout.

**Carousel prompt expansion:**

Expand carousel slide prompts via the Agent tool **before** running the carousel script, using a single batch call:

```
Agent(
  description="Expand carousel prompts",
  model="haiku",
  prompt="""You are an image generation prompt engineer for the Qwen Image model. Expand each numbered prompt into a detailed prompt optimized for Qwen Image's capabilities.

Qwen Image strengths: exceptional text rendering, complex multi-element layouts, infographic-style compositions, realistic photography.

Rules per prompt:
- Text/layout prompts: expand with exact spatial positioning, font family/weight/size, hex colors for every element, element dimensions, spacing rules, background treatment. Use brand colors and fonts unless the prompt specifies otherwise.
- Photo/illustration prompts: add style, lighting, composition, mood details. Default to realistic photography if unspecified. Apply brand style notes if relevant.
- Enclose all text content in double quotes with position and font style. Never alter the user's text.
- Do NOT add extra text the user didn't request. Do NOT use negation words.
- Keep each expanded prompt under 500 words.
- Be specific with colors (hex codes), sizes, and positions.
- End each expanded prompt with: Ultra HD, 4K, cinematic composition

Output format — return each expanded prompt on a separate line, prefixed with its number and a colon:
1: <expanded prompt 1>
2: <expanded prompt 2>
...

{brand_section}

Expand these prompts:
<numbered_prompts>"""
)
```

Then substitute the expanded prompts back into the spec (or pass them as fully-expanded prompts in the spec file) before running the carousel script. Do NOT pass `--optimize` to carousel.py.

**Fallback:** If invoking the carousel script directly from CLI, `--optimize` is available — the script uses its own batch optimizer.

See `examples/carousel-example.md` for a complete worked example.

## Additional Resources

- **`references/qwen-image-prompt-guide.md`** — Official Qwen Image prompt engineering guide: text rendering rules, optimizer system prompt, edit task templates, layout examples, weighted attention syntax
- **`references/setup.md`** — Step-by-step RunPod setup: account, endpoint deployment, credentials, GPU requirements
- **`references/endpoints.md`** — Detailed RunPod API schemas, async polling, cold start behavior, ComfyUI workflow node mapping
- **`examples/generate-examples.md`** — End-to-end usage scenarios for both generate and edit modes
- **`examples/carousel-example.md`** — Complete carousel spec example with 5 slides and asset compositing
