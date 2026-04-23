# Contributing to zc-plugins

Open community marketplace for Claude Code plugins.

## Two ways to contribute

### 1. In-tree plugin

Add your plugin directly to this repo. Good for small plugins.

1. Fork this repo
2. Create your plugin directory at the repo root (e.g. `my-plugin/`)
3. Add your plugin with the required structure (see below)
4. Open a PR

### 2. External repo

Host your plugin in your own GitHub repo. Add a registry entry here.

1. Create your plugin in your own repo
2. Fork this repo
3. Add an entry to `.claude-plugin/marketplace.json` in the `plugins` array:

```json
{
  "name": "my-plugin",
  "source": {
    "source": "github",
    "repo": "your-username/your-plugin-repo"
  },
  "description": "What your plugin does",
  "version": "1.0.0",
  "author": { "name": "Your Name" },
  "keywords": ["relevant", "tags"]
}
```

4. Open a PR

## Requirements

Every plugin must have:

- `.claude-plugin/plugin.json` — plugin manifest with `name` (kebab-case) and `version`
- At least one component: skill, command, agent, or hook
- `README.md` — what the plugin does, how to use it
- `LICENSE` — open source license

Plugin names must be unique within this marketplace.

## Validation

Before opening a PR, validate your plugin:

```bash
claude plugin validate .
```

Must pass with no errors.

## Questions

Open an issue if you have questions about contributing.
