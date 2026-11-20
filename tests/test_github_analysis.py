import base64
from datetime import datetime, timedelta, timezone
import sys
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from app.api.endpoints.github import (
    GitHubAnalysisRequest,
    analyze_github_repository,
    get_github_analysis_report,
    list_github_analysis_reports,
)
from app.core.database import Base
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember
from app.services.github_analysis_service import GitHubAnalysisService
from app.services.github_analysis_service import GitHubAPIError
from app.services.github_analysis_quota import consume_github_analysis_quota
from app.services.workspace_access import WorkspaceAccess


class FakeGitHubResponse:
    def __init__(self, payload, headers=None, status_code=200, text=""):
        self.payload = payload
        self.headers = headers or {}
        self.status_code = status_code
        self.text = text

    def json(self):
        return self.payload

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests

            raise requests.HTTPError(f"status {self.status_code}")


def test_valid_repository_url():
    repo = GitHubAnalysisService.parse_repository_url("https://github.com/microsoft/vscode")
    assert repo is not None
    assert repo["owner"] == "microsoft"
    assert repo["repo"] == "vscode"


def test_invalid_repository_url():
    repo = GitHubAnalysisService.parse_repository_url("https://example.com/project")
    assert repo is None


def test_repository_url_rejects_noncanonical_hosts_and_paths():
    assert GitHubAnalysisService.parse_repository_url(
        "https://github.com.evil.test/owner/repo"
    ) is None
    assert GitHubAnalysisService.parse_repository_url(
        "https://github.com/owner/repo/issues"
    ) is None
    assert GitHubAnalysisService.parse_repository_url(
        "https://github.com/owner/repo?tab=readme"
    ) is None
    assert GitHubAnalysisService.parse_repository_url(
        "https://user@github.com/owner/repo"
    ) is None
    assert GitHubAnalysisService.parse_repository_url(
        "owner/repo.git"
    ) == {"owner": "owner", "repo": "repo"}


def test_dependency_risk_reports_lockfile_and_unpinned_versions():
    risk_with_lock, unpinned_with_lock = GitHubAnalysisService._calculate_dependency_risk(
        ["requests>=2.0\npackage: latest"], has_lockfile=True
    )
    risk_without_lock, _ = GitHubAnalysisService._calculate_dependency_risk(
        ["requests>=2.0\npackage: latest"], has_lockfile=False
    )

    assert unpinned_with_lock > 0
    assert risk_with_lock < risk_without_lock


def test_repository_prediction_uses_existing_if_else_engine():
    metrics = {
        "activity_score": 80,
        "contributor_activity": 70,
        "commit_frequency": 75,
        "issue_resolution": 80,
        "pr_activity": 75,
        "maintenance": 80,
        "documentation": 85,
        "testing_ci": 80,
        "recent_activity": 90,
        "development_consistency": 78,
        "code_quality": 80,
        "dependency_risk": 20,
        "test_files": 12,
        "dependency_files": ["requirements.txt", "poetry.lock"],
        "ci_present": True,
    }

    decision = GitHubAnalysisService.build_rule_prediction(metrics)
    expected = GitHubAnalysisService.to_project_metrics(metrics)
    from app.services.ml_service import MLService

    baseline = MLService.predict_single(expected)
    assert decision["prediction"] == baseline["prediction"].upper()
    assert decision["success_probability"] == baseline["success_probability"]

    at_risk_mapping = GitHubAnalysisService.to_project_metrics({
        **metrics,
        "code_quality": 20,
        "dependency_risk": 90,
        "todo_fixme_count_sampled": 3,
        "source_files": 250,
        "language_count": 4,
    })
    assert at_risk_mapping["bug_count"] > expected["bug_count"]
    assert at_risk_mapping["project_complexity"] > expected["project_complexity"]


