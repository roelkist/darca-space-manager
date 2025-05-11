from pydantic import BaseModel
from typing import Optional
from darca_space_manager.models.space import Space
from darca_space_manager.server.task_queue import ScheduledTask, TaskStatus


# ---------- Space I/O Models ----------

class CreateSpaceRequest(BaseModel):
    name: str
    label: Optional[str] = None
    parent: Optional[str] = None


class SpaceResponse(BaseModel):
    name: str
    path: str
    label: Optional[str]
    parent: Optional[str]
    created_at: str
    last_modified_at: str

    @classmethod
    def from_space(cls, space: Space) -> "SpaceResponse":
        return cls(**space.model_dump())


# ---------- Task I/O Models ----------

class TaskResponse(BaseModel):
    task_id: str
    description: str
    status: TaskStatus
    error: Optional[str] = None

    @classmethod
    def from_task(cls, task: ScheduledTask) -> "TaskResponse":
        return cls(
            task_id=task.task_id,
            description=task.description,
            status=task.status,
            error=task.error,
        )
