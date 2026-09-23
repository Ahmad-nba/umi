from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.enums import Department
from app.models.handler import Handler
from app.models.reporter import Reporter
from app.models.feedback import Feedback


def seed_handlers(db: Session) -> None:
    if db.query(Handler).count() == 0:
        db.add_all(
            [
                Handler(
                    name="Academic Affairs Desk",
                    department=Department.ACADEMIC_AFFAIRS.value,
                    contact="aa@umi.ac.ug",
                    active=True,
                ),
                Handler(
                    name="IT Support",
                    department=Department.IT.value,
                    contact="it@umi.ac.ug",
                    active=True,
                ),
                Handler(
                    name="Facilities Office",
                    department=Department.FACILITIES.value,
                    contact="facilities@umi.ac.ug",
                    active=True,
                ),
                Handler(
                    name="General Administration",
                    department=Department.ADMINISTRATION.value,
                    contact="admin@umi.ac.ug",
                    active=True,
                ),
            ]
        )
    db.commit()


def seed_demo_data(db: Session) -> None:
    seed_handlers(db)

    if db.query(Reporter).count() == 0:
        reporter = Reporter(name="Student Reporter", contact="student@umi.ac.ug")
        db.add(reporter)
        db.flush()

        db.add(
            Feedback(
                reporter_id=reporter.id,
                channel="form",
                content="My Engineering Mathematics marks are missing from the student portal.",
                context="Student portal issue",
            )
        )

    db.commit()
