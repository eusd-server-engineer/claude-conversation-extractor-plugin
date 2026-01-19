#!/usr/bin/env python3
"""
Rename Claude conversation extracts with date ranges and add Obsidian frontmatter.

Output format: MM-DD-YYYY--MM-DD-YYYY-description.md

Frontmatter includes:
- session_id: Original session ID for matching during updates
- start_date: First message date
- end_date: Latest message date
- title: Human-readable title
- project: Project/directory name
"""

import re
import sys
import io
from pathlib import Path
from datetime import datetime

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def extract_session_id(content: str) -> str | None:
    """Extract session ID from content."""
    match = re.search(r'Session ID:\s*([a-f0-9-]+)', content, re.IGNORECASE)
    if match:
        return match.group(1)
    return None


def extract_start_date(content: str) -> datetime | None:
    """Extract the session start date from the header."""
    # Format: Date: 2026-01-13 22:58:44
    match = re.search(r'^Date:\s*(\d{4}-\d{2}-\d{2})', content, re.MULTILINE)
    if match:
        return datetime.strptime(match.group(1), "%Y-%m-%d")
    return None


def extract_latest_date(content: str) -> datetime | None:
    """Find the latest date mentioned in the content."""
    # Look for dates in various formats
    dates = []

    # Format: 2026-01-13 or 2026-01-13 22:58:44
    for match in re.finditer(r'(\d{4})-(\d{2})-(\d{2})', content):
        try:
            d = datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)))
            # Sanity check - should be reasonable date
            if 2020 <= d.year <= 2030:
                dates.append(d)
        except ValueError:
            pass

    return max(dates) if dates else None


def extract_project_name(content: str) -> str | None:
    """Try to extract project/directory name from content."""
    # Look for working directory mentions - be strict about format
    patterns = [
        r'Working directory:\s*[A-Z]:\\Users\\[^\\]+\\Projects\\([a-zA-Z0-9_-]+)',
        r'Working directory:\s*[A-Z]:\\Users\\[^\\]+\\Downloads\\([a-zA-Z0-9_-]+)',
        r'C:\\Users\\[^\\]+\\Projects\\([a-zA-Z0-9_-]+)[\s\\"]',
    ]

    for pattern in patterns:
        match = re.search(pattern, content)
        if match:
            project = match.group(1)
            # Validate it looks like a project name (not garbage)
            if len(project) > 2 and len(project) < 50 and not project.startswith('-'):
                return project
    return None


def sanitize_description(desc: str) -> str:
    """Clean up description to be filename-safe."""
    # Remove any non-alphanumeric except hyphens
    desc = re.sub(r'[^a-z0-9-]', '-', desc.lower())
    # Collapse multiple hyphens
    desc = re.sub(r'-+', '-', desc)
    # Remove leading/trailing hyphens
    desc = desc.strip('-')
    # Limit length
    return desc[:50] if desc else "conversation"


def is_agent_session(content: str, filename: str) -> bool:
    """Check if this is a subagent session."""
    if 'agent-' in filename.lower():
        return True
    if 'subagent' in content.lower()[:500]:
        return True
    return False


def generate_description(content: str, project_name: str | None, filename: str = "") -> str:
    """Generate a short description from the conversation content."""

    # For agent/subagent sessions, just use project name + "subagent"
    if is_agent_session(content, filename):
        if project_name and len(project_name) < 30:
            clean_name = sanitize_description(project_name)
            if clean_name and len(clean_name) > 2:
                return f"{clean_name}-subagent"
        return "subagent"

    # Get the first user message - be more careful to get actual user text
    # Look for User header followed by actual content (not system stuff)
    match = re.search(r'## 👤 User\s*\n\s*([^#\n][^\n]*)', content)
    if not match:
        # Try alternate format
        match = re.search(r'## Human\s*\n\s*([^#\n][^\n]*)', content)

    if match:
        first_msg = match.group(1).strip()[:200]

        # Skip if it looks like system content
        if first_msg.startswith('`') or first_msg.startswith('{') or 'Caveat:' in first_msg:
            first_msg = ""
        else:
            first_msg_lower = first_msg.lower()

            # Common topic patterns
            if 'excel' in first_msg_lower and ('google' in first_msg_lower or 'sheet' in first_msg_lower):
                return "excel-to-sheets-migration"
            if 'mitel' in first_msg_lower:
                return "mitel-skill-development"
            if 'read' in first_msg_lower and 'ai' in first_msg_lower:
                return "read-ai-clone"
            if 'milestone' in first_msg_lower or 'powershell' in first_msg_lower:
                return "milestone-powershell"
            if 'plugin' in first_msg_lower:
                return "plugin-development"
            if 'test' in first_msg_lower:
                return "testing"
            if 'bug' in first_msg_lower or 'fix' in first_msg_lower:
                return "bugfix"
            if 'feature' in first_msg_lower:
                return "feature-development"
            if 'extract' in first_msg_lower and 'conversation' in first_msg_lower:
                return "conversation-extraction"

    # Fall back to project name
    if project_name:
        return sanitize_description(project_name)

    return "conversation"


