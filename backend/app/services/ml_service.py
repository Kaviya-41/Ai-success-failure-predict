from typing import Dict, Any
import time


class MLService:
    """
    Success/Failure Decision-Making Algorithm.

    This is NOT a machine-learning model.
    It uses predefined IF-ELSE rules to determine
    whether a software project is likely to succeed or fail.
    """

    @staticmethod
    def predict_single(metrics: Dict[str, Any]) -> Dict[str, Any]:
        start_time = time.perf_counter()

        # ---------------------------------------------------------
        # Read project inputs
        # ---------------------------------------------------------

        budget = float(metrics.get("budget", 0))
        duration_days = int(metrics.get("duration_days", 0))
        team_size = int(metrics.get("team_size", 0))
        team_experience_years = float(
            metrics.get("team_experience_years", 0)
        )

        project_complexity = int(
            metrics.get("project_complexity", 1)
        )

        requirement_changes = int(
            metrics.get("requirement_changes", 0)
        )

        sprint_delays = int(
            metrics.get("sprint_delays", 0)
        )

        bug_count = int(
            metrics.get("bug_count", 0)
        )

        testing_coverage = float(
            metrics.get("testing_coverage", 0)
        )

        client_involvement = int(
            metrics.get("client_involvement", 1)
        )

        resource_availability = float(
            metrics.get("resource_availability", 0)
        )

        customer_satisfaction = int(
            metrics.get("customer_satisfaction", 1)
        )

        project_type = str(
            metrics.get("project_type", "Web")
        )

        # ---------------------------------------------------------
        # SUCCESS / FAILURE CONDITIONS
        # ---------------------------------------------------------

        success_conditions = 0
        failure_conditions = 0

        # 1. Sprint delays
        if sprint_delays <= 2:
            success_conditions += 1
        else:
            failure_conditions += 1

        # 2. Bug count
        if bug_count <= 25:
            success_conditions += 1
        else:
            failure_conditions += 1

        # 3. Testing coverage
        if testing_coverage >= 70:
            success_conditions += 1
        else:
            failure_conditions += 1

        # 4. Team experience
        if team_experience_years >= 3:
            success_conditions += 1
        else:
            failure_conditions += 1

        # 5. Resource availability
        if resource_availability >= 70:
            success_conditions += 1
        else:
            failure_conditions += 1

        # 6. Customer satisfaction
        if customer_satisfaction >= 3:
            success_conditions += 1
        else:
            failure_conditions += 1

        # 7. Client involvement
        if client_involvement >= 3:
            success_conditions += 1
        else:
            failure_conditions += 1

        # 8. Requirement changes
        if requirement_changes <= 3:
            success_conditions += 1
        else:
            failure_conditions += 1

        # 9. Project complexity
        if project_complexity <= 3:
            success_conditions += 1
        else:
            failure_conditions += 1

        # 10. Team size
        if team_size >= 3:
            success_conditions += 1
        else:
            failure_conditions += 1

        # 11. Duration
        if duration_days <= 365:
            success_conditions += 1
        else:
            failure_conditions += 1

        # 12. Budget
        if budget > 0:
            success_conditions += 1
        else:
            failure_conditions += 1

        # ---------------------------------------------------------
        # MAIN IF-ELSE DECISION
        # ---------------------------------------------------------

        total_conditions = success_conditions + failure_conditions

        success_percentage = (
            success_conditions / total_conditions
        ) * 100

        failure_percentage = (
            failure_conditions / total_conditions
        ) * 100

        # Main Success/Failure algorithm
        if success_conditions >= failure_conditions:
            is_successful = True
            prediction = "Success"
        else:
            is_successful = False
            prediction = "Failure"

        # ---------------------------------------------------------
        # Risk score
        # ---------------------------------------------------------

        risk_score = round(failure_percentage, 2)

        if risk_score <= 25:
            risk_level = "Low"
        elif risk_score <= 50:
            risk_level = "Medium"
        else:
            risk_level = "High"

        # ---------------------------------------------------------
        # Health score
        # ---------------------------------------------------------

        health_score = round(success_percentage, 2)

        # ---------------------------------------------------------
        # Confidence
        # ---------------------------------------------------------

        confidence_score = round(
            abs(success_percentage - failure_percentage),
            2
        )

        # ---------------------------------------------------------
        # Risk factors
        # ---------------------------------------------------------

        top_risk_factors = []

        if sprint_delays > 2:
            top_risk_factors.append(
                "High number of sprint delays"
            )

        if bug_count > 25:
            top_risk_factors.append(
                "High bug count"
            )

        if testing_coverage < 70:
            top_risk_factors.append(
                "Low testing coverage"
            )

        if team_experience_years < 3:
            top_risk_factors.append(
                "Low team experience"
            )

        if resource_availability < 70:
            top_risk_factors.append(
                "Low resource availability"
            )

        if customer_satisfaction < 3:
            top_risk_factors.append(
                "Low customer satisfaction"
            )

        if requirement_changes > 3:
            top_risk_factors.append(
                "Frequent requirement changes"
            )

        if project_complexity > 3:
            top_risk_factors.append(
                "High project complexity"
            )

        # ---------------------------------------------------------
        # Success factors
        # ---------------------------------------------------------

        top_success_factors = []

        if sprint_delays <= 2:
            top_success_factors.append(
                "Low sprint delays"
            )

        if bug_count <= 25:
            top_success_factors.append(
                "Controlled bug count"
            )

        if testing_coverage >= 70:
            top_success_factors.append(
                "Good testing coverage"
            )

        if team_experience_years >= 3:
            top_success_factors.append(
                "Experienced development team"
            )

        if resource_availability >= 70:
            top_success_factors.append(
                "Good resource availability"
            )

        if customer_satisfaction >= 3:
            top_success_factors.append(
                "Good customer satisfaction"
            )

        if client_involvement >= 3:
            top_success_factors.append(
                "Good client involvement"
            )

        if requirement_changes <= 3:
            top_success_factors.append(
                "Stable requirements"
            )

        # ---------------------------------------------------------
        # Recommendations
        # ---------------------------------------------------------

        recommendations = []

        if sprint_delays > 2:
            recommendations.append(
                "Reduce sprint delays by improving sprint planning."
            )

        if bug_count > 25:
            recommendations.append(
                "Reduce bugs through better testing and code reviews."
            )

        if testing_coverage < 70:
            recommendations.append(
                "Increase automated and manual testing coverage."
            )

        if team_experience_years < 3:
            recommendations.append(
                "Provide mentoring and technical training to the team."
            )

        if resource_availability < 70:
            recommendations.append(
                "Improve resource allocation and team availability."
            )

        if customer_satisfaction < 3:
            recommendations.append(
                "Increase customer communication and feedback."
            )

        if requirement_changes > 3:
            recommendations.append(
                "Improve requirement analysis and change management."
            )

        if project_complexity > 3:
            recommendations.append(
                "Break complex modules into smaller manageable tasks."
            )

        if not recommendations:
            recommendations.append(
                "Project conditions are healthy. Continue monitoring."
            )

        prediction_time_ms = (
            time.perf_counter() - start_time
        ) * 1000

        # ---------------------------------------------------------
        # Final response
        # ---------------------------------------------------------

        return {
            "is_successful_prediction": is_successful,
            "success_probability": round(
                success_percentage, 2
            ),
            "failure_probability": round(
                failure_percentage, 2
            ),
            "risk_score": risk_score,
            "risk_level": risk_level,
            "health_score": health_score,
            "confidence_score": confidence_score,
            "prediction_time_ms": round(
                prediction_time_ms, 2
            ),
            "model_algorithm": "Success/Failure IF-ELSE Decision Algorithm",
            "prediction": prediction,
            "top_risk_factors": top_risk_factors,
            "top_success_factors": top_success_factors,
            "recommendations": recommendations,

            # Useful for debugging/frontend
            "success_conditions": success_conditions,
            "failure_conditions": failure_conditions,
            "total_conditions": total_conditions,
            "project_type": project_type
        }

    @staticmethod
    def predict_project(metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compatibility method.
        """
        return MLService.predict_single(metrics)

    @staticmethod
    def preprocess_df(df):
        """Compatibility wrapper for older training endpoints."""
        from app.services.training_service import TrainingService

        X, y, _ = TrainingService.preprocess_data(df)
        return X, y

    @staticmethod
    def train_and_compare(X, y):
        """Train the default model family and return a minimal comparison payload."""
        from app.services.training_service import TrainingService

        training_result = TrainingService.train_xgboost(X, y)
        model_name = "xgboost"
        model_path = TrainingService.save_model(
            training_result["model"],
            training_result["scaler"],
            model_name,
        )

        comparison = {
            model_name: {
                "model_name": model_name,
                "algorithm": "xgboost",
                "file_path": model_path,
                "accuracy": float(training_result["metrics"]["accuracy"]),
                "precision": float(training_result["metrics"]["precision"]),
                "recall": float(training_result["metrics"]["recall"]),
                "f1_score": float(training_result["metrics"]["f1_score"]),
                "roc_auc": float(training_result["metrics"]["roc_auc"]),
            }
        }

        return {
            "best_model": model_name,
            "comparison": comparison,
        }

    @staticmethod
    def get_active_model_details():
        """Backward-compatible placeholder for legacy model metadata queries."""
        return {
            "model_name": "xgboost",
            "algorithm": "xgboost",
            "accuracy": 0.0,
        }