from fastapi import APIRouter

from app.api.endpoints import (
    auth,
    projects,
    predictions,
    datasets,
    models,
    notifications,
    admin,
    reports,
    github,
    ml_predictions,
    workspaces,
)


api_router = APIRouter()


api_router.include_router(
    auth.router
)

api_router.include_router(
    workspaces.router
)

api_router.include_router(
    projects.router
)

api_router.include_router(
    predictions.router
)

api_router.include_router(
    ml_predictions.router
)

api_router.include_router(
    datasets.router
)

api_router.include_router(
    models.router
)

api_router.include_router(
    github.router
)

api_router.include_router(
    notifications.router
)

api_router.include_router(
    admin.router
)

api_router.include_router(
    reports.router
)