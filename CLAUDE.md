# CLAUDE.md

## Project Overview

Open community marketplace for Claude Code plugins. Hosted at `ZeroClue/zc-plugins`.

Install the marketplace:
```
/plugin marketplace add ZeroClue/zc-plugins
```

Each plugin lives in its own directory with a `.claude-plugin/plugin.json` manifest, or in an external GitHub repo referenced from `.claude-plugin/marketplace.json`.

## Plugins

### ai-image-toolkit

AI image generation and editing via RunPod serverless Qwen Image endpoints.

- **Qwen Image 2512** (`generate` mode) — text-to-image, 4-step Lightning LoRA (~2s/image), up to 4096x4096
- **Qwen Image Edit 2511** (`edit` mode) — image editing from text instructions, 4-step Lightning or 40-step full quality
- **Multi-image carousels** — visually consistent slide decks from markdown specs

Worker repos: [ZeroClue/qwen-img-2512](https://github.com/ZeroClue/qwen-img-2512), [ZeroClue/qwen-img-edit-2511](https://github.com/ZeroClue/qwen-img-edit-2511)

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `RUNPOD_2512_ENDPOINT_ID` | RunPod serverless endpoint ID for text-to-image |
| `RUNPOD_EDIT_ENDPOINT_ID` | RunPod serverless endpoint ID for image editing |
| `RUNPOD_API_KEY` | RunPod API key (shared across both endpoints) |

Set these in `.env` at the project root (gitignored) or export them in the shell. Scripts load via `Path.cwd() / ".env"`.

## API Patterns

Both endpoints use RunPod's serverless API:

```
POST https://api.runpod.ai/v2/{endpoint_id}/runsync   # sync
POST https://api.runpod.ai/v2/{endpoint_id}/run        # async submit
GET  https://api.runpod.ai/v2/{endpoint_id}/status/{id} # async poll
```

Response: `{"status": "COMPLETED", "output": {"images": [{"data": "base64..."}]}}`

## RunPod Behavior

- Scripts default to async (run + poll). `--sync` for warm workers only
- Cold starts are normal — health check: `GET /v2/{endpoint_id}/health`
- Never retry on timeout — jobs continue on RunPod; retrying creates duplicates

## Gotchas

- Edit endpoint has no width/height — output inherits source image dimensions
- Marketplace version bumps must update both `plugin.json` and `marketplace.json`

## Installing Plugins

```bash
# Add the marketplace
/plugin marketplace add ZeroClue/zc-plugins

# Install a plugin
/plugin install ai-image-toolkit@zc-plugins

# Or test locally
claude --plugin-dir /path/to/zc-plugins/ai-image-toolkit
```
