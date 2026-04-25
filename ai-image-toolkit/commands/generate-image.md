---
name: generate-image
description: Generate or edit AI images with full parameter control. Use for explicit image generation or editing with specific settings like seed, dimensions, steps, or output path.
argument-hint: "[generate|edit] <prompt> [flags] | <carousel-spec> [--seed N] [--output-dir <path>]"
allowed-tools: Bash(*), Agent
---

# Generate Image

Generate or edit images via RunPod serverless Qwen Image endpoints with explicit parameters.

## Prompt expansion

Before calling any script, check if the prompt needs expansion. If the user asks for "optimized", "detailed", or "high quality" output, or the prompt is short (<20 words) for a complex layout, expand it first using the Agent tool:

```
Agent(
  description="Expand image prompt",
  model="haiku",
  prompt="""... Qwen Image expansion rules from SKILL.md ..."""
)
```

See the **Prompt optimization** section in `skills/generate-image/SKILL.md` for the full Agent tool template, brand config injection rules, and when to/not to expand. Use the expanded prompt as the `<prompt>` argument to the script.

**Do NOT pass `--optimize` to generate.py or carousel.py** — handle expansion yourself via the Agent tool. The `--optimize` flag is a fallback for direct CLI usage only.

## Carousel detection

If the user's input contains `## Slide` (a markdown carousel spec):

1. **Expand prompts first** — For each slide prompt (or typed template), use the Agent tool with `model: haiku` to expand them. See the **Carousel prompt expansion** section in `skills/generate-image/SKILL.md` for the batch expansion template. Substitute expanded prompts back into the spec.
2. Save the full input text (with expanded prompts) to a temporary file (e.g. `/tmp/carousel-spec-{timestamp}.md`)
3. Extract any flags the user appended after the spec (e.g. `--seed 42`, `--output-dir ./output`, `--steps 4`, `--sync`)
4. Run:
   ```bash
   python3 skills/generate-image/scripts/carousel.py /tmp/carousel-spec-{timestamp}.md [--output-dir <path>] [--seed N] [--steps N] [--sync]
   ```
5. Report the output directory, number of slides generated, and base seed

If no `## Slide` pattern found, proceed with normal generate/edit parsing below.

## Usage

The user provides a mode (generate or edit) and a prompt, plus optional flags. Parse the arguments and invoke the script.

### Mode: generate (text-to-image)

If the user provides `generate` or omits the mode:

```bash
python3 skills/generate-image/scripts/generate.py generate "<prompt>" [--width W --height H] [--seed N] [--steps N] [--negative-prompt "text"] [--output-dir <path>] [--filename <name>] [--batch-size N] [--sync]
```

### Mode: edit (image editing)

If the user provides `edit`:

```bash
python3 skills/generate-image/scripts/generate.py edit "<prompt>" --image <path> [--reference-image <path>] [--seed N] [--steps N] [--negative-prompt "text"] [--output-dir <path>] [--filename <name>] [--sync]
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
| Carousel spec with `## Slide` headers | Expand prompts via Agent, save to temp file, run `carousel.py` |

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
| `--sync` | off | Use synchronous mode (faster when worker is warm) |

## After running

1. Report the saved file path and dimensions
2. Mention the seed used for reproducibility
3. If it failed, suggest: retry once for transient errors, use async mode for timeouts, check env vars for config errors
