Ethara Task Manager
===================

Project Overview
----------------
Ethara Task Manager is a minimal full-stack task management application that demonstrates role-based access control, project and task management, and a simple dashboard. The backend is implemented with FastAPI and SQLAlchemy; the user interface is provided as a Streamlit app. The project is intended as a submission for a campus placement full-stack assessment and includes REST APIs, authentication (JWT), and deployment guidance for Railway.

Key Features
------------
- Authentication: Signup and Login with JWT tokens.
- Role-based access control: `Admin` and `Member` roles.
- Project management: create and list projects (Admin creates; Members see projects where they have tasks).
- Task management: create tasks, assign to users, update status (`Pending`, `In Progress`, `Completed`).
- Dashboard: Streamlit UI for authentication, project creation, task dispatch and status updates.
 - Project scheduling: each project now includes `start_date` and `end_date` fields visible in the UI and used for basic duration/overdue checks.

Repository Layout
-----------------
- `main.py` — FastAPI application and API endpoints.
- `auth.py` — authentication helpers, JWT creation and role enforcement.
- `database.py` — SQLAlchemy engine, session and Base.
- `models.py` — SQLAlchemy models: `User`, `Project`, `Task`.
- `schemas.py` — Pydantic schemas for API request/response models.
- `app.py` — Streamlit UI that interacts with the API.
- `requirements.txt` — Python dependencies.

Quick start (Windows)
---------------------
1. Create and activate a virtual environment, then install dependencies:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

2. Start the FastAPI backend (bind to localhost or `0.0.0.0` for hosting):

```powershell
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

3. In a separate terminal, run the Streamlit UI (it points to `http://127.0.0.1:8000` by default):

```powershell
streamlit run app.py
```

Environment variables
---------------------
- `SECRET_KEY` — recommended to set a strong JWT secret in production. The code falls back to a default value if not set.
- `DATABASE_URL` — SQLAlchemy connection string. Defaults to a local SQLite file `sqlite:///./taskmanager.db`.
- `PORT` — hosting platforms such as Railway provide this for the server process; use when deploying.

API Reference (summary)
-----------------------
- `POST /auth/signup` — create a new user. Payload: `{ "username": "...", "password": "...", "role": "Member|Admin" }`.
- `POST /auth/login` — obtain access token. Form fields: `username`, `password`. Returns `{ "access_token": "...", "token_type": "bearer" }`.
- `POST /projects/` — create a new project (Admin only). Payload: `{ "name": "...", "description": "..." }`.
 - `POST /projects/` — create a new project (Admin only). Payload: `{ "name": "...", "description": "...", "start_date": "YYYY-MM-DDTHH:MM:SS", "end_date": "YYYY-MM-DDTHH:MM:SS" }`.
- `GET /projects/` — list projects: Admins see their projects; Members see projects where they have tasks.
- `POST /projects/{project_id}/tasks/` — create a task under a project (Admin only). Payload: `{ "title": "...", "description": "...", "assigned_to": <user_id>, "due_date": "ISO datetime" }`.
- `PATCH /tasks/{task_id}/status?status=Completed` — update a task's status (Admin can update any; Member only their tasks).

Data Models (high level)
------------------------
- `User`: `id`, `username`, `hashed_password`, `role` (`Admin` or `Member`).
- `Project`: `id`, `name`, `description`, `admin_id` (FK to `User`).
	- `Project` also contains `start_date` and `end_date` (ISO datetimes).
- `Task`: `id`, `title`, `description`, `status`, `due_date`, `project_id` (FK), `assigned_to` (FK to `User`).

Security & Notes
----------------
- JWT authentication is implemented in `auth.py`. Tokens are signed with `SECRET_KEY`.
- Passwords are hashed using `passlib`'s `pbkdf2_sha256`.
- The current implementation will create database tables automatically on application start. For production workflows use migration.
- If serving the Streamlit UI from a different origin than the API, enable CORS middleware or host the UI so it points to the same domain.


Demo Accounts
-------------
Use the following demo accounts for recording the demo or testing after seeding/creating them:

- Admin: `admin_ishan` / `password123`
- Member: `member_1` / `member1_123`


Further improvements
----------------------------------
- Add CORS middleware to the FastAPI app when the UI is hosted separately.
- Add Alembic for database migrations.
- Remove any hard-coded default `SECRET_KEY` and enforce secure secrets in production.
- Add unit/integration tests and a CI pipeline for automated checks.

License & Submission
--------------------
This repository is a demonstration for placement task. 
