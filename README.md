# Claude Conversation Extractor Plugin

A Claude Code plugin that extracts conversations to well-named markdown files.

## Features

- Extract the current conversation with a single command
- Automatically suggests descriptive filenames based on conversation content
- Includes full tool use and system messages for complete context
- Works on Windows, macOS, and Linux

## Installation

### From EUSD Marketplace

```bash
# Add the EUSD marketplace (one-time)
/plugin marketplace add eusd-server-engineer/claude-code-marketplace

# Install the plugin
/plugin install conversation-extractor
```

### Direct Installation

```bash
/plugin install eusd-server-engineer/claude-conversation-extractor-plugin
```

## Usage

Simply run the slash command in any Claude Code session:

```
/extract-conversation
```

You'll be prompted to provide a descriptive filename. The conversation will be saved to the current working directory.

### With a filename hint

```
/extract-conversation api-debugging-session
```

## Output Format

The extracted conversation is saved as a markdown file with the format:

```
claude-conversation-YYYY-MM-DD-descriptive-name.md
```

Example: `claude-conversation-2025-01-15-excel-to-google-sheets-migration.md`

## Dependencies

This plugin uses [claude-conversation-extractor](https://github.com/ZeroSumQuant/claude-conversation-extractor) under the hood. It will be automatically installed via `uv` when you first run the command.

## License

MIT License - See LICENSE file for details.

## Contributing

Issues and pull requests welcome at: https://github.com/eusd-server-engineer/claude-conversation-extractor-plugin
