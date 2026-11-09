# Entity Relationship (ER) Diagram

The following diagram illustrates the relational database model of the **Advanced Project & Team Management System** built with SQLAlchemy ORM and SQLite/PostgreSQL.

```mermaid
erDiagram
    USERS ||--o{ PROJECTS : "owns"
    USERS ||--o{ PROJECT_MEMBERS : "participates_in"
    PROJECTS ||--o{ PROJECT_MEMBERS : "has_members"
    USERS ||--o{ TASKS : "creates"
    USERS ||--o{ TASKS : "assigned_to"
    PROJECTS ||--o{ TASKS : "contains"
    TASKS ||--o{ TASK_COMMENTS : "has"
    USERS ||--o{ TASK_COMMENTS : "writes"
    USERS ||--o{ ACTIVITY_LOGS : "triggers"
    PROJECTS ||--o{ ACTIVITY_LOGS : "logs"
    TASKS ||--o{ ACTIVITY_LOGS : "logs"

    USERS {
        int id PK
        string email UK
        string full_name
        string hashed_password
        enum role "Admin, Project Manager, Team Member"
        boolean is_active
        datetime created_at
        datetime updated_at
    }

    PROJECTS {
        int id PK
        string name
        text description
        enum status "Planning, In Progress, On Hold, Completed, Cancelled"
        datetime start_date
        datetime end_date
        int owner_id FK
        datetime created_at
        datetime updated_at
    }

    PROJECT_MEMBERS {
        int project_id PK, FK
        int user_id PK, FK
        datetime joined_at
    }

    TASKS {
        int id PK
        string title
        text description
        enum status "To Do, In Progress, Review, Completed"
        enum priority "Low, Medium, High, Critical"
        datetime deadline
        int project_id FK
        int creator_id FK
        int assignee_id FK
        datetime created_at
        datetime updated_at
    }

    TASK_COMMENTS {
        int id PK
        int task_id FK
        int user_id FK
        text content
        datetime created_at
    }

    ACTIVITY_LOGS {
        int id PK
        int user_id FK
        int project_id FK
        int task_id FK
        string action
        text details
        datetime timestamp
    }
```
