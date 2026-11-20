from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import Base, engine
from app.api.api import api_router
from app import models as registered_models
from app.db_migrations import upgrade_workspace_schema


# ---------------------------------------------------------
# Create database tables
# ---------------------------------------------------------

Base.metadata.create_all(
    bind=engine
)
upgrade_workspace_schema(engine)


# ---------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------

app = FastAPI(
    title="AI Project Success/Failure Prediction System API",
    description=(
        "Software project outcome prediction system "
        "using a Success/Failure IF-ELSE decision algorithm."
    ),
    version="1.0.0"
)


# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------

app.add_middleware(
    CORSMiddleware,

    allow_origins=settings.cors_origins,

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


# ---------------------------------------------------------
# API Router
# ---------------------------------------------------------

app.include_router(
    api_router,
    prefix="/api"
)


# ---------------------------------------------------------
# Root endpoint
# ---------------------------------------------------------

@app.get("/")
def read_root():

    return {
        "message": (
            "AI Project Success/Failure "
            "Prediction System API is running."
        ),

        "algorithm": (
            "Success/Failure IF-ELSE "
            "Decision Algorithm"
        )
    }


# ---------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------

@app.get("/health")
def health_check():

    return {
        "status": "healthy",

        "algorithm": (
            "Success/Failure IF-ELSE"
        )
    }