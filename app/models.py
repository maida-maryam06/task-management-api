"""
app/models.py — SQLAlchemy ORM models.

Models:
    User    — registered API users with hashed passwords
    Project — a container for tasks, owned by one user
    Task    — a work item inside a project
"""

from datetime import datetime, timezone
import bcrypt
from app import db


def _now():
    return datetime.now(timezone.utc)


class User(db.Model):
    """Registered API user.

    Attributes:
        id:            Auto-increment primary key.
        username:      Unique display name (max 80 chars).
        email:         Unique email address used for login (max 120 chars).
        password_hash: bcrypt hash of the user's password.
        created_at:    UTC timestamp of account creation.
    """
    __tablename__ = "users"

    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80),  unique=True, nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at    = db.Column(db.DateTime, default=_now)

    owned_projects = db.relationship("Project", backref="owner", lazy=True,
                                     foreign_keys="Project.owner_id")
    assigned_tasks = db.relationship("Task",    backref="assignee", lazy=True,
                                     foreign_keys="Task.assigned_to")

    def set_password(self, password: str) -> None:
        """Hash and store a plain-text password using bcrypt.

        Args:
            password: The plain-text password to hash.
        """
        self.password_hash = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

    def check_password(self, password: str) -> bool:
        """Verify a plain-text password against the stored hash.

        Args:
            password: The plain-text password to verify.

        Returns:
            True if the password matches, False otherwise.
        """
        return bcrypt.checkpw(
            password.encode("utf-8"),
            self.password_hash.encode("utf-8")
        )

    def __repr__(self):
        return f"<User {self.username}>"


class Project(db.Model):
    """A container for tasks, owned by one user.

    Attributes:
        id:          Auto-increment primary key.
        name:        Project name (max 120 chars, required).
        description: Optional description text.
        owner_id:    Foreign key to the User who created this project.
        created_at:  UTC timestamp of project creation.
    """
    __tablename__ = "projects"

    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    owner_id    = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at  = db.Column(db.DateTime, default=_now)

    tasks = db.relationship("Task", backref="project", lazy=True,
                            cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Project {self.name}>"


class Task(db.Model):
    """A work item inside a project.

    Attributes:
        id:          Auto-increment primary key.
        title:       Short task title (max 200 chars, required).
        description: Optional detailed description.
        status:      One of "todo", "in_progress", "done". Defaults to "todo".
        priority:    One of "low", "medium", "high", "urgent". Defaults to "medium".
        due_date:    Optional UTC deadline datetime.
        assigned_to: Foreign key to the User responsible for this task.
        project_id:  Foreign key to the containing Project.
        created_at:  UTC timestamp of task creation.
        updated_at:  UTC timestamp of last update.
    """
    __tablename__ = "tasks"

    VALID_STATUSES   = ("todo", "in_progress", "done")
    VALID_PRIORITIES = ("low", "medium", "high", "urgent")

    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status      = db.Column(db.String(20),  nullable=False, default="todo")
    priority    = db.Column(db.String(20),  nullable=False, default="medium")
    due_date    = db.Column(db.DateTime, nullable=True)
    assigned_to = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    project_id  = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    created_at  = db.Column(db.DateTime, default=_now)
    updated_at  = db.Column(db.DateTime, default=_now, onupdate=_now)

    def __repr__(self):
        return f"<Task {self.title}>"
