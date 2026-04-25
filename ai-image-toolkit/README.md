# ai-image-toolkit

AI image generation and editing for Claude Code, powered by Qwen Image models on [RunPod](https://runpod.io?ref=lnnwdl3q) serverless GPU.

[![Get RunPod](https://img.shields.io/badge/Get%20RunPod-Sign%20Up-8B5CF6)](https://runpod.io?ref=lnnwdl3q)
[![Deploy 2512](https://img.shields.io/badge/Deploy%20Qwen%202512-RunPod-8B5CF6)](https://console.runpod.io/hub/ZeroClue/qwen-img-2512)
[![Deploy Edit 2511](https://img.shields.io/badge/Deploy%20Edit%202511-RunPod-8B5CF6)](https://console.runpod.io/hub/ZeroClue/qwen-img-edit-2511)

## Features

- **Text-to-image** — Generate images from text prompts (Qwen Image 2512, 4-step Lightning, ~2s/image, up to 4096x4096)
- **Image editing** — Edit existing images with text instructions (Qwen Image Edit 2511, single or dual image input)
- **Multi-image carousels** — Generate visually consistent slide decks from markdown specs (auto-detected in `/generate-image`)
- **Smart prompt expansion** — Claude Code expands short prompts into detailed image specs via Agent tool (haiku model). Works for all subscribers without API keys. CLI fallback available (`--optimize`)
- **Brand config** — Define brand colors, fonts, and style in `.image-brand.json`, auto-injected into every prompt
- **Slide templates** — Built-in templates for common carousel patterns (`stat-hook`, `statement-hook`, `checklist`, `comparison`, `flow`, `split`, `cta`)
- **Split contrast modes** — Visual treatment instructions for split slides (`before-after`, `good-bad`, `old-new`, `problem-solution`, `light-dark`)
- **Edit fallback** — Automatic retry with backoff on edit failures, falls back to generate endpoint
- **Prompt logging** — Expanded prompts logged to `_prompts.jsonl` for auditing and iteration
- **Shrink guard** — Rejects optimizer output shorter than 50% of input to prevent silent content loss

## Prerequisites

This plugin requires a [RunPod](https://runpod.io?ref=lnnwdl3q) account with two serverless endpoints:

- [Deploy Qwen Image 2512](https://console.runpod.io/hub/ZeroClue/qwen-img-2512) — text-to-image worker ([source](https://github.com/ZeroClue/qwen-img-2512))
- [Deploy Qwen Image Edit 2511](https://console.runpod.io/hub/ZeroClue/qwen-img-edit-2511) — image editing worker ([source](https://github.com/ZeroClue/qwen-img-edit-2511))

Deploy both as serverless endpoints, then set three environment variables:

| Variable | Purpose |
|---|---|
| `RUNPOD_2512_ENDPOINT_ID` | Serverless endpoint ID for text-to-image |
| `RUNPOD_EDIT_ENDPOINT_ID` | Serverless endpoint ID for image editing |
| `RUNPOD_API_KEY` | RunPod API key (shared across both endpoints) |

Find these in your RunPod dashboard:
- **Endpoint ID**: Serverless > your endpoint > ID in URL or settings
- **API key**: Settings > API Keys

## Installation

```bash
claude plugin install ai-image-toolkit
```

Or for local development:

```bash
claude --plugin-dir /path/to/ai-image-toolkit
```

## Usage

Once installed, Claude Code automatically activates the skill when you ask to generate or edit images:

**Generate:**
> "Generate an image of a mountain sunset"
> "Create a 1920x1080 cyberpunk cityscape"
> "Make a picture of a cat with seed 42"

**Edit:**
> "Edit this image to change the background to a beach: /path/to/image.png"
> "Remove the text from this image: photo.png"

**Carousel (paste a spec into `/generate-image`):**
> /generate-image
> # My Carousel
> ## Slide 1 — Hook
> Dark background, bold white text...
> ## Slide 2 — Problem
> Wireframe diagram...

## Supported Models

| Model | Mode | Default Steps | Full Quality |
|---|---|---|---|
| Qwen Image 2512 | Text-to-image | 4 (Lightning) | 50 |
| Qwen Image Edit 2511 | Image editing | 4 (Lightning) | 40 |

## Parameters

### Generate & Edit (common)

| Flag | Default | Description |
|------|---------|-------------|
| `--seed` | random | Reproducible random seed |
| `--steps` | 4 | Sampling steps (4=fast ~2s, 5-8=balanced ~4-8s, 50/40=full quality ~15-30s). Auto-selects LoRA. |
| `--cfg` | auto | Override CFG scale (auto: 1.0 Lightning, 4.0 base). Endpoint v1.8.0+ |
| `--shift` | 3.1 | ModelSamplingAuraFlow shift — increase if blurry/dark, decrease for detail. Endpoint v1.8.0+ |
| `--sampler` | euler | KSampler sampler name (euler, res_multistep, etc). Endpoint v1.8.0+ |
| `--scheduler` | simple | KSampler scheduler name. Endpoint v1.8.0+ |
| `--lora` | auto | Override LoRA selection: `4step`, `8step`, `none`. Auto-selected from steps. Endpoint v1.8.0+ |
| `--negative-prompt` | "" | Negative prompt text |
| `--output-dir` | . | Output directory |
| `--filename` | auto | Output filename |
| `--sync` | off | Synchronous mode (faster when worker is warm) |
| `--brand-config` | auto | Path to `.image-brand.json` (auto-searches CWD if not specified) |

### Generate-only

| Flag | Default | Description |
|------|---------|-------------|
| `--aspect-ratio` | 1:1 | Preset ratio (1:1, 16:9, 9:16, 4:3, 3:4, 3:2, 2:3). Overrides `--width`/`--height` |
| `--width` | 1328 | Image width (256–4096) |
| `--height` | 1328 | Image height (256–4096) |
| `--batch-size` | 1 | Number of images |

### Edit-only

| Flag | Default | Description |
|------|---------|-------------|
| `--image` | required | Source image file path |
| `--reference-image` | none | Optional reference image for multi-image edits |

### Carousel

| Flag | Default | Description |
|------|---------|-------------|
| `--output-dir` | auto | Output directory (default: `./<title-slug>`) |
| `--seed` | random | Base seed (each slide gets base + index, or base for all with `--shared-seed`) |
| `--shared-seed` | off | Use the same seed for all slides — same random state across generate and edit passes |
| `--steps` | 4 | Override steps from spec |
| `--cfg` | auto | Override CFG scale. Endpoint v1.8.0+ |
| `--shift` | 3.1 | ModelSamplingAuraFlow shift. Endpoint v1.8.0+ |
| `--sampler` | euler | KSampler sampler name. Endpoint v1.8.0+ |
| `--scheduler` | simple | KSampler scheduler name. Endpoint v1.8.0+ |
| `--lora` | auto | Override LoRA: `4step`, `8step`, `none`. Endpoint v1.8.0+ |
| `--sync` | off | Synchronous mode (warm workers only) |
| `--generate-all` | off | Use generate endpoint for all slides with shared style prefix for consistency |
| `--edit-retries` | 3 | Retries per slide before fallback |
| `--no-fallback` | off | Disable automatic edit→generate fallback |
| `--brand-config` | auto | Path to `.image-brand.json` |

### Carousel spec directives

| Directive | Templates | Description |
|-----------|-----------|-------------|
| `type:` | all | Template name (stat-hook, statement-hook, checklist, comparison, flow, split, cta) |
| `number:` | stat-hook | Large centered stat (e.g. "53%") |
| `text:` | stat-hook, statement-hook | Supporting text below the stat/heading |
| `items:` | checklist | Bulleted list (one per line with `- ` prefix) |
| `icon:` | checklist | Icon for each item (e.g. "✓", "✗") |
| `left:` / `right:` | split | Content for each half |
| `contrast:` | split | Visual treatment mode (before-after, good-bad, old-new, problem-solution, light-dark) |
| `steps:` | flow | Arrow-separated steps ("Audit → Prioritize → Implement") |
| `columns:` | comparison | Pipe-separated columns ("Column A | Column B") |
| `action_text:` | cta | Bold action text |
| `url:` | cta | URL to display |
| `accent:` | any | Override accent color for this slide |
| `asset:` | any | Path to image asset to composite onto the slide |

## What's New

### v0.8.0 (2026-04-25)

- **Endpoint v1.8.0 parameters** — New flags `--cfg`, `--shift`, `--sampler`, `--scheduler`, `--lora` for fine-tuning ComfyUI workflow parameters. Exposed in generate, edit, and carousel modes.
- **8-step Lightning auto-detection** — Steps 5-8 now auto-select the 8-step Lightning LoRA for better text quality at ~4-8s generation time.
- **Step quality tiers** — Documented guidance: 4=prototyping, 8=text-heavy, 50/40=production.

### v0.7.3 (2026-04-25)

- **`--generate-all` with shared style prefix** — Text-heavy carousels (infographics, checklists, stats) now bypass the edit endpoint entirely, generating all slides via 2512 with a shared style prefix derived from brand config. The edit endpoint corrupts text due to full re-synthesis; this avoids the issue while maintaining visual consistency (see #2).
- **`--shared-seed`** — Use the same seed for all carousel slides instead of base + index. Works with both normal and `--generate-all` pipelines for consistent random state across the carousel.
- **`extract_style_prefix()`** — New template function builds a style block from brand config (colors, typography, style notes) that gets prepended to slides 2-N in generate-all mode.

### v0.7.2 (2026-04-25)

- **Fix: heading directive ignored in carousel specs** — `heading:` now overrides the `## Slide N — Description` markdown header. Previously fell through into the prompt body as noise (closes #1).
- **Fix: horizontal rules and blockquotes in specs** — `---`, `> text` lines are now skipped instead of being appended to the prompt.

### v0.7.1 (2026-04-25)

- **Parameters documentation** — Full flag reference tables for generate, edit, and carousel modes, plus carousel spec directives with template compatibility.

### v0.7.0 (2026-04-25)

- **Root cause fix: optimizer shrinking prompts** — Three fixes: (1) Checklist items use `- ` instead of `1.` to prevent collision with batch numbering, (2) System prompts refactored from "expand short prompt" to "preserve ALL detail, add specificity", (3) Batch input uses `[PROMPT N]` markers instead of plain numbered lines, with matching output parser.
- **Spec writing tips** — Added guidance on choosing `statement-hook` vs `stat-hook`, using `contrast:` on splits, keeping checklist items concise, and avoiding markdown in directives.

### v0.6.1 (2026-04-25)

- **Optimizer shrink guard** — If the optimizer produces a prompt shorter than 50% of the input, the original prompt is used instead. Prevents silent content loss when the model collapses structured content (e.g. checklists) into a one-liner.

### v0.6.0 (2026-04-25)

- **Command file prompt expansion** — `/generate-image` slash command now uses Agent tool for prompt expansion (was only in SKILL.md natural language path). Both activation paths are now consistent.
- **Split template contrast modes** — `contrast:` directive on split slides injects visual treatment instructions (`before-after`, `good-bad`, `old-new`, `problem-solution`, `light-dark`). Each side gets card containers with rounded corners.
- **Prompt logging** — Expanded prompts written to `_prompts.jsonl` in output directory when `--optimize` is active, for auditing and iteration.
- **MAGIC_SUFFIX fix** — All template functions now include "Ultra HD, 4K, cinematic composition" directly, with double-suffix protection in the optimizer fallback.

### v0.5.0 (2026-04-25)

- **Native prompt expansion** — Claude Code handles prompt expansion via Agent tool (model: haiku) instead of Python subprocess. No SDK dependency, no CLI subprocess — works for all subscribers. `--optimize` remains as CLI fallback.
- **Consistent across all modes** — Generate, edit, and carousel all use the same Agent-based expansion with full Qwen Image rules, brand config injection, and batch support for carousels.

### v0.4.0 (2026-04-25)

- **Anthropic SDK primary path** — Optimizer uses direct API call when `ANTHROPIC_API_KEY` is set (fast, no subprocess). Falls back to `claude` CLI for subscribers without API keys.
- **Batch optimization** — Carousel prompts optimized in a single API call instead of one per slide
- **Configurable word cap** — `--max-words` flag (default 500, was 200). Text/layout prompts now have room for full spatial descriptions.
- **Richer templates** — All templates now include canvas size, spacing rules, gradient bars, font specs, and positioning. Output ~80-100 words before optimization.
- **statement-hook template** — New template type for text-only hooks without a stat number
- **Broader response parsing** — `extract_images()` now checks `image`, `data`, and `url` keys in addition to `images`

### v0.3.1 (2026-04-25)

- **Qwen-specific prompt rules** — Optimizer system prompts rewritten with official Qwen Image best practices: text in double quotes with position/font, no negation words, no extra text, weighted attention syntax, magic quality suffix ("Ultra HD, 4K, cinematic composition")
- **Edit-awareness** — Optimizer handles edit instructions differently from generate, preserving original image intent
- **Prompt reference guide** — `references/qwen-image-prompt-guide.md` compiled from official Qwen sources

### v0.3.0 (2026-04-25)

- **Prompt optimizer** — `--optimize` flag expands short prompts into detailed image generation specs via the `claude` CLI. Model configurable with `--optimizer-model` (haiku/sonnet/opus, default haiku). Falls back to template-based expansion when CLI unavailable.
- **Brand config** — `.image-brand.json` defines colors, fonts, canvas size, and style notes. Auto-injected into every prompt when `--optimize` or `--brand-config` is used.
- **Slide type templates** — Carousel specs support `type:` directive with 6 built-in templates: `stat-hook`, `checklist`, `comparison`, `flow`, `split`, `cta`.
- **Edit retry + fallback** — Edit endpoint calls retry 3x with backoff (5s/10s/15s) before falling back to the generate endpoint. Configurable with `--edit-retries` and `--no-fallback`.
- **`--generate-all` flag** — Use the 2512 generate endpoint for all carousel slides, bypassing edit-based consistency entirely.
- **Debug logging** — `save_result()` now logs raw API responses on all failure paths (FAILED, IN_QUEUE/IN_PROGRESS timeout, empty images, missing data).

### v0.2.0 (2026-04-24)

- Health check endpoint (`GET /v2/{endpoint_id}/health`)
- Default to async mode to handle cold starts gracefully
- Prevent retry storms on cold starts

## License

MIT
