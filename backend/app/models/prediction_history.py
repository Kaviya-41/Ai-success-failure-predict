from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base
from app.models.workspace import Workspace

class PredictionHistory(Base):
    """
    Stores historical prediction results for tracking and auditing.
    """
    __tablename__ = "prediction_history"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    
    # Prediction method
    method = Column(String, default="baseline")  # baseline, xgboost, etc.
    
    # Input metrics
    metrics_json = Column(Text, nullable=True)  # JSON string of input metrics
    
    # Results
    is_successful_prediction = Column(Boolean, nullable=True)
    success_probability = Column(Float, nullable=True)
    failure_probability = Column(Float, nullable=True)
    risk_score = Column(Float, nullable=True)
    risk_level = Column(String, nullable=True)
    health_score = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=True)
    prediction = Column(String, nullable=True)  # "Success" or "Failure"
    
    # Explanation
    shap_explanation = Column(JSON, nullable=True)  # SHAP values if available
    top_risk_factors = Column(JSON, nullable=True)
    top_success_factors = Column(JSON, nullable=True)
    recommendations = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    project = relationship("Project", foreign_keys=[project_id])


class GitHubRepository(Base):
    """
    Stores GitHub repository analysis results.
    """
    __tablename__ = "github_repositories"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    workspace_id = Column(
        Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True
    )
    
    # Repository info
    repository_url = Column(String, nullable=False)
    repository_name = Column(String, nullable=False)
    is_private = Column(Boolean, default=False)
    
    # GitHub metrics
    total_commits = Column(Integer, default=0)
    contributors = Column(Integer, default=0)
    stars = Column(Integer, default=0)
    forks = Column(Integer, default=0)
    open_issues = Column(Integer, default=0)
    branches = Column(Integer, default=0)
    language = Column(String, nullable=True)
    
    # Estimated project metrics from GitHub
    estimated_metrics = Column(JSON, nullable=True)
    
    analyzed_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    project = relationship("Project", foreign_keys=[project_id])
    workspace = relationship("Workspace")


class ModelVersion(Base):
    """
    Stores different versions of trained models.
    """
    __tablename__ = "model_versions"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String, nullable=False, unique=True)
    algorithm = Column(String, nullable=False)  # xgboost, random_forest, etc.
    
    # Training info
    dataset_id = Column(Integer, ForeignKey("datasets.id", ondelete="SET NULL"), nullable=True)
    training_date = Column(DateTime, default=datetime.utcnow)
    
    # Model metrics
    accuracy = Column(Float, default=0.0)
    precision = Column(Float, default=0.0)
    recall = Column(Float, default=0.0)
    f1_score = Column(Float, default=0.0)
    roc_auc = Column(Float, default=0.0)
    
    # Training data info
    training_samples = Column(Integer, default=0)
    test_samples = Column(Integer, default=0)
    
    # Feature importance (top features)
    top_features = Column(JSON, nullable=True)
    
    # Status
    file_path = Column(String, nullable=False)
    is_active = Column(Boolean, default=False)
    
    # Metadata
    training_duration_seconds = Column(Float, nullable=True)
    preprocessing_notes = Column(Text, nullable=True)
    
    # Relationships
    dataset = relationship("Dataset", foreign_keys=[dataset_id])
