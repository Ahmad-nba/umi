from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.enums import Department
from app.core.exceptions import WorkflowError
from app.core.logging import logger
from app.models.handler import Handler


class RoutingService:
    DEPARTMENT_HANDLER_MAP = {
        Department.ACADEMIC_AFFAIRS.value: "Academic Affairs",
        Department.IT.value: "IT",
        Department.FACILITIES.value: "Facilities",
    }

    def __init__(self, db: Session):
        self.db = db

    def route_issue(self, department: Department | str) -> Handler:
        dept_name = (
            department.value if isinstance(department, Department) else str(department)
        )
        handler = (
            self.db.query(Handler)
            .filter(Handler.department == dept_name, Handler.active.is_(True))
            .first()
        )
        if handler is not None:
            logger.info(
                "issue_routed",
                extra={"department": dept_name, "handler_id": handler.id},
            )
            return handler

        fallback = (
            self.db.query(Handler)
            .filter(
                Handler.department == Department.ADMINISTRATION.value,
                Handler.active.is_(True),
            )
            .first()
        )
        if fallback is not None:
            logger.warning(
                "route_fallback_used",
                extra={
                    "requested_department": dept_name,
                    "fallback_department": fallback.department,
                },
            )
            return fallback

        raise WorkflowError(
            "No active handler configured for the requested department",
            code="handler_not_found",
        )
