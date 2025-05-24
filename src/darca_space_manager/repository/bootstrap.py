import os
from darca_space_manager.repository.yaml_repository_backend import YamlRepositoryBackend
from darca_space_manager.repository.repository_backend import RepositoryBackend

# Placeholder for future DB repository
# from darca_space_manager.core.space_admin.db_backend_repository import DatabaseSpaceBackendRepository


def get_backend_repository() -> RepositoryBackend:
    mode = os.getenv("DARCA_BACKEND_MODE", "yaml").lower()

    if mode == "database":
        raise NotImplementedError("Database backend repository not yet implemented.")
        # return DatabaseSpaceBackendRepository(
        #     db_url=os.getenv("DARCA_DB_URL"),
        #     user=os.getenv("DARCA_DB_USER"),
        #     password=os.getenv("DARCA_DB_PASSWORD"),
        # )

    profile_dir = os.getenv("DARCA_PROFILE_DIR", os.path.expanduser("~/.local/share/darca_space/profiles"))
    return YamlRepositoryBackend(profile_dir)
