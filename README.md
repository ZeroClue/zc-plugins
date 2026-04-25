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

- **0.4.0** (2025-04-25): Anthropic SDK fast path, batch optimization, configurable word cap, richer templates, statement-hook template, broader response parsing
- **0.3.1** (2025-04-25): Qwen-specific prompt rules, edit-aware optimization, prompt reference guide
- **0.3.0** (2025-04-25): Prompt optimizer (`--optimize`), brand config (`.image-brand.json`), slide type templates, edit retry with fallback, `--generate-all` flag, debug logging
- **0.2.0** (2025-04-24): Health check, async default, cold start handling
- **0.1.0**: Initial release — text-to-image, image editing, multi-image carousels

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines on adding your own plugin to the marketplace.

## License

MIT
