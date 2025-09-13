"""Version information utilities for Easy Lessons Bot."""

import subprocess
import sys
from pathlib import Path

try:
    import importlib.metadata
    __version__ = importlib.metadata.version("easy-lessons-bot")
except importlib.metadata.PackageNotFoundError:
    __version__ = "unknown"


def get_git_commit_hash() -> str | None:
    """Get the current git commit hash."""
    try:
        # Get the project root directory
        project_root = Path(__file__).parent.parent

        # Run git command to get commit hash
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True,
            timeout=5
        )
        return result.stdout.strip()[:8]  # Return first 8 characters
    except (
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        FileNotFoundError,
    ):
        return None


def get_git_branch() -> str | None:
    """Get the current git branch name."""
    try:
        # Get the project root directory
        project_root = Path(__file__).parent.parent

        # Run git command to get branch name
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True,
            timeout=5
        )
        return result.stdout.strip()
    except (
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        FileNotFoundError,
    ):
        return None


def get_version_info() -> dict:
    """Get comprehensive version information."""
    return {
        "version": __version__,
        "git_commit": get_git_commit_hash(),
        "git_branch": get_git_branch(),
        "python_version": (
            f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        )
    }


def format_version_info() -> str:
    """Format version information for logging."""
    info = get_version_info()
    parts = [f"version={info['version']}"]

    if info["git_commit"]:
        parts.append(f"commit={info['git_commit']}")

    if info["git_branch"]:
        parts.append(f"branch={info['git_branch']}")

    parts.append(f"python={info['python_version']}")

    return ", ".join(parts)
