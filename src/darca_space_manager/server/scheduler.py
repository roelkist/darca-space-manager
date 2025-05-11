import threading
import time
import logging

from darca_space_manager.server.task_queue import TaskQueue, ScheduledTask, TaskStatus

logger = logging.getLogger("task_scheduler")


class TaskScheduler:
    def __init__(self, poll_interval: float = 1.0):
        self._interval = poll_interval
        self._running = False
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._queue = TaskQueue.instance()

    def start(self):
        if not self._running:
            logger.info("🕓 Starting task scheduler...")
            self._running = True
            self._thread.start()

    def stop(self):
        self._running = False
        logger.info("🛑 Task scheduler stopped.")

    def _run_loop(self):
        while self._running:
            task: ScheduledTask = self._queue.dequeue_ready()
            if task:
                logger.info(f"🚀 Executing task {task.task_id}: {task.description}")
                try:
                    task.run()
                    logger.info(f"✅ Task {task.task_id} finished with status: {task.status}")
                    if task.error:
                        logger.error(f"❌ Task error: {task.error}")
                except Exception as e:
                    logger.exception(f"Unhandled error in task: {task.task_id}")
            else:
                time.sleep(self._interval)
