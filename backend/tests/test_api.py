import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.database import Base, get_db
from backend.app.main import app
from backend.app.core.security import hash_password
from backend.app.models.all_models import User, UserRole, Project, ProjectStatus, Task, TaskStatus, TaskPriority

TEST_DB_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    admin = User(
        email="test_admin@example.com",
        full_name="Admin Test",
        hashed_password=hash_password("password123"),
        role=UserRole.ADMIN,
        is_active=True
    )
    pm = User(
        email="test_pm@example.com",
        full_name="PM Test",
        hashed_password=hash_password("password123"),
        role=UserRole.PROJECT_MANAGER,
        is_active=True
    )
    member = User(
        email="test_member@example.com",
        full_name="Member Test",
        hashed_password=hash_password("password123"),
        role=UserRole.TEAM_MEMBER,
        is_active=True
    )
    db.add_all([admin, pm, member])
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    return TestClient(app)

def get_auth_token(client, email, password="password123"):
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()["access_token"]

def test_auth_login_success(client):
    res = client.post("/api/v1/auth/login", json={"email": "test_admin@example.com", "password": "password123"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["email"] == "test_admin@example.com"

def test_auth_login_invalid(client):
    res = client.post("/api/v1/auth/login", json={"email": "test_admin@example.com", "password": "wrong"})
    assert res.status_code == 401

def test_user_registration(client):
    res = client.post("/api/v1/auth/register", json={
        "email": "newuser@example.com",
        "full_name": "New Person",
        "password": "secretpassword",
        "role": "Team Member"
    })
    assert res.status_code == 201
    assert res.json()["email"] == "newuser@example.com"

def test_get_current_user(client):
    token = get_auth_token(client, "test_admin@example.com")
    res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["email"] == "test_admin@example.com"

def test_projects_crud_and_stats(client):
    pm_token = get_auth_token(client, "test_pm@example.com")
    headers = {"Authorization": f"Bearer {pm_token}"}

    res = client.post("/api/v1/projects", json={
        "name": "E-Commerce Microservices",
        "description": "Migration to event-driven microservices",
        "status": "In Progress"
    }, headers=headers)
    assert res.status_code == 201
    project_id = res.json()["id"]

    res = client.get("/api/v1/projects", headers=headers)
    assert res.status_code == 200
    assert any(p["id"] == project_id for p in res.json())

    res_task1 = client.post("/api/v1/tasks", json={
        "title": "Setup Kafka cluster",
        "description": "Kafka deployment on k8s",
        "status": "Completed",
        "priority": "High",
        "project_id": project_id
    }, headers=headers)
    assert res_task1.status_code == 201
    task1_id = res_task1.json()["id"]

    res_task2 = client.post("/api/v1/tasks", json={
        "title": "Implement Payment Consumer",
        "description": "Consumer service for Stripe events",
        "status": "In Progress",
        "priority": "Critical",
        "project_id": project_id
    }, headers=headers)
    assert res_task2.status_code == 201

    res_stats = client.get(f"/api/v1/projects/{project_id}/stats", headers=headers)
    assert res_stats.status_code == 200
    stats = res_stats.json()
    assert stats["total_tasks"] == 2
    assert stats["completed_tasks"] == 1
    assert stats["in_progress_tasks"] == 1
    assert stats["progress_percentage"] == 50.0

    res_comment = client.post(f"/api/v1/tasks/{task1_id}/comments", json={
        "content": "Kafka cluster successfully benchmarked."
    }, headers=headers)
    assert res_comment.status_code == 201
    assert res_comment.json()["content"] == "Kafka cluster successfully benchmarked."

    res_comments = client.get(f"/api/v1/tasks/{task1_id}/comments", headers=headers)
    assert res_comments.status_code == 200
    assert len(res_comments.json()) >= 1

def test_rbac_restrictions(client):
    member_token = get_auth_token(client, "test_member@example.com")
    member_headers = {"Authorization": f"Bearer {member_token}"}

    res = client.post("/api/v1/projects", json={
        "name": "Unauthorized Project",
        "description": "Should fail",
        "status": "Planning"
    }, headers=member_headers)
    assert res.status_code == 403

    res = client.post("/api/v1/users", json={
        "email": "hacker@example.com",
        "full_name": "Hacker",
        "password": "password123",
        "role": "Admin"
    }, headers=member_headers)
    assert res.status_code == 403

def test_dashboard_stats(client):
    admin_token = get_auth_token(client, "test_admin@example.com")
    res = client.get("/api/v1/dashboard/stats", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    data = res.json()
    assert "total_projects" in data
    assert "total_tasks" in data
    assert "recent_activities" in data
    assert len(data["recent_activities"]) > 0
