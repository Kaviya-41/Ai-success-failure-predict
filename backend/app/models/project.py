from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=True)
    company_name = Column(String, nullable=True)
    project_type = Column(String, nullable=True) # e.g., Web, Mobile, AI/ML, Cloud, DevOps, Security
    
    # Financials & Planning
    budget = Column(Float, default=0.0)
    duration_days = Column(Integer, default=0)
    
    # Team Metrics
    team_size = Column(Integer, default=0)
    team_experience_years = Column(Float, default=0.0)
    tech_stack = Column(String, nullable=True) # Comma-separated list or tags
    
    # Execution Metrics
    requirement_changes = Column(Integer, default=0)
    sprint_delays = Column(Integer, default=0)
    bug_count = Column(Integer, default=0)
    testing_coverage = Column(Float, default=0.0) # Percentage (0-100)
    
    # Client & Resources
    client_involvement = Column(Integer, default=3) # Rating 1-5
    resource_availability = Column(Float, default=100.0) # Percentage (0-100)
    customer_satisfaction = Column(Integer, default=3) # Rating 1-5
    project_complexity = Column(Integer, default=3) # Rating 1-5
    
    # Prediction Results
    success_probability = Column(Float, nullable=True)
    failure_probability = Column(Float, nullable=True)
    risk_score = Column(Float, nullable=True) # 0-100
    risk_level = Column(String, nullable=True) # Low, Medium, High
    health_score = Column(Float, nullable=True) # 0-100
    is_successful_prediction = Column(Boolean, nullable=True) # True = Success, False = Failure
    
    is_archived = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Owner relationship
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    workspace_id = Column(
        Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    owner = relationship("User", back_populates="projects")
    workspace = relationship("Workspace")
