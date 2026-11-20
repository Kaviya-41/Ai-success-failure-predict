from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from datetime import datetime
from app.core.database import Base

class ModelMetadata(Base):
    __tablename__ = "model_metadata"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String, nullable=False, unique=True) # Unique model identifier
    algorithm = Column(String, nullable=False) # XGBoost, Random Forest, etc.
    
    # Evaluation Metrics
    accuracy = Column(Float, default=0.0)
    precision = Column(Float, default=0.0)
    recall = Column(Float, default=0.0)
    f1_score = Column(Float, default=0.0)
    roc_auc = Column(Float, default=0.0)
    
    file_path = Column(String, nullable=False) # Path to saved joblib model file
    is_active = Column(Boolean, default=False) # Is this the active model used for predictions?
    trained_at = Column(DateTime, default=datetime.utcnow)
