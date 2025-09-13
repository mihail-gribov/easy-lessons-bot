#!/usr/bin/env python3
"""Script to automatically bump version in pyproject.toml."""

import argparse
import re
import sys
from pathlib import Path
from typing import Tuple


def parse_version(version: str) -> Tuple[int, int, int]:
    """Parse version string into major, minor, patch components."""
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)$", version)
    if not match:
        raise ValueError(f"Invalid version format: {version}")
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def format_version(major: int, minor: int, patch: int) -> str:
    """Format version components into version string."""
    return f"{major}.{minor}.{patch}"


def bump_version(version: str, bump_type: str) -> str:
    """Bump version according to type."""
    major, minor, patch = parse_version(version)
    
    if bump_type == "major":
        return format_version(major + 1, 0, 0)
    elif bump_type == "minor":
        return format_version(major, minor + 1, 0)
    elif bump_type == "patch":
        return format_version(major, minor, patch + 1)
    else:
        raise ValueError(f"Invalid bump type: {bump_type}")


def update_pyproject_version(pyproject_path: Path, new_version: str) -> None:
    """Update version in pyproject.toml file."""
    content = pyproject_path.read_text()
    
    # Replace version line
    pattern = r'^version = ".*"$'
    replacement = f'version = "{new_version}"'
    
    new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    if new_content == content:
        raise ValueError("Version not found in pyproject.toml")
    
    pyproject_path.write_text(new_content)
    print(f"Updated version to {new_version} in pyproject.toml")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Bump version in pyproject.toml")
    parser.add_argument(
        "bump_type",
        choices=["major", "minor", "patch"],
        help="Type of version bump"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without making changes"
    )
    parser.add_argument(
        "--no-commit",
        action="store_true",
        help="Don't commit the version change (for use in git hooks)"
    )
    
    args = parser.parse_args()
    
    # Find pyproject.toml
    project_root = Path(__file__).parent.parent
    pyproject_path = project_root / "pyproject.toml"
    
    if not pyproject_path.exists():
        print("Error: pyproject.toml not found")
        sys.exit(1)
    
    # Read current version
    content = pyproject_path.read_text()
    version_match = re.search(r'^version = "([^"]+)"$', content, re.MULTILINE)
    
    if not version_match:
        print("Error: Version not found in pyproject.toml")
        sys.exit(1)
    
    current_version = version_match.group(1)
    new_version = bump_version(current_version, args.bump_type)
    
    print(f"Current version: {current_version}")
    print(f"New version: {new_version}")
    
    if args.dry_run:
        print("Dry run: No changes made")
        return
    
    # Update version
    try:
        update_pyproject_version(pyproject_path, new_version)
        print(f"Successfully bumped version to {new_version}")
    except Exception as e:
        print(f"Error updating version: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
