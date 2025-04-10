import os

# Use environment variable if set (e.g. in containers or tests)
DARCA_SPACE_BASE = os.getenv("DARCA_SPACE_BASE")

# Define the base directory
DEFAULT_BASE_DIR = (
    DARCA_SPACE_BASE
    if DARCA_SPACE_BASE
    else os.path.expanduser("~/.local/share/darca_space")
)

# Directory configurations (local storage)
DIRECTORIES = {
    "SPACE_DIR": os.path.join(DEFAULT_BASE_DIR, "spaces"),
    "METADATA_DIR": os.path.join(DEFAULT_BASE_DIR, "metadata"),
    "LOG_DIR": os.path.join(DEFAULT_BASE_DIR, "logs"),
}

# Ensure directories exist at module load
for path in DIRECTORIES.values():
    os.makedirs(path, exist_ok=True)
