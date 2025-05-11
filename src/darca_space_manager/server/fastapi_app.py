from fastapi import FastAPI
from darca_space_manager.server.router_space import router as space_router
from darca_space_manager.server.router_tasks import router as task_router
from darca_space_manager.server.scheduler import TaskScheduler

app = FastAPI(
    title="Darca Space Manager API",
    version="1.0.0",
    description="A RESTful service for managing logical project spaces, files, and background tasks."
)

# Register routers
app.include_router(space_router, prefix="/spaces", tags=["Spaces"])
app.include_router(task_router, prefix="/tasks", tags=["Tasks"])

# Start background task scheduler
scheduler = TaskScheduler()
scheduler.start()
