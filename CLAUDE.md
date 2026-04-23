# CLAUDE.md

## Project Overview

Shared Claude Code skills/plugins repo. Skills live in `.claude/skills/<name>/` and can be symlinked into any project's `.claude/skills/` directory for use.

## Current Skills

### generate-image

Unified image generation skill supporting two RunPod serverless endpoints:

- **Qwen Image 2512** (`generate` mode) — text-to-image, 4-step Lightning LoRA (~2s/image), up to 4096x4096
- **Qwen Image Edit 2511** (`edit` mode) — image editing from text instructions, single or dual image input, 4-step Lightning (~2-5s) or 40-step full quality (~15-30s)

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `RUNPOD_2512_ENDPOINT_ID` | RunPod serverless endpoint ID for 2512 text-to-image |
| `RUNPOD_EDIT_ENDPOINT_ID` | RunPod serverless endpoint ID for edit-2511 image editing |
| `RUNPOD_API_KEY` | RunPod API key (shared across both endpoints) |

Set these in the project's `.env` file (gitignored) or export them in the shell.

## Source Projects

The skills in this repo are derived from three companion RunPod serverless worker repos. All three share identical `src/start.sh`, `scripts/`, `requirements.txt`, and Dockerfile patterns.

### qwen_img_2512 (`~/projects/qwen_img_2512`)

**GitHub:** `ZeroClue/qwen-img-2512` | **Purpose:** Text-to-image generation

Key details:
- Simplified input: `{"prompt": "...", "seed": N, "width": 1328, "height": 1328, "steps": 4, "negative_prompt": "", "batch_size": 1}`
- Default resolution: 1328x1328, max 4096x4096
- Lightning mode: steps <= 4 (LoRA on, CFG=1), Full quality: 50 steps (CFG=4)
- Switch pattern: `PrimitiveBoolean` node feeds three `Switch` nodes selecting model/LoRA, steps, CFG
- Workflow node IDs use `"238:XXX"` pattern (e.g. `"238:227"` for text encode, `"238:229"` for switch)
- Models: `qwen_image_2512_fp8_e4m3fn.safetensors` (diffusion), `qwen_2.5_vl_7b_fp8_scaled.safetensors` (CLIP), `qwen_image_vae.safetensors` (VAE), `Qwen-Image-2512-Lightning-4steps-V1.0-fp32.safetensors` (LoRA)
- Docker image: `nvidia/cuda:12.8.0-cudnn-runtime-ubuntu24.04`, PyTorch cu128

### qwen_img_edit_2511 (`~/projects/qwen_img_edit_2511`)

**GitHub:** `ZeroClue/qwen-img-edit-2511` | **Purpose:** Image editing with text instructions

Key details:
- Simplified input: `{"prompt": "edit instruction", "image": "base64...", "reference_image": "base64..." (optional), "seed": N, "steps": 4, "negative_prompt": ""}`
- No width/height params — output inherits dimensions from source image
- Lightning mode: steps <= 4 (LoRA on, CFG=1), Full quality: 40 steps (CFG=4)
- Switch pattern same as 2512 but with different node IDs
- Workflow node IDs: `"41"` (source image loader), `"83"` (reference image loader), `"170:151"` (positive prompt), `"170:149"` (negative prompt), `"170:169"` (KSampler seed), `"170:168"` (switch boolean)
- If no reference image provided, source image is reused (single-image edit)
- Models: `qwen_image_edit_2511_fp8mixed.safetensors` (diffusion), shared CLIP/VAE, `Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors` (LoRA)
- Known bug: `comfy-manager-set-mode.sh` uses `$CFG_FILE` instead of `$MODE` — deploys will fail on that script

### qwen_img_8step (`~/projects/qwen_img_8step`)

**GitHub:** `ZeroClue/qwen-img-8step` | **Purpose:** Original text-to-image, 8-step Lightning

This is the older model superseded by 2512. Not directly used in the plugin but serves as the original implementation reference. Same architecture pattern as the other two.

## API Patterns

### RunPod Serverless API

Both endpoints use the same RunPod API pattern:

```
POST https://api.runpod.ai/v2/{endpoint_id}/runsync
Authorization: Bearer {api_key}
Content-Type: application/json

{"input": {...params...}}
```

For longer jobs, use async:
```
POST https://api.runpod.ai/v2/{endpoint_id}/run         # submit
GET  https://api.runpod.ai/v2/{endpoint_id}/status/{id}  # poll
```

Response format:
```json
{
  "status": "COMPLETED",
  "output": {
    "images": [{"data": "base64...", "filename": "image.png"}]
  }
}
```

### Image Upload for Edit Mode

Edit endpoint requires base64-encoded source images. The handler decodes them and POSTs to ComfyUI's `/upload/image` endpoint. The skill script handles this automatically — users provide a file path, the script reads and base64-encodes it.

## Known Issues

- RunPod Hub tests are intentionally disabled (`.runpod/tests_.json`) due to platform HTTP-401 bug — do not re-enable without verifying
- `comfy-manager-set-mode.sh` in edit-2511 has unfixed printf bug — deploys will fail on that script
- RunPod cold starts can cause first-request timeouts — use async mode or retry once
- ComfyUI custom nodes installed via `comfy-node-install.sh` which wraps `comfy node install --mode=remote`

## Skill Installation

To use a skill from this repo in another project:

```bash
# Symlink the skill directory
ln -s /path/to/zc-plugins/.claude/skills/generate-image /path/to/target-project/.claude/skills/generate-image
```
