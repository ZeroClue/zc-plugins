# zc-plugins

Open community marketplace for Claude Code plugins.

## Install the marketplace

```
/plugin marketplace add ZeroClue/zc-plugins
```

## Available plugins

| Plugin | Description |
|--------|-------------|
| [ai-image-toolkit](./ai-image-toolkit) | AI image generation, editing, and multi-image carousels via RunPod serverless Qwen Image endpoints |

## Install a plugin

```
/plugin install ai-image-toolkit@zc-plugins
```

## Changelog

### ai-image-toolkit

- **0.7.2** (2025-04-25): Fix heading directive ignored in carousel specs, skip horizontal rules and blockquotes (#1)
- **0.7.1** (2025-04-25): Parameters documentation — full flag reference + carousel spec directives
- **0.7.0** (2025-04-25): Root cause fix for optimizer shrinking prompts (checklist collision + system prompt framing + batch delimiters), spec writing tips
- **0.6.1** (2025-04-25): Optimizer shrink guard — rejects expanded prompts shorter than 50% of input
- **0.6.0** (2025-04-25): Command file uses Agent tool for expansion, split template contrast modes, prompt logging (`_prompts.jsonl`), MAGIC_SUFFIX fix in templates
- **0.5.0** (2025-04-25): Native prompt expansion via Agent tool (haiku) for all modes, consistent Qwen rules + brand injection, `--optimize` demoted to CLI fallback
- **0.4.0** (2025-04-25): Anthropic SDK fast path, batch optimization, configurable word cap, richer templates, statement-hook template, broader response parsing
- **0.3.1** (2025-04-25): Qwen-specific prompt rules, edit-aware optimization, prompt reference guide
- **0.3.0** (2025-04-25): Prompt optimizer (`--optimize`), brand config (`.image-brand.json`), slide type templates, edit retry with fallback, `--generate-all` flag, debug logging
- **0.2.0** (2025-04-24): Health check, async default, cold start handling
- **0.1.0**: Initial release — text-to-image, image editing, multi-image carousels

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines on adding your own plugin to the marketplace.

## License

MIT
