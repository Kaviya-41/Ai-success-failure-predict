"""
Integration tests for ML upgrade features.

Tests:
- Training XGBoost models
- SHAP explanations
- GitHub analysis
- Unified predictions
- Prediction history tracking
"""

import pytest
import os
import sys
import json
import tempfile
import pandas as pd
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from app.services.training_service import TrainingService
from app.services.shap_service import SHAPService
from app.services.github_service import GitHubService
from app.services.prediction_service import PredictionService
from app.services.ml_service import MLService
import numpy as np


class TestTrainingService:
    """Test model training pipeline."""
    
    @pytest.fixture(autouse=True)
    def setup_models_dir(self):
        """Setup temporary models directory."""
        self.test_dir = tempfile.mkdtemp()
        TrainingService.set_models_dir(self.test_dir)
        yield
        # Cleanup
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def create_sample_dataset(self):
        """Create sample training dataset."""
        np.random.seed(42)
        n_samples = 50
        
        data = {
            "budget": np.random.randint(50000, 200000, n_samples),
            "duration_days": np.random.randint(30, 365, n_samples),
            "team_size": np.random.randint(3, 20, n_samples),
            "team_experience_years": np.random.uniform(1, 10, n_samples),
            "project_complexity": np.random.randint(1, 5, n_samples),
            "requirement_changes": np.random.randint(0, 10, n_samples),
            "sprint_delays": np.random.randint(0, 5, n_samples),
            "bug_count": np.random.randint(0, 50, n_samples),
            "testing_coverage": np.random.uniform(0, 100, n_samples),
            "client_involvement": np.random.uniform(0, 5, n_samples),
            "resource_availability": np.random.uniform(0, 100, n_samples),
            "customer_satisfaction": np.random.uniform(0, 5, n_samples),
            "status": np.random.randint(0, 2, n_samples)  # Target
        }
        
        return pd.DataFrame(data)
    
    def test_preprocess_data(self):
        """Test data preprocessing."""
        df = self.create_sample_dataset()
        X, y, metadata = TrainingService.preprocess_data(df)
        
        assert X is not None, "Features should not be None"
        assert y is not None, "Target should not be None"
        assert len(X) == len(df), "X should have same length as input"
        assert len(y) == len(df), "y should have same length as input"
        assert metadata["total_samples"] == len(df), "Metadata should track samples"
    
    def test_train_xgboost(self):
        """Test XGBoost training."""
        df = self.create_sample_dataset()
        X, y, _ = TrainingService.preprocess_data(df)
        
        result = TrainingService.train_xgboost(X, y)
        
        assert result is not None, "Training should return result"
        assert "model" in result, "Result should contain model"
        assert "scaler" in result, "Result should contain scaler"
        assert "metrics" in result, "Result should contain metrics"
        
        metrics = result["metrics"]
        assert metrics["accuracy"] > 0, "Accuracy should be positive"
        assert 0 <= metrics["accuracy"] <= 1, "Accuracy should be between 0 and 1"
        assert hasattr(result["model"], "predict"), "Model should have predict method"
    
    def test_save_and_load_model(self):
        """Test model persistence."""
        df = self.create_sample_dataset()
        X, y, _ = TrainingService.preprocess_data(df)
        result = TrainingService.train_xgboost(X, y)
        
        model_name = "test_model_v1"
        model_path = TrainingService.save_model(
            result["model"],
            result["scaler"],
            model_name
        )
        
        assert os.path.exists(model_path), "Model file should be saved"
        
        # Load model
        loaded_model, loaded_scaler = TrainingService.load_model(model_name)
        assert loaded_model is not None, "Loaded model should not be None"
        assert loaded_scaler is not None, "Loaded scaler should not be None"
    
    def test_train_and_save_complete_pipeline(self):
        """Test complete training pipeline."""
        df = self.create_sample_dataset()
        model_name = "complete_test_v1"
        
        result = TrainingService.train_and_save(df, model_name)
        
        assert result is not None, "Should return result"
        assert result["status"] == "success", "Training should succeed"
        assert result["metrics"]["accuracy"] > 0, "Should have valid metrics"
        assert os.path.exists(result["model_path"]), "Model should be saved"


