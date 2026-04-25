# ai-image-toolkit

AI image generation and editing for Claude Code, powered by Qwen Image models on [RunPod](https://runpod.io?ref=lnnwdl3q) serverless GPU.

[![Get RunPod](https://img.shields.io/badge/Get%20RunPod-Sign%20Up-8B5CF6)](https://runpod.io?ref=lnnwdl3q)
[![Deploy 2512](https://img.shields.io/badge/Deploy%20Qwen%202512-RunPod-8B5CF6)](https://console.runpod.io/hub/ZeroClue/qwen-img-2512)
[![Deploy Edit 2511](https://img.shields.io/badge/Deploy%20Edit%202511-RunPod-8B5CF6)](https://console.runpod.io/hub/ZeroClue/qwen-img-edit-2511)

## Features

- **Text-to-image** — Generate images from text prompts (Qwen Image 2512, 4-step Lightning, ~2s/image, up to 4096x4096)
- **Image editing** — Edit existing images with text instructions (Qwen Image Edit 2511, single or dual image input)
- **Multi-image carousels** — Generate visually consistent slide decks from markdown specs (auto-detected in `/generate-image`)
- **Prompt optimizer** — Expand short prompts into detailed image specs via `claude` CLI (`--optimize`, configurable model)
- **Brand config** — Define brand colors, fonts, and style in `.image-brand.json`, auto-injected into every prompt
- **Slide templates** — Built-in templates for common carousel patterns (`stat-hook`, `checklist`, `comparison`, `flow`, `split`, `cta`)
- **Edit fallback** — Automatic retry with backoff on edit failures, falls back to generate endpoint

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

## What's New

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
