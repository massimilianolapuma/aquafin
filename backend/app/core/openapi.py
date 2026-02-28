"""Custom OpenAPI schema configuration for Aquafin API."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def custom_openapi(app: FastAPI) -> dict[str, Any]:
    """Generate a custom OpenAPI schema with project metadata.

    Caches the schema on the app instance so it's computed only once.
    """
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Aquafin API",
        version="1.0.0",
        description="Personal finance management API",
        routes=app.routes,
    )

    openapi_schema["info"]["contact"] = {
        "name": "Aquafin Team",
        "email": "support@aquafin.app",
    }
    openapi_schema["info"]["license"] = {
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema
