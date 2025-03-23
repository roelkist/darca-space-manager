import os

# Default max spaces limit
MAX_SPACES = 10

# Define the base directory following the Filesystem Hierarchy Standard (FHS)
DEFAULT_BASE_DIR = os.path.expanduser("~/.local/share/darca_space")

# Directory configurations (local storage)
DIRECTORIES = {
    "SPACE_DIR": os.path.join(DEFAULT_BASE_DIR, "spaces"),
    "METADATA_DIR": os.path.join(DEFAULT_BASE_DIR, "metadata"),
    "LOG_DIR": os.path.join(DEFAULT_BASE_DIR, "logs"),
}

# Ensure directories exist at module load
for path in DIRECTORIES.values():
    os.makedirs(path, exist_ok=True)
