#!/usr/bin/env python3
"""
Update existing conversation extracts with new messages.

This script:
1. Extracts conversations to a temp directory
2. Matches session IDs by reading them from INSIDE the file content
3. Updates existing files while preserving user notes sections
4. Supports ANY filename - no naming convention required

The session ID is read from the file header:
    # Claude Conversation Log

    Session ID: ef08bb5d-596c-4ea9-b88c-a0c5e2415da0

User notes are preserved if placed in a fenced section:
    <!-- USER NOTES - This section will be preserved on update -->
    Your notes here...
    <!-- END USER NOTES -->
"""

import os
import re
import sys
import shutil
import tempfile
import subprocess
from pathlib import Path

# Marker for user notes section that should be preserved
USER_NOTES_START = "<!-- USER NOTES - This section will be preserved on update -->"
USER_NOTES_END = "<!-- END USER NOTES -->"


def extract_session_id_from_content(content: str) -> str | None:
    """Extract the session ID from file content.

    Looks for: Session ID: <uuid or hex string>
    """
    match = re.search(r'Session ID:\s*([a-f0-9-]+)', content, re.IGNORECASE)
    if match:
        # Return just the first part before any hyphens for consistency
        # Full UUID: ef08bb5d-596c-4ea9-b88c-a0c5e2415da0
        # We use the first segment for matching: ef08bb5d
        session_id = match.group(1)
        return session_id.split('-')[0] if '-' in session_id else session_id
    return None


def extract_session_id_from_filename(filename: str) -> str | None:
    """Fallback: Extract session ID from filename if not in content."""
    match = re.search(r'claude-conversation-\d{4}-\d{2}-\d{2}-([a-f0-9]{8,})', filename)
    if match:
        return match.group(1)
    # Also try agent format: agent-a1b2c3d4
    match = re.search(r'agent-([a-f0-9]{2,})', filename)
    if match:
        return match.group(1)
    return None


def extract_user_notes(content: str) -> str | None:
    """Extract user notes section if present."""
    start_idx = content.find(USER_NOTES_START)
    end_idx = content.find(USER_NOTES_END)

    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        return content[start_idx:end_idx + len(USER_NOTES_END)]
    return None


def merge_with_user_notes(new_content: str, user_notes: str | None) -> str:
    """Merge new content with preserved user notes."""
    if not user_notes:
        return new_content

    # Add user notes at the end of the file
    return new_content.rstrip() + "\n\n" + user_notes + "\n"


def get_existing_files(backup_dir: Path) -> dict[str, tuple[Path, str | None]]:
    """Get a mapping of session_id -> (filepath, user_notes) for existing extracts.

    Reads session ID from inside each file, not from filename.
    Also extracts any user notes to preserve.
    """
    existing = {}

    for f in backup_dir.glob("*.md"):
        try:
            content = f.read_text(encoding="utf-8")
        except Exception as e:
            print(f"  Warning: Could not read {f.name}: {e}")
            continue

        # Try to get session ID from content first, then filename
        session_id = extract_session_id_from_content(content)
        if not session_id:
            session_id = extract_session_id_from_filename(f.name)

        if session_id:
            user_notes = extract_user_notes(content)
            existing[session_id] = (f, user_notes)

    return existing


def run_extraction(output_dir: Path, session_numbers: str | None = None) -> bool:
    """Run claude-extract to the specified directory."""
    cmd = ["claude-extract", "--output", str(output_dir), "--detailed"]
    if session_numbers:
        cmd.extend(["--extract", session_numbers])
    else:
        cmd.append("--all")

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    result = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Extraction failed: {result.stderr}", file=sys.stderr)
        return False
    print(result.stdout)
    return True


def update_extracts(backup_dir: Path, session_numbers: str | None = None) -> dict:
    """Main function to update extracts."""
    backup_dir = Path(backup_dir)

    # Get existing files (reads session ID from content, preserves user notes)
    existing = get_existing_files(backup_dir)
    print(f"Found {len(existing)} existing extracts in {backup_dir}")

    # Extract to temp directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        print(f"Extracting to temp directory...")

        if not run_extraction(temp_path, session_numbers):
            return {"error": "Extraction failed"}

        # Get new extracts
        new_files = list(temp_path.glob("claude-conversation-*.md"))
        print(f"Extracted {len(new_files)} files")

        stats = {"updated": 0, "new": 0, "unchanged": 0, "skipped": 0, "notes_preserved": 0}

        for new_file in new_files:
            new_content = new_file.read_text(encoding="utf-8")

            # Get session ID from the new file's content
            session_id = extract_session_id_from_content(new_content)
            if not session_id:
                session_id = extract_session_id_from_filename(new_file.name)

            if not session_id:
                print(f"  Skipping {new_file.name} (no session ID found)")
                stats["skipped"] += 1
                continue

            if session_id in existing:
                # Update existing file
                existing_file, user_notes = existing[session_id]
                old_content = existing_file.read_text(encoding="utf-8")

                # Merge new content with preserved user notes
                final_content = merge_with_user_notes(new_content, user_notes)

                # Compare without user notes section for change detection
                old_without_notes = old_content
                if user_notes and user_notes in old_content:
                    old_without_notes = old_content.replace(user_notes, "").rstrip()

                if new_content.rstrip() != old_without_notes.rstrip():
                    existing_file.write_text(final_content, encoding="utf-8")
                    note_msg = " (notes preserved)" if user_notes else ""
                    print(f"  Updated: {existing_file.name}{note_msg}")
                    stats["updated"] += 1
                    if user_notes:
                        stats["notes_preserved"] += 1
                else:
                    print(f"  Unchanged: {existing_file.name}")
                    stats["unchanged"] += 1
            else:
                # New file - copy to backup dir
                dest = backup_dir / new_file.name
                shutil.copy2(new_file, dest)
                print(f"  New: {new_file.name}")
                stats["new"] += 1

        return stats


def main():
    if len(sys.argv) < 2:
        print("Usage: update-extracts.py <backup_directory> [session_numbers]")
        print("  session_numbers: comma-separated list like '1,2,3' or omit for all")
        sys.exit(1)

    backup_dir = Path(sys.argv[1])
    session_numbers = sys.argv[2] if len(sys.argv) > 2 else None

    if not backup_dir.exists():
        print(f"Error: Directory {backup_dir} does not exist")
        sys.exit(1)

    stats = update_extracts(backup_dir, session_numbers)

    print("\n=== Summary ===")
    for key, value in stats.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
