# CLAUDE.md

## Project Overview

Open community marketplace for Claude Code plugins. Hosted at `ZeroClue/zc-plugins`.

Each plugin lives in its own directory with a `.claude-plugin/plugin.json` manifest, or in an external GitHub repo referenced from `.claude-plugin/marketplace.json`.

## Repo Structure

```
.claude-plugin/marketplace.json          # Marketplace registry
ai-image-toolkit/                        # Plugin directory
  .claude-plugin/plugin.json             # Plugin manifest
  commands/generate-image.md             # Slash command handler
  skills/generate-image/
    SKILL.md                             # Skill definition (Agent tool expansion rules)
    scripts/
      generate.py                        # Generate/edit entry point
      carousel.py                        # Multi-slide carousel generator
      optimize.py                        # Prompt optimizer (SDK/CLI/template fallback)
      templates.py                       # Slide type templates (7 built-in)
      brand.py                           # .image-brand.json loader
    references/                          # Qwen Image docs, RunPod API, setup guide
    examples/                            # Carousel spec examples
CONTRIBUTING.md                          # Contribution guidelines
.github/ISSUE_TEMPLATE/                  # Bug report & feature request templates
```

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `RUNPOD_2512_ENDPOINT_ID` | RunPod serverless endpoint ID for text-to-image |
| `RUNPOD_EDIT_ENDPOINT_ID` | RunPod serverless endpoint ID for image editing |
| `RUNPOD_API_KEY` | RunPod API key (shared across both endpoints) |

Set these in `.env` at the project root (gitignored) or export them in the shell. Scripts load via `Path.cwd() / ".env"`.

## Dev Commands

```bash
# Syntax check all scripts (fast, no network)
python3 -m py_compile ai-image-toolkit/skills/generate-image/scripts/*.py && echo OK

# Test generate (from repo root, requires .env)
python3 ai-image-toolkit/skills/generate-image/scripts/generate.py generate "a cat"

# Test edit
python3 ai-image-toolkit/skills/generate-image/scripts/generate.py edit "make it darker" --image photo.png

# Test carousel
python3 ai-image-toolkit/skills/generate-image/scripts/carousel.py spec.md

# Test plugin locally
claude --plugin-dir ./ai-image-toolkit

# Install from marketplace
# /plugin install ai-image-toolkit@zc-plugins
```

## GitHub Issues

Labels: `bug`, `enhancement`, `documentation`, `good first issue`, `ai-image-toolkit`
Use `gh issue` CLI. Reference issue numbers in fix commits.

## RunPod Behavior

- Scripts default to async (run + poll). `--sync` for warm workers only
- Cold starts are normal — health check: `GET /v2/{endpoint_id}/health`
- Never retry on timeout — jobs continue on RunPod; retrying creates duplicates

## Gotchas

- Edit endpoint has no width/height — output inherits source image dimensions
- Step quality tiers: 4=Lightning fast (prototyping), 8=balanced (text-heavy), 50/40=full quality (production). Auto-selects LoRA from steps via endpoint v1.8.0.
- `.image-brand.json` auto-discovery order: `--brand-config` path > CWD > project root > plugin root
- New carousel spec directives must be added to `parse_spec()` handler in carousel.py — unhandled directives silently pollute the prompt
- `---`, `***`, `___` and `> ` lines in specs are skipped, not parsed

## Plugin Architecture

Skills (SKILL.md) and commands (commands/*.md) are separate activation paths:
- Natural language ("generate an image...") → SKILL.md
- Slash command (`/generate-image`) → commands/generate-image.md
Changes to SKILL.md do NOT propagate to the command file — update both.
Command files need `allowed-tools: Agent` for sub-agent expansion to work.

## Version Bumps

Every version bump must update BOTH `plugin.json` and `marketplace.json`.
The plugin version appears in 4 places: both JSON files + both READMEs.

## Optimizer Gotchas

Three-tier fallback: SDK (ANTHROPIC_API_KEY) → CLI (`claude` binary) → template.
Templates produce rich prompts — optimizer must "preserve ALL detail, never summarize."
Checklist items use `- ` not `N. ` to avoid collision with batch numbering.
Batch input uses `[PROMPT N]` delimiters, not plain numbered lines.

## Endpoint Repos

Two public RunPod endpoint repos with their own ComfyUI workflows and handler.py:
- `ZeroClue/qwen-img-2512` — text-to-image endpoint
- `ZeroClue/qwen-img-edit-2511` — image editing endpoint
Read files without cloning: `gh api repos/ZeroClue/qwen-img-2512/contents/handler.py --jq '.content' | base64 -d`
Workflow parameters (cfg, shift, sampler, lora) are set in handler.py `build_workflow()` — the plugin just passes them through.
