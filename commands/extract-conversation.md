---
description: Extract the current Claude Code conversation to a markdown file with a descriptive name
argument-hint: "[filename-hint]"
---

# /extract-conversation

Extract the current Claude Code conversation to a well-named markdown file in the current directory.

## Instructions

When the user invokes `/extract-conversation`, follow these steps:

### Step 1: Ensure the extraction tool is installed

Run:
```bash
uv tool install claude-conversation-extractor 2>/dev/null || echo "Already installed"
```

### Step 2: List available conversations

Run this command to find the current conversation:
```bash
PYTHONIOENCODING=utf-8 claude-extract --list 2>&1 | head -20
```

The current conversation will typically be #1 (most recent) and will match the current working directory.

### Step 3: Ask the user for a descriptive filename

Use the AskUserQuestion tool to ask the user what they want to name the file. Suggest a name based on the main topic of conversation. The format should be:
- `claude-conversation-YYYY-MM-DD-descriptive-topic.md`

For example:
- `claude-conversation-2025-01-15-excel-to-google-sheets-migration.md`
- `claude-conversation-2025-01-15-api-authentication-debugging.md`

If the user provided an argument hint, use that as the basis for the filename.

### Step 4: Extract the conversation

Run the extraction with the `--detailed` flag to include tool use:
```bash
PYTHONIOENCODING=utf-8 claude-extract --extract 1 --output "$(pwd)" --detailed 2>&1
```

### Step 5: Rename to the descriptive filename

The tool creates a file like `claude-conversation-YYYY-MM-DD-sessionid.md`. Rename it to the user's chosen name:
```bash
mv claude-conversation-*.md "user-chosen-filename.md"
```

### Step 6: Confirm completion

Tell the user the file has been created and show the full path.

## Notes

- The `PYTHONIOENCODING=utf-8` prefix is required on Windows to handle emoji output
- The `--detailed` flag includes tool invocations and system messages for full context
- If the user wants a different conversation (not #1), they can specify which number to extract