class TestSHAPService:
    """Test SHAP explainability."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test models and data."""
        self.test_dir = tempfile.mkdtemp()
        TrainingService.set_models_dir(self.test_dir)
        
        # Train a sample model
        np.random.seed(42)
        n_samples = 50
        data = {
            "budget": np.random.randint(50000, 200000, n_samples),
            "duration_days": np.random.randint(30, 365, n_samples),
            "team_size": np.random.randint(3, 20, n_samples),
            "team_experience_years": np.random.uniform(1, 10, n_samples),
            "project_complexity": np.random.randint(1, 5, n_samples),
            "requirement_changes": np.random.randint(0, 10, n_samples),
            "sprint_delays": np.random.randint(0, 5, n_samples),
            "bug_count": np.random.randint(0, 50, n_samples),
            "testing_coverage": np.random.uniform(0, 100, n_samples),
            "client_involvement": np.random.uniform(0, 5, n_samples),
            "resource_availability": np.random.uniform(0, 100, n_samples),
            "customer_satisfaction": np.random.uniform(0, 5, n_samples),
            "status": np.random.randint(0, 2, n_samples)
        }
        df = pd.DataFrame(data)
        
        X, y, _ = TrainingService.preprocess_data(df)
        training_result = TrainingService.train_xgboost(X, y)
        
        self.model = training_result["model"]
        self.scaler = training_result["scaler"]
        self.X_train = X
        
        yield
        
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_explain_prediction(self):
        """Test SHAP explanation generation."""
        # Create a test instance
        test_features = self.X_train.iloc[:1].copy()
        
        result = SHAPService.explain_prediction(
            self.model,
            self.scaler,
            test_features,
            TrainingService.FEATURE_COLUMNS
        )
        
        assert result["status"] == "success", "Should generate explanation successfully"
        assert "explanations" in result, "Should contain explanations"
        
        exp = result["explanations"]
        assert "prediction_probability_success" in exp, "Should have prediction probability"
        assert "top_positive_factors" in exp, "Should have positive factors"
        assert "top_negative_factors" in exp, "Should have negative factors"
        assert "summary" in exp, "Should have summary text"
    
    def test_global_feature_importance(self):
        """Test global feature importance."""
        result = SHAPService.get_global_feature_importance(
            self.model,
            self.scaler,
            self.X_train,
            TrainingService.FEATURE_COLUMNS
        )
        
        assert result["status"] == "success", "Should calculate feature importance"
        assert "feature_importance" in result, "Should have feature importance"
        
        importance = result["feature_importance"]
        assert len(importance) > 0, "Should have features ranked"
        assert all(isinstance(f, str) for f in importance.keys()), "Features should be strings"


class TestGitHubService:
    """Test GitHub analysis."""
    
    def test_parse_github_url_https(self):
        """Test parsing HTTPS GitHub URL."""
        url = "https://github.com/owner/repo"
        result = GitHubService.parse_github_url(url)
        
        assert result is not None, "Should parse valid URL"
        assert result["owner"] == "owner", "Should extract owner"
        assert result["repo"] == "repo", "Should extract repo name"
    
    def test_parse_github_url_owner_repo(self):
        """Test parsing owner/repo format."""
        url = "owner/repo"
        result = GitHubService.parse_github_url(url)
        
        assert result is not None, "Should parse owner/repo format"
        assert result["owner"] == "owner"
        assert result["repo"] == "repo"
    
    def test_parse_github_url_git_ssh(self):
        """Test parsing git SSH format."""
        url = "git@github.com:owner/repo.git"
        result = GitHubService.parse_github_url(url)
        
        assert result is not None, "Should parse SSH format"
        assert result["owner"] == "owner"
        assert result["repo"] == "repo"
    
    def test_parse_github_url_invalid(self):
        """Test parsing invalid URL."""
        result = GitHubService.parse_github_url("invalid")
        assert result is None, "Should return None for invalid URL"
    
    def test_estimate_project_metrics(self):
        """Test GitHub metrics to project metrics conversion."""
        github_metrics = {
            "total_commits": 100,
            "contributors": 5,
            "open_issues": 10,
            "stars": 50,
            "branches": 3
        }
        
        result = GitHubService._estimate_project_metrics(github_metrics)
        
        assert result is not None, "Should estimate metrics"
        assert "sprint_delays" in result, "Should estimate sprint_delays"
        assert "team_size" in result, "Should estimate team_size"
        assert "bug_count" in result, "Should estimate bug_count"
        assert 0 <= result["sprint_delays"] <= 5, "sprint_delays should be in range"


