import os


def get_base_dir():
    """Get the DARCA_SPACE_BASE directory (from env or default)."""
    return os.getenv(
        "DARCA_SPACE_BASE", os.path.expanduser("~/.local/share/darca_space")
    )


def get_directories():
    """Return the configured subdirectories."""
    base = get_base_dir()
    return {
        "SPACE_DIR": os.path.join(base, "spaces"),
        "METADATA_DIR": os.path.join(base, "metadata"),
        "LOG_DIR": os.path.join(base, "logs"),
    }


def ensure_directories_exist():
    """Ensure necessary directories exist."""
    for path in get_directories().values():
        os.makedirs(path, exist_ok=True)
