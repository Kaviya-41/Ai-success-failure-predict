from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DatasetOut(BaseModel):
    id: int
    filename: str
    row_count: int
    features_json: Optional[str] = None
    uploaded_at: datetime
    uploaded_by: int

    class Config:
        from_attributes = True
