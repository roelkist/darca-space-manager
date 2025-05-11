from fastapi import APIRouter, HTTPException
from darca_space_manager.api.space_service import SpaceService
from darca_space_manager.models.space_uri import SpaceURI
from darca_space_manager.api.space_file_manager import SpaceFileManagerException
from darca_space_manager.api.space_executor import SpaceExecutorException
from darca_space_manager.api.space_manager import SpaceManagerException
from darca_space_manager.server.task_queue import TaskQueue, TaskPriority
from darca_space_manager.server.models import CreateSpaceRequest, SpaceResponse

router = APIRouter()
service = SpaceService()
queue = TaskQueue.instance()


# ---------- Core Space Operations ----------

@router.post("/", response_model=SpaceResponse)
def create_space(request: CreateSpaceRequest):
    try:
        space = service.create_space(request.name, label=request.label, parent=request.parent)
        return SpaceResponse.from_space(space)
    except SpaceManagerException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{name}", response_model=SpaceResponse)
def get_space(name: str):
    space = service.get_space(name)
    if not space:
        raise HTTPException(status_code=404, detail="Space not found.")
    return SpaceResponse.from_space(space)


@router.delete("/{name}")
def delete_space(name: str, force: bool = False):
    try:
        service.delete_space(name, force=force)
        return {"message": f"Space '{name}' deleted successfully."}
    except SpaceManagerException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{old_name}/rename/{new_name}", response_model=SpaceResponse)
def rename_space(old_name: str, new_name: str):
    try:
        space = service.rename_space(old_name, new_name)
        return SpaceResponse.from_space(space)
    except SpaceManagerException as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------- Queued Deletion ----------

@router.post("/{name}/delete-queued")
def delete_space_queued(name: str, force: bool = True):
    def action():
        service.delete_space(name, force=force)

    task_id = queue.enqueue(
        action=action,
        priority=TaskPriority.LOW,
        description=f"Queued delete for space '{name}'"
    )
    return {"message": "Delete task enqueued", "task_id": task_id}


# ---------- File Operations ----------

@router.post("/{space_name}/files")
def write_file(space_name: str, relative_path: str, content: dict):
    uri = SpaceURI(space=space_name, path=relative_path)
    try:
        service.write_file(uri, content)
        return {"message": f"File '{relative_path}' written in space '{space_name}'."}
    except SpaceFileManagerException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{space_name}/files")
def list_files(space_name: str):
    try:
        return service.list_files(space_name)
    except SpaceFileManagerException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{space_name}/files/{relative_path}")
def read_file(space_name: str, relative_path: str, load: bool = False):
    uri = SpaceURI(space=space_name, path=relative_path)
    try:
        return service.read_file(uri, load=load)
    except SpaceFileManagerException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{space_name}/files/{relative_path}")
def delete_file(space_name: str, relative_path: str):
    uri = SpaceURI(space=space_name, path=relative_path)
    try:
        service.delete_file(uri)
        return {"message": f"File '{relative_path}' deleted from space '{space_name}'."}
    except SpaceFileManagerException as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------- Command Execution ----------

@router.post("/{space_name}/run")
def run_command(space_name: str, command: list[str]):
    try:
        uri = f"space://{space_name}/"
        result = service.run(uri, command, capture_output=True)
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except SpaceExecutorException as e:
        raise HTTPException(status_code=500, detail=str(e))
