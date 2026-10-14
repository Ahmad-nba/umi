from __future__ import annotations

from fastapi import FastAPI

from app.api.feedback import router as feedback_router
from app.api.health import router as health_router
from app.api.issues import router as issues_router
from app.api.notifications import router as notifications_router
from app.api.qa import router as qa_router
from app.api.conversations import router as conversations_router
from app.api.workflow import router as workflow_router
import app.core.database as database
from app.core.config import get_settings
from app.seed import seed_handlers
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Feedback Watch Tower for UMI")
app.include_router(health_router)
app.include_router(feedback_router)
app.include_router(issues_router)
app.include_router(workflow_router)
app.include_router(notifications_router)
app.include_router(qa_router)
app.include_router(conversations_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event() -> None:
    if get_settings().app_env.lower() == "production":
        return
    database.init_db()
    db = database.SessionLocal()
    try:
        seed_handlers(db)
    finally:
        db.close()
