import os
import io
import json
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.dataset import Dataset
from app.models.activity_log import ActivityLog
from app.schemas.dataset import DatasetOut

router = APIRouter(prefix="/datasets")

@router.post("/upload", response_model=DatasetOut)
def upload_dataset(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Uploads a CSV or Excel dataset, validates its structure, performs analysis of missing/duplicate fields, and saves it."""
    filename = file.filename
    if not (filename.endswith(".csv") or filename.endswith(".xlsx") or filename.endswith(".xls")):
        raise HTTPException(status_code=400, detail="Only CSV or Excel files are supported")
        
    try:
        contents = file.file.read()
        if filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_excel(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {str(e)}")
        
    row_count = len(df)
    if row_count == 0:
        raise HTTPException(status_code=400, detail="The uploaded dataset is empty")
        
    # Analyze data structure
    missing_total = int(df.isnull().sum().sum())
    duplicate_count = int(df.duplicated().sum())
    
    # Check if necessary target and feature columns are present for training
    required_features = ["budget", "duration_days", "team_size", "team_experience_years", "testing_coverage", "bug_count", "status"]
    missing_req = [f for f in required_features if f not in df.columns]
    
    columns_info = {}
    for col in df.columns:
        col_type = str(df[col].dtype)
        unique_vals = int(df[col].nunique())
        columns_info[col] = {
            "type": col_type,
            "unique_values": unique_vals,
            "missing": int(df[col].isnull().sum())
        }
        
    features_json_data = {
        "columns": columns_info,
        "missing_total": missing_total,
        "duplicate_count": duplicate_count,
        "missing_required_features": missing_req,
        "is_trainable": len(missing_req) == 0
    }
    
    # Create dataset database entry
    dataset = Dataset(
        filename=filename,
        row_count=row_count,
        features_json=json.dumps(features_json_data),
        uploaded_by=current_user.id
    )
    
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    
    # Save the file locally so it can be loaded for retraining
    datasets_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "uploaded_datasets")
    os.makedirs(datasets_dir, exist_ok=True)
    local_path = os.path.join(datasets_dir, f"dataset_{dataset.id}_{filename}")
    with open(local_path, "wb") as f_out:
        f_out.write(contents)
        
    # Audit log
    log = ActivityLog(action="upload_dataset", details=f"Uploaded dataset {filename}", user_id=current_user.id)
    db.add(log)
    db.commit()
    
    return dataset

@router.get("/", response_model=list[DatasetOut])
def list_datasets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lists all uploaded datasets."""
    return db.query(Dataset).order_by(Dataset.uploaded_at.desc()).all()
