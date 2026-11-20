"""
Training service for machine learning models.

Handles data preprocessing, model training, and evaluation.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple, List
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
import xgboost as xgb
import joblib
import os
from datetime import datetime


class TrainingService:
    """
    Service for training XGBoost models on project datasets.
    
    Features used for training:
    - budget
    - duration_days
    - team_size
    - team_experience_years
    - project_complexity
    - requirement_changes
    - sprint_delays
    - bug_count
    - testing_coverage
    - client_involvement
    - resource_availability
    - customer_satisfaction
    
    Target: status (1 = Success, 0 = Failure)
    """
    
    FEATURE_COLUMNS = [
        "budget",
        "duration_days",
        "team_size",
        "team_experience_years",
        "project_complexity",
        "requirement_changes",
        "sprint_delays",
        "bug_count",
        "testing_coverage",
        "client_involvement",
        "resource_availability",
        "customer_satisfaction",
    ]
    
    TARGET_COLUMN = "status"
    
    MODELS_DIR = None  # Set during initialization
    
    @staticmethod
    def set_models_dir(path: str):
        """Set the directory where models are saved."""
        TrainingService.MODELS_DIR = path
        os.makedirs(path, exist_ok=True)
    
    @staticmethod
    def preprocess_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, Dict[str, Any]]:
        """
        Preprocess dataset for training.
        
        Args:
            df: Raw dataframe from uploaded file
            
        Returns:
            X: Features dataframe
            y: Target series
            metadata: Info about preprocessing
        """
        metadata = {
            "total_samples": len(df),
            "original_rows": len(df),
            "original_columns": len(df.columns)
        }
        
        # Convert target column to binary (1 for success, 0 for failure)
        # Acceptable variations: success/failure, 1/0, true/false, yes/no
        if TrainingService.TARGET_COLUMN not in df.columns:
            # Try to find a status-like column
            status_cols = [col for col in df.columns if 'status' in col.lower() or 'success' in col.lower() or 'result' in col.lower()]
            if status_cols:
                target_col = status_cols[0]
            else:
                raise ValueError(f"No target column '{TrainingService.TARGET_COLUMN}' found in dataset")
        else:
            target_col = TrainingService.TARGET_COLUMN
        
        # Create binary target
        y = df[target_col].copy()
        
        # Convert to binary (1 = success/true/yes, 0 = failure/false/no)
        if y.dtype == 'object':
            y = y.str.lower()
            y = y.isin(['success', '1', 'true', 'yes', 'pass']).astype(int)
        else:
            y = (y > 0).astype(int)
        
        metadata["target_distribution"] = {
            "success_count": int(y.sum()),
            "failure_count": int((y == 0).sum())
        }
        
        # Select features
        X = df[TrainingService.FEATURE_COLUMNS].copy()
        
        # Handle missing values
        missing_before = X.isnull().sum().sum()
        X = X.fillna(X.mean())  # Fill numeric missing with mean
        X = X.fillna(0)  # Fill remaining with 0
        missing_after = X.isnull().sum().sum()
        
        metadata["missing_values_filled"] = missing_before
        
        # Remove rows with missing target
        valid_idx = y.notna()
        X = X[valid_idx]
        y = y[valid_idx]
        
        metadata["final_rows"] = len(X)
        
        # Check if we have enough data
        if len(X) < 10:
            raise ValueError(f"Dataset too small after preprocessing: {len(X)} rows (need at least 10)")
        
        return X, y, metadata
    
    @staticmethod
    def train_xgboost(X: pd.DataFrame, y: pd.Series, test_size: float = 0.2) -> Dict[str, Any]:
        """
        Train XGBoost classifier.
        
        Args:
            X: Features
            y: Target (binary)
            test_size: Test set fraction
            
        Returns:
            Dictionary with model, metrics, and metadata
        """
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train model
        model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            verbosity=0,
            eval_metric='logloss'
        )
        
        model.fit(
            X_train_scaled, y_train,
            eval_set=[(X_test_scaled, y_test)],
            verbose=False
        )
        
        # Evaluate
        y_pred = model.predict(X_test_scaled)
        y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
        
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, zero_division=0)
        recall = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        roc_auc = roc_auc_score(y_test, y_pred_proba)
        
        return {
            "model": model,
            "scaler": scaler,
            "metrics": {
                "accuracy": float(accuracy),
                "precision": float(precision),
                "recall": float(recall),
                "f1_score": float(f1),
                "roc_auc": float(roc_auc),
                "test_size": test_size,
                "train_samples": len(X_train),
                "test_samples": len(X_test)
            },
            "feature_importance": dict(zip(TrainingService.FEATURE_COLUMNS, model.feature_importances_))
        }
    
    @staticmethod
    def save_model(model: Any, scaler: Any, model_name: str) -> str:
        """
        Save trained model and scaler to disk.
        
        Args:
            model: Trained XGBoost model
            scaler: Fitted scaler
            model_name: Name for the model file
            
        Returns:
            Path to saved model file
        """
        if not TrainingService.MODELS_DIR:
            raise ValueError("Models directory not set. Call set_models_dir() first.")
        
        model_path = os.path.join(TrainingService.MODELS_DIR, f"{model_name}.joblib")
        scaler_path = os.path.join(TrainingService.MODELS_DIR, f"{model_name}_scaler.joblib")
        
        joblib.dump(model, model_path)
        joblib.dump(scaler, scaler_path)
        
        return model_path
    
    @staticmethod
    def load_model(model_name: str) -> Tuple[Any, Any]:
        """
        Load trained model and scaler from disk.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Tuple of (model, scaler)
        """
        if not TrainingService.MODELS_DIR:
            raise ValueError("Models directory not set. Call set_models_dir() first.")
        
        model_path = os.path.join(TrainingService.MODELS_DIR, f"{model_name}.joblib")
        scaler_path = os.path.join(TrainingService.MODELS_DIR, f"{model_name}_scaler.joblib")
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found: {model_path}")
        
        model = joblib.load(model_path)
        scaler = joblib.load(scaler_path)
        
        return model, scaler
    
    @staticmethod
    def train_and_save(df: pd.DataFrame, model_name: str = "xgboost_v1") -> Dict[str, Any]:
        """
        Complete training pipeline: preprocess → train → save.
        
        Args:
            df: Raw dataframe
            model_name: Name for the trained model
            
        Returns:
            Dictionary with training results and metrics
        """
        # Preprocess
        X, y, preprocess_info = TrainingService.preprocess_data(df)
        
        # Train
        training_result = TrainingService.train_xgboost(X, y)
        
        # Save
        model_path = TrainingService.save_model(
            training_result["model"],
            training_result["scaler"],
            model_name
        )
        
        return {
            "model_name": model_name,
            "model_path": model_path,
            "status": "success",
            "preprocessing": preprocess_info,
            "metrics": training_result["metrics"],
            "feature_importance": training_result["feature_importance"],
            "timestamp": datetime.utcnow().isoformat()
        }
