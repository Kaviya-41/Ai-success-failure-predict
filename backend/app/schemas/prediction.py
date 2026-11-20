from typing import List, Optional

from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):

    budget: float = Field(..., ge=0)

    duration_days: int = Field(..., ge=0)

    team_size: int = Field(..., ge=0)

    team_experience_years: float = Field(
        ...,
        ge=0
    )

    project_complexity: int = Field(
        ...,
        ge=1,
        le=5
    )

    requirement_changes: int = Field(
        ...,
        ge=0
    )

    sprint_delays: int = Field(
        ...,
        ge=0
    )

    bug_count: int = Field(
        ...,
        ge=0
    )

    testing_coverage: float = Field(
        ...,
        ge=0,
        le=100
    )

    client_involvement: int = Field(
        ...,
        ge=1,
        le=5
    )

    resource_availability: float = Field(
        ...,
        ge=0,
        le=100
    )

    customer_satisfaction: int = Field(
        ...,
        ge=1,
        le=5
    )

    project_type: str = "Web"


class PredictionResponse(BaseModel):

    is_successful_prediction: bool

    success_probability: float

    failure_probability: float

    risk_score: float

    risk_level: str

    health_score: float

    confidence_score: float

    prediction_time_ms: float

    model_algorithm: str

    prediction: str

    top_risk_factors: List[str]

    top_success_factors: List[str]

    recommendations: List[str]

    success_conditions: int

    failure_conditions: int

    total_conditions: int

    project_type: str


class WhatIfRequest(BaseModel):

    project_id: Optional[int] = None

    current_values: PredictionRequest


class WhatIfResponse(BaseModel):

    base_prediction: Optional[PredictionResponse] = None

    simulated_prediction: PredictionResponse