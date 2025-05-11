from fastapi import APIRouter, HTTPException
from darca_space_manager.server.task_queue import TaskQueue
from darca_space_manager.server.models import TaskResponse

router = APIRouter()
queue = TaskQueue.instance()


@router.get("/", response_model=list[TaskResponse])
def list_tasks():
    """
    List all known tasks, regardless of status.
    """
    return [
        TaskResponse.from_task(task)
        for task in queue.list_tasks()
    ]


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: str):
    """
    Retrieve a single task's status and metadata.
    """
    task = queue.get_task_info(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")
    return TaskResponse.from_task(task)
