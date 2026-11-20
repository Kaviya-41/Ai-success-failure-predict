from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    row_count = Column(Integer, default=0)
    features_json = Column(String, nullable=True) # JSON representation of columns and stats
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    # Uploader relationship
    uploaded_by = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    uploader = relationship("User", back_populates="datasets")