def test_github_rate_limit_explains_daily_cap_and_token_setup(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "GITHUB_TOKEN", None)
    response = FakeGitHubResponse(
        {"message": "API rate limit exceeded"},
        headers={"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "1793731200"},
        status_code=403,
        text="API rate limit exceeded",
    )
    with patch(
        "app.services.github_analysis_service.requests.get",
        return_value=response,
    ):
        try:
            GitHubAnalysisService._request_json("https://api.github.com/repos/owner/repo")
        except GitHubAPIError as exc:
            assert exc.status_code == 429
            assert "hourly API rate limit" in str(exc)
            assert "separate from the app's limit of 10 analyses per day" in str(exc)
            assert "GITHUB_TOKEN in backend/.env" in str(exc)
            assert "retry after" in str(exc)
        else:
            raise AssertionError("Rate limiting should be surfaced to the caller")


def test_retry_after_seconds_are_shown_as_utc_time():
    response = FakeGitHubResponse(
        {"message": "API rate limit exceeded"},
        headers={"Retry-After": "30"},
        status_code=429,
        text="API rate limit exceeded",
    )
    with patch(
        "app.services.github_analysis_service.requests.get",
        return_value=response,
    ):
        try:
            GitHubAnalysisService._request_json("https://api.github.com/repos/owner/repo")
        except GitHubAPIError as exc:
            assert exc.status_code == 429
            assert "retry after" in str(exc)
            assert "30." not in str(exc)
        else:
            raise AssertionError("Rate limiting should be surfaced to the caller")


def test_github_token_from_settings_is_used_for_api_requests(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "GITHUB_TOKEN", "test-token")

    headers = GitHubAnalysisService._get_headers()

    assert headers["Authorization"] == "Bearer test-token"


def test_github_analysis_quota_counts_failed_attempts_and_blocks_the_eleventh():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    db = sessionmaker(bind=engine)()
    user = User(email="quota-owner@example.test", hashed_password="test-hash")
    db.add(user)
    db.commit()
    workspace = Workspace(name="Quota workspace", created_by=user.id)
    db.add(workspace)
    db.commit()
    access = WorkspaceAccess(workspace_id=workspace.id, role="owner")

    try:
        with patch.object(
            GitHubAnalysisService,
            "analyze_repository",
            side_effect=ValueError("GitHub request failed"),
        ) as analyze:
            for _ in range(10):
                try:
                    analyze_github_repository(
                        GitHubAnalysisRequest(
                            repository_url="https://github.com/owner/repo"
                        ),
                        db=db,
                        current_user=user,
                        access=access,
                    )
                except HTTPException as exc:
                    assert exc.status_code == 400
                else:
                    raise AssertionError("The failed GitHub request should be reported")

            try:
                analyze_github_repository(
                    GitHubAnalysisRequest(
                        repository_url="https://github.com/owner/repo"
                    ),
                    db=db,
                    current_user=user,
                    access=access,
                )
            except HTTPException as exc:
                assert exc.status_code == 429
                assert "limit reached" in exc.detail.lower()
                assert int(exc.headers["Retry-After"]) > 0
            else:
                raise AssertionError("The eleventh analysis should be rate limited")

            assert analyze.call_count == 10
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def test_github_analysis_quota_is_per_user_and_workspace_and_resets_daily():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    db = sessionmaker(bind=engine)()
    now = datetime(2026, 11, 3, 12, tzinfo=timezone.utc)

    try:
        for _ in range(10):
            consume_github_analysis_quota(db, user_id=1, workspace_id=1, now=now)

        for user_id, workspace_id in ((2, 1), (1, 2)):
            try:
                consume_github_analysis_quota(
                    db,
                    user_id=user_id,
                    workspace_id=workspace_id,
                    now=now,
                )
            except HTTPException as exc:
                assert exc.status_code == 429
            else:
                raise AssertionError("The exhausted user or workspace should be limited")

        consume_github_analysis_quota(
            db,
            user_id=2,
            workspace_id=1,
            now=now + timedelta(days=1),
        )
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def test_repository_analysis_uses_live_api_payloads_for_repository_indicators():
    now = datetime.now(timezone.utc).isoformat()
    encoded_readme = base64.b64encode(
        b"# Overview\n\nInstall and usage instructions."
    ).decode()
    encoded_source = base64.b64encode(
        b"def run():\n    # TODO: add validation\n    return True\n"
    ).decode()
    encoded_dependencies = base64.b64encode(
        b'{"dependencies":{"example":"*"}}'
    ).decode()

    def fake_get(url, headers, params, timeout):
        if url.endswith("/repos/owner/repo"):
            return FakeGitHubResponse({
                "full_name": "owner/repo",
                "name": "repo",
                "owner": {"login": "owner"},
                "language": "Python",
                "created_at": now,
                "updated_at": now,
                "open_issues_count": 3,
                "default_branch": "main",
                "stargazers_count": 0,
                "forks_count": 0,
                "private": False,
            })
        if url.endswith("/languages"):
            return FakeGitHubResponse({"Python": 2000, "TypeScript": 1000})
        if url.endswith("/contributors"):
            return FakeGitHubResponse(
                [{"login": "one"}],
                {"Link": '<https://api.github.com?page=2>; rel="last"'},
            )
        if url.endswith("/commits") and params.get("since"):
            return FakeGitHubResponse([{}, {}])
        if url.endswith("/commits"):
            return FakeGitHubResponse(
                [{}],
                {"Link": '<https://api.github.com?page=42>; rel="last"'},
            )
        if url.endswith("/pulls") and params.get("state") == "open":
            return FakeGitHubResponse([{}])
        if url.endswith("/pulls") and params.get("state") == "closed":
            return FakeGitHubResponse(
                [{}, {}],
                {"Link": '<https://api.github.com?page=2>; rel="last"'},
            )
        if url.endswith("/issues"):
            return FakeGitHubResponse(
                [{}, {}],
                {"Link": '<https://api.github.com?page=4>; rel="last"'},
            )
        if "/git/trees/" in url:
            return FakeGitHubResponse({"tree": [
                {"path": "README.md", "type": "blob", "size": 80},
                {"path": "src/app.py", "type": "blob", "size": 80},
                {"path": "tests/test_app.py", "type": "blob", "size": 40},
                {"path": "package.json", "type": "blob", "size": 40},
                {"path": "package-lock.json", "type": "blob", "size": 200},
                {"path": ".github/workflows/ci.yml", "type": "blob", "size": 30},
            ]})
        if url.endswith("/contents/package.json"):
            return FakeGitHubResponse({"encoding": "base64", "content": encoded_dependencies})
        if url.endswith("/contents/src/app.py"):
            return FakeGitHubResponse({"encoding": "base64", "content": encoded_source})
        if url.endswith("/readme"):
            return FakeGitHubResponse({"encoding": "base64", "content": encoded_readme})
        raise AssertionError(f"Unexpected GitHub API request: {url}")

    with patch("app.services.github_analysis_service.requests.get", side_effect=fake_get):
        result = GitHubAnalysisService.analyze_repository(
            "https://github.com/owner/repo"
        )

    metrics = result["metrics"]
    assert result["status"] == "success"
    assert metrics["commits"] == 42
    assert metrics["contributors"] == 2
    assert metrics["open_issues"] == 2
    assert metrics["closed_issues"] == 2
    assert metrics["source_files"] == 1
    assert metrics["test_files"] == 1
    assert metrics["languages"] == {"Python": 2000, "TypeScript": 1000}
    assert metrics["todo_fixme_count_sampled"] == 1
    assert metrics["lockfile_present"] is True
    assert metrics["unpinned_dependency_count_sampled"] == 1


def test_analysis_reports_are_saved_and_workspace_scoped():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    db = session_factory()
    user = User(email="report-owner@example.test", hashed_password="test-hash", role="member")
    db.add(user)
    db.commit()
    workspace = Workspace(name="Report workspace", created_by=user.id)
    db.add(workspace)
    db.commit()
    db.add(WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role="owner"))
    db.commit()
    access = WorkspaceAccess(workspace_id=workspace.id, role="owner")
    metrics = {
        "activity_score": 80,
        "contributor_activity": 70,
        "commit_frequency": 75,
        "issue_resolution": 80,
        "pr_activity": 75,
        "maintenance": 80,
        "documentation": 85,
        "testing_ci": 80,
        "recent_activity": 90,
        "development_consistency": 78,
        "code_quality": 80,
        "dependency_risk": 20,
        "test_files": 12,
        "dependency_files": ["requirements.txt", "poetry.lock"],
        "ci_present": True,
    }
    repository_result = {
        "status": "success",
        "repository": {
            "repository_name": "owner/repo",
            "owner": "owner",
        },
        "metrics": metrics,
    }

    try:
        with patch.object(
            GitHubAnalysisService,
            "analyze_repository",
            return_value=repository_result,
        ):
            result = analyze_github_repository(
                GitHubAnalysisRequest(repository_url="https://github.com/owner/repo"),
                db=db,
                current_user=user,
                access=access,
            )

        assert result["report_id"] > 0
        assert result["prediction"] in {"SUCCESS", "FAILURE"}
        summaries = list_github_analysis_reports(
            limit=20,
            search=None,
            prediction=None,
            db=db,
            access=access,
        )
        assert len(summaries["reports"]) == 1
        saved = get_github_analysis_report(
            result["report_id"], db=db, access=access
        )
        assert saved["metrics"] == metrics

        stranger = User(
            email="stranger@example.test",
            hashed_password="test-hash",
            role="member",
        )
        db.add(stranger)
        db.commit()
        stranger_workspace = Workspace(name="Stranger workspace", created_by=stranger.id)
        db.add(stranger_workspace)
        db.commit()
        db.add(
            WorkspaceMember(
                workspace_id=stranger_workspace.id,
                user_id=stranger.id,
                role="owner",
            )
        )
        db.commit()
        stranger_access = WorkspaceAccess(
            workspace_id=stranger_workspace.id,
            role="owner",
        )
        try:
            get_github_analysis_report(
                result["report_id"], db=db, access=stranger_access
            )
        except HTTPException as exc:
            assert exc.status_code == 404
        else:
            raise AssertionError("A user must not retrieve another user's report")
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def test_predict_healthy_activity():
    metrics = {
        "activity_score": 90,
        "contributor_activity": 85,
        "commit_frequency": 80,
        "issue_resolution": 82,
        "pr_activity": 76,
        "maintenance": 88,
        "documentation": 75,
        "testing_ci": 80,
        "recent_activity": 90,
        "development_consistency": 87,
    }
    result = GitHubAnalysisService.build_prediction(metrics)
    assert result["prediction"] == "SUCCESS"
    assert result["success_probability"] >= 60
    assert result["failure_probability"] <= 40


def test_predict_risky_activity():
    metrics = {
        "activity_score": 15,
        "contributor_activity": 20,
        "commit_frequency": 10,
        "issue_resolution": 18,
        "pr_activity": 12,
        "maintenance": 12,
        "documentation": 20,
        "testing_ci": 15,
        "recent_activity": 10,
        "development_consistency": 18,
    }
    result = GitHubAnalysisService.build_prediction(metrics)
    assert result["prediction"] == "FAILURE"
    assert result["risk_score"] >= 50
    assert result["health_score"] <= 50


def test_recommendations_are_dynamic():
    metrics = {
        "activity_score": 15,
        "contributor_activity": 18,
        "commit_frequency": 12,
        "issue_resolution": 20,
        "pr_activity": 17,
        "maintenance": 10,
        "documentation": 15,
        "testing_ci": 12,
        "recent_activity": 10,
        "development_consistency": 14,
    }
    result = GitHubAnalysisService.build_prediction(metrics)
    assert any("commit" in rec.lower() for rec in result["recommendations"])
    assert any("issue" in rec.lower() for rec in result["recommendations"])
    assert result["motivation"] == ""