class TestPredictionService:
    """Test unified prediction service."""
    
    def test_baseline_prediction_available(self, monkeypatch):
        """Test baseline prediction is always available."""
        metrics = {
            "budget": 100000,
            "duration_days": 180,
            "team_size": 5,
            "team_experience_years": 3,
            "project_complexity": 3,
            "requirement_changes": 2,
            "sprint_delays": 1,
            "bug_count": 15,
            "testing_coverage": 75,
            "client_involvement": 3,
            "resource_availability": 85,
            "customer_satisfaction": 4,
            "project_type": "Web"
        }
        
        monkeypatch.setattr(PredictionService, "MODELS_DIR", None)
        result = PredictionService.predict_with_both_methods(metrics)

        assert result["baseline_prediction"] is not None, "Baseline should always be available"
        assert result["ml_prediction"] is None, "ML should be None when no model is configured"
        assert result["prediction_method"] == "Baseline IF-ELSE (No trained model)"
    
    def test_determine_risk_level(self):
        """Test risk level classification."""
        assert PredictionService._determine_risk_level(20) == "Low"
        assert PredictionService._determine_risk_level(50) == "Medium"
        assert PredictionService._determine_risk_level(75) == "High"


class TestMLService:
    """Test baseline ML service."""
    
    def test_baseline_prediction_output_format(self):
        """Test baseline prediction returns correct format."""
        metrics = {
            "budget": 100000,
            "duration_days": 180,
            "team_size": 5,
            "team_experience_years": 3,
            "project_complexity": 3,
            "requirement_changes": 2,
            "sprint_delays": 1,
            "bug_count": 15,
            "testing_coverage": 75,
            "client_involvement": 3,
            "resource_availability": 85,
            "customer_satisfaction": 4
        }
        
        result = MLService.predict_single(metrics)
        
        assert "prediction" in result, "Should have prediction"
        assert "is_successful_prediction" in result, "Should have boolean flag"
        assert "success_probability" in result, "Should have success probability"
        assert "failure_probability" in result, "Should have failure probability"
        assert "risk_score" in result, "Should have risk score"
        assert "risk_level" in result, "Should have risk level"
        assert "health_score" in result, "Should have health score"
        
        assert result["prediction"] in ["Success", "Failure"], "Prediction should be Success or Failure"
        assert isinstance(result["is_successful_prediction"], bool), "Should be boolean"
        assert 0 <= result["success_probability"] <= 100, "Probability should be 0-100"
        assert 0 <= result["failure_probability"] <= 100, "Probability should be 0-100"
    
    def test_baseline_prediction_deterministic(self):
        """Test baseline prediction is deterministic."""
        metrics = {
            "budget": 100000,
            "duration_days": 180,
            "team_size": 5,
            "team_experience_years": 3,
            "project_complexity": 3,
            "requirement_changes": 2,
            "sprint_delays": 1,
            "bug_count": 15,
            "testing_coverage": 75,
            "client_involvement": 3,
            "resource_availability": 85,
            "customer_satisfaction": 4
        }
        
        result1 = MLService.predict_single(metrics)
        result2 = MLService.predict_single(metrics)
        
        assert result1["prediction"] == result2["prediction"], "Should be deterministic"
        assert result1["success_probability"] == result2["success_probability"], "Should be deterministic"


# ============================================================
# Main test runner
# ============================================================

def run_tests():
    """Run all tests."""
    import subprocess
    result = subprocess.run(
        ["pytest", __file__, "-v", "--tb=short"],
        cwd=os.path.dirname(os.path.dirname(__file__))
    )
    return result.returncode


if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)
