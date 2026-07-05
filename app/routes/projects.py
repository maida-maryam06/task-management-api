"""
app/routes/projects.py — Project CRUD endpoints.

Endpoints:
    GET    /projects          — list all projects (paginated)
    POST   /projects          — create a new project
    GET    /projects/<id>     — get a single project
    PUT    /projects/<id>     — update a project (owner only)
    DELETE /projects/<id>     — delete a project (owner only)
"""

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError

from app import db
from app.models import Project
from app.schemas import project_schema, project_list_schema
from app.utils import success_response, error_response, paginate_query

projects_bp = Blueprint("projects", __name__)


@projects_bp.route("", methods=["GET"])
@jwt_required()
def list_projects():
    """List all projects with pagination.

    Query params:
        page     (int, default 1):  page number.
        per_page (int, default 10): items per page (max 50).

    Returns:
        200 with paginated project list.
    """
    page     = request.args.get("page",     1,  type=int)
    per_page = min(request.args.get("per_page", 10, type=int), 50)
    query    = Project.query.order_by(Project.created_at.desc())
    result   = paginate_query(query, project_list_schema, page, per_page)
    return success_response(result, "Projects retrieved.")


@projects_bp.route("", methods=["POST"])
@jwt_required()
def create_project():
    """Create a new project owned by the current user.

    Request body (JSON):
        name        (str, required): project name.
        description (str, optional): project description.

    Returns:
        201 with the new project on success.
        400 if validation fails.
    """
    try:
        data = project_schema.load(request.get_json() or {})
    except ValidationError as err:
        return error_response(str(err.messages), 400)

    owner_id = int(get_jwt_identity())
    project  = Project(
        name=data["name"],
        description=data.get("description"),
        owner_id=owner_id,
    )
    db.session.add(project)
    db.session.commit()
    return success_response(project_schema.dump(project), "Project created.", 201)


@projects_bp.route("/<int:project_id>", methods=["GET"])
@jwt_required()
def get_project(project_id: int):
    """Get a single project by ID.

    Returns:
        200 with the project on success.
        404 if not found.
    """
    project = db.session.get(Project, project_id)
    if not project:
        return error_response("Project not found.", 404)
    return success_response(project_schema.dump(project), "Project retrieved.")


@projects_bp.route("/<int:project_id>", methods=["PUT"])
@jwt_required()
def update_project(project_id: int):
    """Update a project. Only the owner may edit.

    Request body (JSON):
        name        (str, optional): new project name.
        description (str, optional): new description.

    Returns:
        200 with updated project on success.
        403 if the current user is not the owner.
        404 if not found.
    """
    project = db.session.get(Project, project_id)
    if not project:
        return error_response("Project not found.", 404)

    user_id = int(get_jwt_identity())
    if project.owner_id != user_id:
        return error_response("Only the project owner can edit it.", 403)

    try:
        data = project_schema.load(request.get_json() or {}, partial=True)
    except ValidationError as err:
        return error_response(str(err.messages), 400)

    if "name"        in data: project.name        = data["name"]
    if "description" in data: project.description = data["description"]

    db.session.commit()
    return success_response(project_schema.dump(project), "Project updated.")


@projects_bp.route("/<int:project_id>", methods=["DELETE"])
@jwt_required()
def delete_project(project_id: int):
    """Delete a project and all its tasks. Only the owner may delete.

    Returns:
        200 with confirmation on success.
        403 if the current user is not the owner.
        404 if not found.
    """
    project = db.session.get(Project, project_id)
    if not project:
        return error_response("Project not found.", 404)

    user_id = int(get_jwt_identity())
    if project.owner_id != user_id:
        return error_response("Only the project owner can delete it.", 403)

    db.session.delete(project)
    db.session.commit()
    return success_response(None, "Project deleted.")
