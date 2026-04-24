# CLAUDE.md

## Project Overview

Open community marketplace for Claude Code plugins. Hosted at `ZeroClue/zc-plugins`.

Install the marketplace:
```
/plugin marketplace add ZeroClue/zc-plugins
```

Each plugin lives in its own directory with a `.claude-plugin/plugin.json` manifest, or in an external GitHub repo referenced from `.claude-plugin/marketplace.json`.

## Repo Structure

```
.claude-plugin/marketplace.json   # Marketplace registry
ai-image-toolkit/                # Plugin directory
  .claude-plugin/plugin.json     # Plugin manifest
  commands/                      # Slash commands
  skills/generate-image/         # Skill with scripts, references, examples
CONTRIBUTING.md                  # Contribution guidelines
```

## Plugins

See `.claude-plugin/marketplace.json` for the current plugin registry.

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `RUNPOD_2512_ENDPOINT_ID` | RunPod serverless endpoint ID for text-to-image |
| `RUNPOD_EDIT_ENDPOINT_ID` | RunPod serverless endpoint ID for image editing |
| `RUNPOD_API_KEY` | RunPod API key (shared across both endpoints) |

Set these in `.env` at the project root (gitignored) or export them in the shell. Scripts load via `Path.cwd() / ".env"`.

## Dev Commands

```bash
# Test generate (from repo root, requires .env)
python3 ai-image-toolkit/skills/generate-image/scripts/generate.py generate "a cat"

# Test edit
python3 ai-image-toolkit/skills/generate-image/scripts/generate.py edit "make it darker" --image photo.png

# Test carousel
python3 ai-image-toolkit/skills/generate-image/scripts/carousel.py spec.md

# Test plugin locally
claude --plugin-dir ./ai-image-toolkit
```

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
