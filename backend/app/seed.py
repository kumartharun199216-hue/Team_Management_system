from datetime import datetime, timedelta, timezone
from backend.app.database import SessionLocal
from backend.app.core.security import hash_password
from backend.app.models import (
    User, UserRole, Project, ProjectStatus, Task, TaskStatus, TaskPriority,
    TaskComment, ActivityLog
)

def seed_db():
    db = SessionLocal()
    try:
        if db.query(User).first():
            return

        now = datetime.now(timezone.utc)

        admin_user = User(
            email="admin@example.com",
            full_name="Alice Admin",
            hashed_password=hash_password("admin123"),
            role=UserRole.ADMIN,
            is_active=True
        )
        pm_user = User(
            email="pm@example.com",
            full_name="Bob Manager",
            hashed_password=hash_password("manager123"),
            role=UserRole.PROJECT_MANAGER,
            is_active=True
        )
        dev_user1 = User(
            email="dev1@example.com",
            full_name="Charlie Developer",
            hashed_password=hash_password("dev123"),
            role=UserRole.TEAM_MEMBER,
            is_active=True
        )
        dev_user2 = User(
            email="dev2@example.com",
            full_name="Diana Designer",
            hashed_password=hash_password("dev123"),
            role=UserRole.TEAM_MEMBER,
            is_active=True
        )

        db.add_all([admin_user, pm_user, dev_user1, dev_user2])
        db.commit()
        db.refresh(admin_user)
        db.refresh(pm_user)
        db.refresh(dev_user1)
        db.refresh(dev_user2)

        p1 = Project(
            name="Cloud Migration & DevOps Automation",
            description="Migrate internal monolith services to cloud infrastructure with CI/CD automation and monitoring.",
            status=ProjectStatus.IN_PROGRESS,
            start_date=now - timedelta(days=15),
            end_date=now + timedelta(days=45),
            owner_id=pm_user.id
        )
        p1.members = [pm_user, dev_user1, dev_user2]

        p2 = Project(
            name="Customer Mobile Portal v2",
            description="Re-engineer the iOS and Android applications to support real-time telemetry and biometrics.",
            status=ProjectStatus.PLANNING,
            start_date=now + timedelta(days=5),
            end_date=now + timedelta(days=90),
            owner_id=admin_user.id
        )
        p2.members = [admin_user, pm_user, dev_user1]

        db.add_all([p1, p2])
        db.commit()
        db.refresh(p1)
        db.refresh(p2)

        t1 = Task(
            title="Setup Terraform Infrastructure",
            description="Provision AWS VPC, subnets, RDS PostgreSQL instance, and IAM security roles.",
            status=TaskStatus.COMPLETED,
            priority=TaskPriority.CRITICAL,
            deadline=now - timedelta(days=2),
            project_id=p1.id,
            creator_id=pm_user.id,
            assignee_id=dev_user1.id
        )

        t2 = Task(
            title="Configure GitHub Actions CI/CD Pipeline",
            description="Build automated test runners and deployment pipeline for staging and production environments.",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.HIGH,
            deadline=now + timedelta(days=5),
            project_id=p1.id,
            creator_id=pm_user.id,
            assignee_id=dev_user1.id
        )

        t3 = Task(
            title="Design Application Dashboard Mockups",
            description="Create Figma high-fidelity wireframes and prototype responsive interactions.",
            status=TaskStatus.REVIEW,
            priority=TaskPriority.MEDIUM,
            deadline=now + timedelta(days=8),
            project_id=p1.id,
            creator_id=pm_user.id,
            assignee_id=dev_user2.id
        )

        t4 = Task(
            title="Security Audit & Compliance Review",
            description="Review API token life cycle, role permissions, and sensitive configuration handling.",
            status=TaskStatus.TODO,
            priority=TaskPriority.HIGH,
            deadline=now + timedelta(days=20),
            project_id=p1.id,
            creator_id=admin_user.id,
            assignee_id=dev_user2.id
        )

        t5 = Task(
            title="Mobile Architecture Specification",
            description="Define offline-first sync protocols and GraphQL query structures.",
            status=TaskStatus.TODO,
            priority=TaskPriority.LOW,
            deadline=now + timedelta(days=30),
            project_id=p2.id,
            creator_id=admin_user.id,
            assignee_id=dev_user1.id
        )

        db.add_all([t1, t2, t3, t4, t5])
        db.commit()
        db.refresh(t1)
        db.refresh(t2)

        c1 = TaskComment(
            task_id=t1.id,
            user_id=dev_user1.id,
            content="Terraform configs verified and applied cleanly. State stored in remote S3 bucket."
        )
        c2 = TaskComment(
            task_id=t1.id,
            user_id=pm_user.id,
            content="Great job Charlie! Approved."
        )

        db.add_all([c1, c2])

        l1 = ActivityLog(
            user_id=admin_user.id,
            project_id=p1.id,
            action="Created Project",
            details=f"Project '{p1.name}' was created."
        )
        l2 = ActivityLog(
            user_id=pm_user.id,
            project_id=p1.id,
            task_id=t1.id,
            action="Completed Task",
            details=f"Task '{t1.title}' marked as Completed."
        )

        db.add_all([l1, l2])
        db.commit()

    finally:
        db.close()

if __name__ == "__main__":
    seed_db()