def create_frontmatter(session_id: str, start_date: datetime, end_date: datetime,
                       title: str, project: str | None, is_subagent: bool = False) -> str:
    """Create Obsidian-style YAML frontmatter optimized for Bases."""
    lines = [
        "---",
        f"session_id: {session_id}",
        f'title: "{title}"',
        f"start_date: {start_date.strftime('%Y-%m-%d')}",
        f"end_date: {end_date.strftime('%Y-%m-%d')}",
    ]

    if project:
        lines.append(f'project: "{project}"')

    # Conversation type
    conv_type = "subagent" if is_subagent else "conversation"
    lines.append(f'conversation_type: "{conv_type}"')

    # Status tracking
    lines.append('status: "complete"')
    lines.append("is_archived: false")
    lines.append("has_actionable_outcomes: false")
    lines.append('outcome_summary: ""')

    # Quality indicators
    lines.append('ai_model: "claude-opus-4-5"')
    lines.append("is_reviewed: false")

    # Categorization
    lines.append("topics: []")
    lines.append("related_conversations: []")
    lines.append("tags: [claude-code, conversation]")

    lines.append("---")
    lines.append("")

    return "\n".join(lines)


def add_frontmatter_to_content(content: str, frontmatter: str) -> str:
    """Add frontmatter to content, replacing any existing frontmatter."""
    # Remove existing frontmatter if present
    if content.startswith("---"):
        end_match = re.search(r'^---\s*$', content[3:], re.MULTILINE)
        if end_match:
            content = content[3 + end_match.end():].lstrip()

    return frontmatter + content


def process_file(filepath: Path, dry_run: bool = False) -> dict | None:
    """Process a single file and rename it."""
    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception as e:
        print(f"  Error reading {filepath.name}: {e}")
        return None

    session_id = extract_session_id(content)
    if not session_id:
        print(f"  Skipping {filepath.name}: No session ID found")
        return None

    start_date = extract_start_date(content)
    end_date = extract_latest_date(content)

    if not start_date:
        print(f"  Skipping {filepath.name}: No start date found")
        return None

    if not end_date or end_date < start_date:
        end_date = start_date

    project_name = extract_project_name(content)
    description = generate_description(content, project_name, filepath.name)

    # Create title from description
    title = description.replace('-', ' ').title()

    # Check if subagent
    is_subagent = is_agent_session(content, filepath.name)

    # Create frontmatter
    frontmatter = create_frontmatter(session_id, start_date, end_date, title, project_name, is_subagent)

    # Create new filename: MM-DD-YYYY--MM-DD-YYYY-description.md
    new_name = f"{start_date.strftime('%m-%d-%Y')}--{end_date.strftime('%m-%d-%Y')}-{description}.md"
    new_path = filepath.parent / new_name

    # Handle filename collisions
    counter = 1
    while new_path.exists() and new_path != filepath:
        new_name = f"{start_date.strftime('%m-%d-%Y')}--{end_date.strftime('%m-%d-%Y')}-{description}-{counter}.md"
        new_path = filepath.parent / new_name
        counter += 1

    result = {
        "old_name": filepath.name,
        "new_name": new_name,
        "session_id": session_id,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "description": description,
    }

    if dry_run:
        print(f"  Would rename: {filepath.name}")
        print(f"           to: {new_name}")
        return result

    # Add frontmatter and write
    new_content = add_frontmatter_to_content(content, frontmatter)

    # Write to new path first (in case of different name)
    new_path.write_text(new_content, encoding="utf-8")

    # Remove old file if different path
    if new_path != filepath:
        filepath.unlink()

    print(f"  Renamed: {filepath.name}")
    print(f"       to: {new_name}")

    return result


def main():
    if len(sys.argv) < 2:
        print("Usage: rename-extracts.py <directory> [--dry-run]")
        print("  --dry-run: Show what would be renamed without making changes")
        sys.exit(1)

    backup_dir = Path(sys.argv[1])
    dry_run = "--dry-run" in sys.argv

    if not backup_dir.exists():
        print(f"Error: Directory {backup_dir} does not exist")
        sys.exit(1)

    print(f"Processing files in: {backup_dir}")
    if dry_run:
        print("DRY RUN - no changes will be made")
    print()

    files = list(backup_dir.glob("*.md"))
    print(f"Found {len(files)} markdown files")
    print()

    results = []
    for f in sorted(files):
        result = process_file(f, dry_run)
        if result:
            results.append(result)
        print()

    print(f"=== Summary ===")
    print(f"  Processed: {len(results)} files")
    if dry_run:
        print("  (dry run - no changes made)")


if __name__ == "__main__":
    main()
