"""
app/routes/tasks.py — Task CRUD endpoints.

Endpoints:
    GET    /projects/<id>/tasks          — list tasks with filters + pagination
    POST   /projects/<id>/tasks          — create a task in a project
    GET    /projects/<id>/tasks/<tid>    — get a single task
    PUT    /projects/<id>/tasks/<tid>    — update a task
    DELETE /projects/<id>/tasks/<tid>    — delete a task
"""

from datetime import datetime, timezone
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError

from app import db
from app.models import Project, Task
from app.schemas import task_schema, task_list_schema, task_update_schema
from app.utils import success_response, error_response, paginate_query

tasks_bp = Blueprint("tasks", __name__)


def _get_project_or_404(project_id: int):
    """Fetch a project by ID or return None (caller sends 404)."""
    return db.session.get(Project, project_id)


@tasks_bp.route("/<int:project_id>/tasks", methods=["GET"])
@jwt_required()
def list_tasks(project_id: int):
    """List tasks in a project with optional filters and pagination.

    Query params:
        status      (str):  filter by status (todo/in_progress/done).
        priority    (str):  filter by priority (low/medium/high/urgent).
        assigned_to (int):  filter by assigned user ID.
        overdue     (bool): if "true", return only tasks past their due_date.
        page        (int):  page number (default 1).
        per_page    (int):  items per page (default 10, max 50).

    Returns:
        200 with paginated, filtered task list.
        404 if the project is not found.
    """
    project = _get_project_or_404(project_id)
    if not project:
        return error_response("Project not found.", 404)

    query = Task.query.filter_by(project_id=project_id)

    # --- Filters ---
    status      = request.args.get("status")
    priority    = request.args.get("priority")
    assigned_to = request.args.get("assigned_to", type=int)
    overdue     = request.args.get("overdue", "").lower() == "true"

    if status:
        query = query.filter(Task.status == status)
    if priority:
        query = query.filter(Task.priority == priority)
    if assigned_to:
        query = query.filter(Task.assigned_to == assigned_to)
    if overdue:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        query = query.filter(Task.due_date != None, Task.due_date < now)

    query  = query.order_by(Task.created_at.desc())
    page     = request.args.get("page",     1,  type=int)
    per_page = min(request.args.get("per_page", 10, type=int), 50)
    result   = paginate_query(query, task_list_schema, page, per_page)
    return success_response(result, "Tasks retrieved.")


@tasks_bp.route("/<int:project_id>/tasks", methods=["POST"])
@jwt_required()
def create_task(project_id: int):
    """Create a new task inside a project.

    Only the project owner can create tasks. Assignment is optional.

    Request body (JSON):
        title       (str, required): task title.
        description (str, optional): task detail.
        status      (str, optional): default "todo".
        priority    (str, optional): default "medium".
        due_date    (str, optional): ISO datetime string.
        assigned_to (int, optional): user ID to assign to.

    Returns:
        201 with the new task.
        403 if the current user is not the project owner.
        404 if the project is not found.
    """
    project = _get_project_or_404(project_id)
    if not project:
        return error_response("Project not found.", 404)

    user_id = int(get_jwt_identity())
    if project.owner_id != user_id:
        return error_response("Only the project owner can create tasks.", 403)

    try:
        data = task_schema.load(request.get_json() or {})
    except ValidationError as err:
        return error_response(str(err.messages), 400)

    # Strip timezone info for SQLite storage
    due_date = data.get("due_date")
    if due_date and hasattr(due_date, "tzinfo") and due_date.tzinfo:
        due_date = due_date.replace(tzinfo=None)

    task = Task(
        title=data["title"],
        description=data.get("description"),
        status=data.get("status", "todo"),
        priority=data.get("priority", "medium"),
        due_date=due_date,
        assigned_to=data.get("assigned_to"),
        project_id=project_id,
    )
    db.session.add(task)
    db.session.commit()
    return success_response(task_schema.dump(task), "Task created.", 201)


@tasks_bp.route("/<int:project_id>/tasks/<int:task_id>", methods=["GET"])
@jwt_required()
def get_task(project_id: int, task_id: int):
    """Get a single task by ID.

    Returns:
        200 with the task on success.
        404 if the project or task is not found.
    """
    project = _get_project_or_404(project_id)
    if not project:
        return error_response("Project not found.", 404)

    task = Task.query.filter_by(id=task_id, project_id=project_id).first()
    if not task:
        return error_response("Task not found.", 404)

    return success_response(task_schema.dump(task), "Task retrieved.")


@tasks_bp.route("/<int:project_id>/tasks/<int:task_id>", methods=["PUT"])
@jwt_required()
def update_task(project_id: int, task_id: int):
    """Update a task. Only the project owner can update tasks.

    All fields are optional (partial update).

    Returns:
        200 with the updated task.
        403 if not the project owner.
        404 if project or task not found.
    """
    project = _get_project_or_404(project_id)
    if not project:
        return error_response("Project not found.", 404)

    user_id = int(get_jwt_identity())
    if project.owner_id != user_id:
        return error_response("Only the project owner can update tasks.", 403)

    task = Task.query.filter_by(id=task_id, project_id=project_id).first()
    if not task:
        return error_response("Task not found.", 404)

    try:
        data = task_update_schema.load(request.get_json() or {})
    except ValidationError as err:
        return error_response(str(err.messages), 400)

    for field in ("title", "description", "status", "priority", "assigned_to"):
        if field in data:
            setattr(task, field, data[field])

    if "due_date" in data:
        due = data["due_date"]
        if due and hasattr(due, "tzinfo") and due.tzinfo:
            due = due.replace(tzinfo=None)
        task.due_date = due

    task.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.session.commit()
    return success_response(task_schema.dump(task), "Task updated.")


@tasks_bp.route("/<int:project_id>/tasks/<int:task_id>", methods=["DELETE"])
@jwt_required()
def delete_task(project_id: int, task_id: int):
    """Delete a task. Only the project owner can delete tasks.

    Returns:
        200 with confirmation.
        403 if not the project owner.
        404 if project or task not found.
    """
    project = _get_project_or_404(project_id)
    if not project:
        return error_response("Project not found.", 404)

    user_id = int(get_jwt_identity())
    if project.owner_id != user_id:
        return error_response("Only the project owner can delete tasks.", 403)

    task = Task.query.filter_by(id=task_id, project_id=project_id).first()
    if not task:
        return error_response("Task not found.", 404)

    db.session.delete(task)
    db.session.commit()
    return success_response(None, "Task deleted.")
