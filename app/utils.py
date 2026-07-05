"""
app/utils.py — Shared utility functions.
"""

from flask import jsonify


def success_response(data=None, message: str = "OK", status_code: int = 200):
    """Build a consistent success JSON response.

    Args:
        data:        The payload to return (dict, list, or None).
        message:     Human-readable status message.
        status_code: HTTP status code (default 200).

    Returns:
        A Flask Response object.
    """
    return jsonify({
        "success": True,
        "message": message,
        "data":    data,
    }), status_code


def error_response(message: str, status_code: int = 400):
    """Build a consistent error JSON response.

    Args:
        message:     Human-readable error description.
        status_code: HTTP status code (default 400).

    Returns:
        A Flask Response object.
    """
    return jsonify({
        "success": False,
        "message": message,
        "data":    None,
    }), status_code


def paginate_query(query, schema, page: int, per_page: int):
    """Paginate a SQLAlchemy query and serialize the results.

    Args:
        query:    SQLAlchemy query object.
        schema:   Marshmallow schema instance (many=True) for serialization.
        page:     Current page number (1-indexed).
        per_page: Number of items per page.

    Returns:
        A dict with keys: items, total, pages, page, per_page.
    """
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    return {
        "items":    schema.dump(paginated.items),
        "total":    paginated.total,
        "pages":    paginated.pages,
        "page":     paginated.page,
        "per_page": paginated.per_page,
    }
