"""
app/routes/auth.py — Authentication endpoints.

Endpoints:
    POST /auth/register   — create a new user account
    POST /auth/login      — exchange email+password for JWT tokens
    POST /auth/refresh    — get a new access token via refresh token
    GET  /auth/me         — return the current user's profile
"""

from flask import Blueprint, request
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, verify_jwt_in_request
)
from marshmallow import ValidationError

from app import db
from app.models import User
from app.schemas import user_schema, login_schema
from app.utils import success_response, error_response

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    """Register a new user account.

    Request body (JSON):
        username (str, required): 3-80 characters.
        email    (str, required): valid email address.
        password (str, required): minimum 6 characters.

    Returns:
        201 with the new user's profile on success.
        400 if validation fails or the email/username already exists.
    """
    try:
        data = user_schema.load(request.get_json() or {})
    except ValidationError as err:
        return error_response(str(err.messages), 400)

    if User.query.filter_by(email=data["email"]).first():
        return error_response("Email already registered.", 400)
    if User.query.filter_by(username=data["username"]).first():
        return error_response("Username already taken.", 400)

    user = User(username=data["username"], email=data["email"])
    user.set_password(data["password"])
    db.session.add(user)
    db.session.commit()

    return success_response(user_schema.dump(user), "User registered successfully.", 201)


@auth_bp.route("/login", methods=["POST"])
def login():
    """Log in and receive JWT access + refresh tokens.

    Request body (JSON):
        email    (str, required): registered email address.
        password (str, required): account password.

    Returns:
        200 with access_token, refresh_token, and user profile on success.
        401 if credentials are invalid.
    """
    try:
        data = login_schema.load(request.get_json() or {})
    except ValidationError as err:
        return error_response(str(err.messages), 400)

    user = User.query.filter_by(email=data["email"]).first()
    if not user or not user.check_password(data["password"]):
        return error_response("Invalid email or password.", 401)

    access_token  = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    return success_response({
        "access_token":  access_token,
        "refresh_token": refresh_token,
        "user":          user_schema.dump(user),
    }, "Login successful.")


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    """Issue a new access token using a valid refresh token.

    Requires:
        Authorization: Bearer <refresh_token> header.

    Returns:
        200 with a new access_token on success.
    """
    user_id      = get_jwt_identity()
    access_token = create_access_token(identity=user_id)
    return success_response({"access_token": access_token}, "Token refreshed.")


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    """Return the currently authenticated user's profile.

    Requires:
        Authorization: Bearer <access_token> header.

    Returns:
        200 with the user's profile on success.
        404 if the token refers to a deleted user.
    """
    user_id = int(get_jwt_identity())
    user    = db.session.get(User, user_id)
    if not user:
        return error_response("User not found.", 404)
    return success_response(user_schema.dump(user), "User profile.")
