# ApexPlan Pro - Advanced Project & Team Management System

A web-based application built with **Python FastAPI** and a modern, responsive HTML5/CSS/JavaScript dashboard where administrators and managers can track projects, assign tasks to team members, monitor progress percentages, and audit system activities with role-based access control (RBAC).

---

## 🌟 Key Features

### 1. Frontend Dashboard & Management
- **Dashboard Overview:** Real-time statistics including Total Projects, Total Tasks, Completed Tasks, In-Progress Tasks, Completion Percentage, Project Progress Bars, and Recent Activity Feed.
- **Project Management:** Full CRUD operations on projects, progress tracking calculated dynamically from task statuses, start/end date timeline tracking, and team member assignments.
- **Task Management:** Create, edit, and delete tasks with priority levels (`Low`, `Medium`, `High`, `Critical`), statuses (`To Do`, `In Progress`, `Review`, `Completed`), deadline tracking, search, multi-criteria filtering, and sorting.
- **Comments & Activity Stream:** Dedicated drawer on task selection allowing threaded comments and full history logging.
- **User & Team Management:** Admin portal to manage users, toggle activation status, and assign RBAC roles.
- **Role Switcher Demo Bar:** Fast switching between Admin, Project Manager, and Team Member roles for interactive review.

### 2. Backend REST APIs (FastAPI)
- **Authentication & RBAC:** JWT bearer authentication with bcrypt password hashing. Roles supported: `Admin`, `Project Manager`, and `Team Member`.
- **Relational Data Model:** Built with SQLAlchemy 2.0 ORM with relational mapping and Alembic migrations.
- **Audit Logging:** Automated logging of critical actions (project creation, member assignments, task status transitions, comments).
- **Interactive Documentation:** Automatic Swagger UI at `/docs` and ReDoc at `/redoc`.
- **Validation & Error Handling:** Pydantic schema validation, date consistency checks, and request performance logging.

---

## 🏗️ Architecture & Project Structure

```
├── backend/
│   ├── alembic/              # Alembic database migrations configuration & versions
│   ├── alembic.ini           # Alembic CLI config
│   ├── app/
│   │   ├── api/v1/           # REST API endpoints (auth, users, projects, tasks, dashboard)
│   │   ├── core/             # App settings, security (bcrypt & JWT), RBAC dependencies
│   │   ├── crud/             # Database access and audit logging helpers
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── schemas/          # Pydantic v2 validation models
│   │   ├── database.py       # Engine and session factory
│   │   ├── main.py           # FastAPI application entrypoint & static mounting
│   │   └── seed.py           # Database initial demo data seeder
│   └── tests/                # Pytest test suite
├── frontend/
│   ├── index.html            # Main responsive single-page dashboard
│   └── static/
│       ├── app.js            # Frontend application logic & API client
│       └── style.css         # Modern, responsive UI design
├── er_diagram.md             # Mermaid ER diagram of database models
├── postman_collection.json   # Ready-to-import Postman collection
├── pytest.ini                # Pytest configuration
├── requirements.txt          # Python dependencies
└── README.md                 # Project documentation
```

---

## 👥 Role-Based Access Control (RBAC) Matrix

| Feature / Action | Admin | Project Manager | Team Member |
|---|:---:|:---:|:---:|
| View Dashboard & Stats | ✅ | ✅ | ✅ |
| View Projects & Tasks | ✅ | ✅ | ✅ |
| Create Projects | ✅ | ✅ | ❌ |
| Edit / Delete Projects | ✅ | ✅ (Own projects) | ❌ |
| Assign Members to Projects | ✅ | ✅ (Own projects) | ❌ |
| Create / Update Tasks | ✅ | ✅ | ✅ |
| Delete Tasks | ✅ | ✅ | ✅ (Own created tasks) |
| Post Task Comments | ✅ | ✅ | ✅ |
| Manage Users & Roles | ✅ | ❌ | ❌ |
| Activate / Deactivate Users | ✅ | ❌ | ❌ |

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+
- SQLite (default) or PostgreSQL

### 2. Installation
```bash
# Clone the repository and navigate to root
git clone <repo-url>
cd <repo-folder>

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Database Migrations & Seeding
```bash
# Run Alembic migrations
cd backend
alembic upgrade head
cd ..

# (Optional) Seed demo users, projects, and tasks
python3 -m backend.app.seed
```

### 4. Running the Application
```bash
# Start FastAPI backend server
python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

- **Web Dashboard:** Open `http://localhost:8000/` in your browser.
- **Interactive API Docs (Swagger):** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

---

## 🔑 Demo Credentials

| Role | Email | Password |
|---|---|---|
| **Admin** | `admin@example.com` | `admin123` |
| **Project Manager** | `pm@example.com` | `manager123` |
| **Team Member 1** | `dev1@example.com` | `dev123` |
| **Team Member 2** | `dev2@example.com` | `dev123` |

---

## 🧪 Running Automated Tests
```bash
pytest -v
```

All 7 test suites verify:
- Authentication & JWT token issuing
- User registration and password encryption
- Role-based authorization guardrails
- Project and Task CRUD lifecycles
- Project progress percentage calculations
- Task comments and audit logging

---

## 📦 Submission Deliverables
- **GitHub Repository Code:** Full source code cleanly modularized.
- **Database Schema:** Documented in `er_diagram.md` (Mermaid format).
- **Postman Collection:** `postman_collection.json`.
- **Dependencies:** `requirements.txt`.
