from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    company_name: Optional[str] = None
    project_type: Optional[str] = "Web"
    
    # Financials & Planning
    budget: float = Field(0.0, ge=0)
    duration_days: int = Field(0, ge=0)
    
    # Team Metrics
    team_size: int = Field(0, ge=0)
    team_experience_years: float = Field(0.0, ge=0)
    tech_stack: Optional[str] = None
    
    # Execution Metrics
    requirement_changes: int = Field(0, ge=0)
    sprint_delays: int = Field(0, ge=0)
    bug_count: int = Field(0, ge=0)
    testing_coverage: float = Field(0.0, ge=0, le=100)
    
    # Client & Resources
    client_involvement: int = Field(3, ge=1, le=5)
    resource_availability: float = Field(100.0, ge=0, le=100)
    customer_satisfaction: int = Field(3, ge=1, le=5)
    project_complexity: int = Field(3, ge=1, le=5)

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    company_name: Optional[str] = None
    project_type: Optional[str] = None
    budget: Optional[float] = None
    duration_days: Optional[int] = None
    team_size: Optional[int] = None
    team_experience_years: Optional[float] = None
    tech_stack: Optional[str] = None
    requirement_changes: Optional[int] = None
    sprint_delays: Optional[int] = None
    bug_count: Optional[int] = None
    testing_coverage: Optional[float] = None
    client_involvement: Optional[int] = None
    resource_availability: Optional[float] = None
    customer_satisfaction: Optional[int] = None
    project_complexity: Optional[int] = None
    is_archived: Optional[bool] = None

class ProjectOut(ProjectBase):
    id: int
    workspace_id: int
    success_probability: Optional[float] = None
    failure_probability: Optional[float] = None
    risk_score: Optional[float] = None
    risk_level: Optional[str] = None
    health_score: Optional[float] = None
    is_successful_prediction: Optional[bool] = None
    is_archived: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    owner_id: Optional[int] = None

    class Config:
        from_attributes = True
