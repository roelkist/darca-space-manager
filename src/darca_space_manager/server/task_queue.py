from dataclasses import dataclass
from enum import Enum
from queue import PriorityQueue
from threading import Lock
from typing import Callable, Optional, Dict
import time
import uuid


class TaskPriority(int, Enum):
    REALTIME = 1
    NORMAL = 5
    LOW = 10


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


@dataclass(order=True)
class ScheduledTask:
    priority: int
    timestamp: float
    task_id: str
    action: Callable
    description: str
    status: TaskStatus = TaskStatus.PENDING
    error: Optional[str] = None

    def run(self):
        self.status = TaskStatus.RUNNING
        try:
            self.action()
            self.status = TaskStatus.SUCCESS
        except Exception as e:
            self.status = TaskStatus.FAILED
            self.error = str(e)


class TaskQueue:
    _instance = None
    _lock = Lock()

    def __init__(self):
        self.queue = PriorityQueue()
        self.task_registry: Dict[str, ScheduledTask] = {}

    @classmethod
    def instance(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = TaskQueue()
            return cls._instance

    def enqueue(
        self,
        action: Callable,
        priority: TaskPriority = TaskPriority.NORMAL,
        delay_seconds: int = 0,
        description: str = ""
    ) -> str:
        task_id = str(uuid.uuid4())
        scheduled_time = time.time() + delay_seconds
        task = ScheduledTask(
            priority=priority,
            timestamp=scheduled_time,
            task_id=task_id,
            action=action,
            description=description
        )
        self.task_registry[task_id] = task
        self.queue.put(task)
        return task_id

    def dequeue_ready(self) -> Optional[ScheduledTask]:
        if not self.queue.empty():
            next_task = self.queue.queue[0]
            if next_task.timestamp <= time.time():
                return self.queue.get()
        return None

    def get_task_info(self, task_id: str) -> Optional[ScheduledTask]:
        return self.task_registry.get(task_id)

    def list_tasks(self) -> list[ScheduledTask]:
        return list(self.task_registry.values())
