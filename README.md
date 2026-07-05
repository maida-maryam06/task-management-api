# Task Management REST API (Flask)

A production-ready REST API for task management built with Flask, following
the application factory pattern. Features JWT authentication, full CRUD
for Projects and Tasks, input validation with Flask-Marshmallow, pagination,
task filters, and 15 passing integration tests. Built as the Flask task for
the Enischyo Interns Python Development internship program.

**Keywords:** flask rest api, jwt authentication, flask-sqlalchemy,
flask-marshmallow, task management api, python rest api, pythonanywhere
deployment, internship project.

## Tech stack

| Layer | Library |
|-------|---------|
| Framework | Flask 3.x (application factory pattern) |
| Database | SQLite (dev) via Flask-SQLAlchemy |
| Auth | JWT via Flask-JWT-Extended (access + refresh tokens) |
| Validation | Flask-Marshmallow + marshmallow-sqlalchemy |
| Password hashing | bcrypt |
| Testing | pytest + Flask test client |
| Deployment | PythonAnywhere free tier |

## Quick start

```bash
git clone https://github.com/maida-maryam06/task-management-api.git
cd task-management-api
pip install -r requirements.txt
python run.py
```

API is available at `http://localhost:5000`.

## Project structure

```
task-management-api/
├── app/
│   ├── __init__.py       # create_app() factory
│   ├── models.py         # User, Project, Task models
│   ├── schemas.py        # Marshmallow schemas
│   ├── utils.py          # success_response(), error_response(), paginate_query()
│   └── routes/
│       ├── auth.py       # /auth/* endpoints
│       ├── projects.py   # /projects/* endpoints
│       └── tasks.py      # /projects/:id/tasks/* endpoints
├── tests/
│   ├── conftest.py       # pytest fixtures
│   └── test_api.py       # 15 integration tests
├── config.py             # Development / Testing / Production configs
├── run.py                # Development server entry point
├── wsgi.py               # PythonAnywhere WSGI entry point
└── requirements.txt
```

## API endpoints

All responses follow the format:
```json
{"success": true, "message": "...", "data": ...}
```

### Auth

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/auth/register` | None | Create account |
| POST | `/auth/login` | None | Get access + refresh tokens |
| POST | `/auth/refresh` | Refresh token | Get new access token |
| GET | `/auth/me` | Bearer token | Current user profile |

### Projects

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/projects` | Bearer token | List all (paginated) |
| POST | `/projects` | Bearer token | Create project |
| GET | `/projects/:id` | Bearer token | Get project |
| PUT | `/projects/:id` | Owner only | Update project |
| DELETE | `/projects/:id` | Owner only | Delete project + tasks |

### Tasks

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/projects/:id/tasks` | Bearer token | List tasks (filtered + paginated) |
| POST | `/projects/:id/tasks` | Owner only | Create task |
| GET | `/projects/:id/tasks/:tid` | Bearer token | Get task |
| PUT | `/projects/:id/tasks/:tid` | Owner only | Update task |
| DELETE | `/projects/:id/tasks/:tid` | Owner only | Delete task |

**Task filters** (query params on `GET /projects/:id/tasks`):

| Param | Example | Effect |
|-------|---------|--------|
| `status` | `?status=done` | Filter by status |
| `priority` | `?priority=high` | Filter by priority |
| `assigned_to` | `?assigned_to=2` | Filter by user ID |
| `overdue` | `?overdue=true` | Tasks past `due_date` |
| `page` | `?page=2` | Pagination page |
| `per_page` | `?per_page=20` | Items per page (max 50) |

## Example usage

```bash
# Register
curl -X POST http://localhost:5000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"ali","email":"ali@example.com","password":"securepass"}'

# Login
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"ali@example.com","password":"securepass"}'

# Create project
curl -X POST http://localhost:5000/projects \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"name":"My Project"}'

# Create task
curl -X POST http://localhost:5000/projects/1/tasks \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"title":"Build API","priority":"urgent","status":"in_progress"}'

# Filter tasks
curl "http://localhost:5000/projects/1/tasks?status=done&priority=high" \
  -H "Authorization: Bearer <access_token>"
```

## Running tests

```bash
pytest tests/ -v
```

### Actual test output

```
tests/test_api.py::TestAuth::test_01_register_success PASSED             [  6%]
tests/test_api.py::TestAuth::test_02_register_duplicate_email PASSED     [ 13%]
tests/test_api.py::TestAuth::test_03_login_success PASSED                [ 20%]
tests/test_api.py::TestAuth::test_04_login_wrong_password PASSED         [ 26%]
tests/test_api.py::TestAuth::test_05_get_me PASSED                       [ 33%]
tests/test_api.py::TestProjects::test_06_create_project PASSED           [ 40%]
tests/test_api.py::TestProjects::test_07_list_projects_paginated PASSED  [ 46%]
tests/test_api.py::TestProjects::test_08_get_project PASSED              [ 53%]
tests/test_api.py::TestProjects::test_09_update_project_owner_only PASSED [ 60%]tests/test_api.py::TestProjects::test_10_delete_project PASSED           [ 66%]
tests/test_api.py::TestTasks::test_11_create_task PASSED                 [ 73%]
tests/test_api.py::TestTasks::test_12_list_tasks_with_status_filter PASSED [ 80%]
tests/test_api.py::TestTasks::test_13_filter_by_priority PASSED          [ 86%]
tests/test_api.py::TestTasks::test_14_update_task PASSED                 [ 93%]
tests/test_api.py::TestTasks::test_15_delete_task_and_overdue_filter PASSED [100%]

======================= 15 passed, 23 warnings in 8.89s =======================
```

## Deploy to PythonAnywhere (free tier)

### Step 1 — Create account
Sign up at https://www.pythonanywhere.com (free tier is sufficient).

### Step 2 — Upload your code
In the PythonAnywhere dashboard, open a **Bash console** and run:
```bash
git clone https://github.com/maida-maryam06/task-management-api.git
cd task-management-api
pip3 install --user -r requirements.txt
```

### Step 3 — Create a Web App
- Dashboard → **Web** tab → **Add a new web app**
- Choose **Manual configuration** (not Flask)
- Choose **Python 3.10** (or latest available)

### Step 4 — Configure WSGI
- On the Web tab, click the WSGI configuration file link
- Replace its entire content with:

```python
import sys
sys.path.insert(0, '/home/YOUR_USERNAME/task-management-api')

from wsgi import application
```

Replace `YOUR_USERNAME` with your actual PythonAnywhere username.

### Step 5 — Set environment variables
In the Web tab → **Environment variables** section, add:
```
SECRET_KEY=your-strong-random-secret-key-here
JWT_SECRET_KEY=another-strong-jwt-secret-key-here
FLASK_ENV=production
```

### Step 6 — Reload and test
Click **Reload** on the Web tab. Your API is live at:
`https://YOUR_USERNAME.pythonanywhere.com`

Test it:
```bash
curl https://YOUR_USERNAME.pythonanywhere.com/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@test.com","password":"testpass"}'
```


## License

MIT
