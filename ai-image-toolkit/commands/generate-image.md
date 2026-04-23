---
name: generate-image
description: Generate or edit AI images with full parameter control. Use for explicit image generation or editing with specific settings like seed, dimensions, steps, or output path.
argument-hint: "[generate|edit] <prompt> [--width W --height H] [--seed N] [--steps N] [--image <path>] [--output-dir <path>]"
allowed-tools: Bash(*)
---

# Generate Image

Generate or edit images via RunPod serverless Qwen Image endpoints with explicit parameters.

## Usage

The user provides a mode (generate or edit) and a prompt, plus optional flags. Parse the arguments and invoke the script.

### Mode: generate (text-to-image)

If the user provides `generate` or omits the mode:

```bash
python3 skills/generate-image/scripts/generate.py generate "<prompt>" [--width W --height H] [--seed N] [--steps N] [--negative-prompt "text"] [--output-dir <path>] [--filename <name>] [--batch-size N] [--async]
```

### Mode: edit (image editing)

If the user provides `edit`:

```bash
python3 skills/generate-image/scripts/generate.py edit "<prompt>" --image <path> [--reference-image <path>] [--seed N] [--steps N] [--negative-prompt "text"] [--output-dir <path>] [--filename <name>] [--async]
```

## Parsing the arguments

The `argument-hint` text may come as a single string. Parse it to determine:

1. **Mode**: first word is `generate` or `edit`. If missing, default to `generate`.
2. **Prompt**: the text after the mode, before any `--` flags. Strip quotes.
3. **Flags**: standard `--flag value` pairs. Pass them through to the script.

### Examples

| User input | Parsed command |
|---|---|
| `a cat on a windowsill` | `generate "a cat on a windowsill"` |
| `generate a sunset --width 1920 --height 1080` | `generate "a sunset" --width 1920 --height 1080` |
| `edit remove the background --image photo.png` | `edit "remove the background" --image photo.png` |
| `a dragon --seed 42 --steps 50 --output-dir /tmp` | `generate "a dragon" --seed 42 --steps 50 --output-dir /tmp` |

## Quick reference

| Flag | Default | Description |
|---|---|---|
| `--width` | 1328 | Image width, 256-4096 (generate only) |
| `--height` | 1328 | Image height, 256-4096 (generate only) |
| `--seed` | random | Reproducible seed |
| `--steps` | 4 | 4=fast, 50=full quality (generate), 40=full quality (edit) |
| `--image` | required | Source image path (edit only) |
| `--reference-image` | none | Reference image (edit only) |
| `--negative-prompt` | "" | What to avoid |
| `--output-dir` | . | Where to save |
| `--filename` | auto | Output filename |
| `--batch-size` | 1 | Number of images (generate only) |
| `--async` | off | Use async mode for long jobs |

## After running

1. Report the saved file path and dimensions
2. Mention the seed used for reproducibility
3. If it failed, suggest: retry once for transient errors, use `--async` for timeouts, check env vars for config errors
