import base64
import re
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Dict, List, Optional
from urllib.parse import quote, urlparse

import requests

from app.core.config import settings
from app.services.ml_service import MLService


class GitHubAPIError(ValueError):
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


class GitHubAnalysisService:
    """Transparent GitHub repository risk analysis built on top of the existing rule engine."""

    BASE_URL = "https://api.github.com"
    REQUEST_TIMEOUT_SECONDS = 15
    SOURCE_SAMPLE_LIMIT = 3
    DEPENDENCY_SAMPLE_LIMIT = 5

    @staticmethod
    def parse_repository_url(raw_url: str) -> Optional[Dict[str, str]]:
        value = (raw_url or "").strip()
        if not value:
            return None

        if value.startswith("git@github.com:"):
            value = value.replace("git@github.com:", "https://github.com/")

        if "/" in value and "://" not in value:
            parts = [part for part in value.split("/") if part]
            if len(parts) != 2:
                return None
            owner, repo = parts
        else:
            try:
                parsed = urlparse(value)
                invalid_url = (
                    parsed.scheme not in {"http", "https"}
                    or parsed.hostname != "github.com"
                    or parsed.username
                    or parsed.password
                    or parsed.port is not None
                    or parsed.query
                    or parsed.fragment
                )
            except ValueError:
                return None
            if invalid_url:
                return None

            path_parts = [part for part in parsed.path.strip("/").split("/") if part]
            if len(path_parts) != 2:
                return None
            owner, repo = path_parts

        if repo.lower().endswith(".git"):
            repo = repo[:-4]

        if (
            not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]{0,38}", owner)
            or not re.fullmatch(r"[A-Za-z0-9._-]{1,100}", repo)
            or repo in {".", ".."}
        ):
            return None
        return {"owner": owner, "repo": repo}

    @staticmethod
    def _header_value(headers: Any, key: str) -> Optional[str]:
        for header_name, value in headers.items():
            if str(header_name).lower() == key.lower():
                return str(value)
        return None

    @staticmethod
    def _get_headers(github_token: Optional[str] = None) -> Dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "RiskPilot-App",
        }
        token = github_token or settings.GITHUB_TOKEN
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    @staticmethod
    def _get_total_count_from_link(headers: Dict[str, Any]) -> Optional[int]:
        link_header = GitHubAnalysisService._header_value(headers, "link") or ""
        match = re.search(r"page=(\d+)>; rel=\"last\"", link_header)
        if match:
            return int(match.group(1))
        return None

    @staticmethod
    def _request_json(
        url: str,
        github_token: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        allow_missing: bool = False,
        allow_empty_repository: bool = False,
        return_headers: bool = False,
    ) -> Any:
        response = requests.get(
            url,
            headers=GitHubAnalysisService._get_headers(github_token),
            params=params,
            timeout=GitHubAnalysisService.REQUEST_TIMEOUT_SECONDS,
        )

        if response.status_code == 401:
            raise GitHubAPIError(
                "GitHub rejected the configured credentials. Check the GITHUB_TOKEN setting."
            )
        if response.status_code in {403, 429}:
            remaining = GitHubAnalysisService._header_value(response.headers, "X-RateLimit-Remaining")
            body = (getattr(response, "text", "") or "").lower()
            if response.status_code == 429 or remaining == "0" or "rate limit" in body:
                reset = GitHubAnalysisService._header_value(response.headers, "X-RateLimit-Reset")
                retry_after = GitHubAnalysisService._header_value(response.headers, "Retry-After")
                wait_until = None
                if retry_after:
                    try:
                        reset_time = datetime.now(timezone.utc) + timedelta(
                            seconds=max(0, int(retry_after))
                        )
                    except ValueError:
                        try:
                            reset_time = parsedate_to_datetime(retry_after)
                            if reset_time.tzinfo is None:
                                reset_time = reset_time.replace(tzinfo=timezone.utc)
                        except (TypeError, ValueError, OverflowError):
                            reset_time = None
                    if reset_time is not None:
                        wait_until = reset_time.astimezone(timezone.utc).strftime("%H:%M UTC")
                if wait_until is None and reset:
                    try:
                        wait_until = datetime.fromtimestamp(
                            int(reset), tz=timezone.utc
                        ).strftime("%H:%M UTC")
                    except (OverflowError, OSError, ValueError):
                        wait_until = None
                message = (
                    "GitHub's hourly API rate limit was reached. This is separate "
                    "from the app's limit of 10 analyses per day."
                )
                if wait_until:
                    message += f" GitHub says you can retry after {wait_until}."
                if not settings.GITHUB_TOKEN and not github_token:
                    message += (
                        " Configure GITHUB_TOKEN in backend/.env and restart the "
                        "backend to increase GitHub's API allowance."
                    )
                raise GitHubAPIError(message, status_code=429)
            raise GitHubAPIError(
                "GitHub denied access to this repository. It may be private or unavailable.",
                status_code=403,
            )
        if response.status_code == 404:
            if allow_missing:
                return (None, response.headers) if return_headers else None
            raise ValueError("GitHub repository could not be found. Please check the repository URL.")
        if response.status_code == 409 and allow_empty_repository:
            return ([], response.headers) if return_headers else []
        try:
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException as exc:
            raise GitHubAPIError(
                f"GitHub API request failed with status {response.status_code}."
            ) from exc
        return (payload, response.headers) if return_headers else payload

    @staticmethod
    def _paginated_count(
        url: str,
        github_token: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        allow_empty_repository: bool = False,
    ) -> int:
        page, headers = GitHubAnalysisService._request_json(
            url,
            github_token,
            params={**(params or {}), "per_page": 1},
            allow_empty_repository=allow_empty_repository,
            return_headers=True,
        )
        if not isinstance(page, list):
            return 0
        linked_count = GitHubAnalysisService._get_total_count_from_link(headers)
        return linked_count if linked_count is not None else len(page)

    @staticmethod
    def _decode_content(payload: Any) -> str:
        if not isinstance(payload, dict) or payload.get("encoding") != "base64":
            return ""
        encoded = payload.get("content")
        if not isinstance(encoded, str):
            return ""
        try:
            return base64.b64decode(encoded).decode("utf-8", errors="replace")
        except (ValueError, base64.binascii.Error):
            return ""

    @staticmethod
    def _is_test_path(path: str) -> bool:
        normalized = path.lower()
        name = normalized.rsplit("/", 1)[-1]
        return (
            "/test/" in f"/{normalized}/"
            or "/tests/" in f"/{normalized}/"
            or "/__tests__/" in f"/{normalized}/"
            or name.startswith("test_")
            or name.endswith((
                "_test.py", ".test.cjs", ".test.js", ".test.jsx", ".test.mjs",
                ".test.ts", ".test.tsx", ".spec.cjs", ".spec.js", ".spec.mjs",
                ".spec.ts", ".spec.tsx",
            ))
        )

    @staticmethod
    def _dependency_kind(path: str) -> Optional[str]:
        name = path.rsplit("/", 1)[-1].lower()
        lockfiles = {
            "cargo.lock", "composer.lock", "gemfile.lock", "go.sum",
            "package-lock.json", "pnpm-lock.yaml", "pipfile.lock",
            "poetry.lock", "yarn.lock",
        }
        manifests = {
            "cargo.toml", "composer.json", "gemfile", "go.mod",
            "package.json", "pipfile", "pom.xml", "pyproject.toml",
            "requirements.txt",
        }
        if name in lockfiles:
            return "lockfile"
        if name in manifests or (name.startswith("requirements") and name.endswith(".txt")):
            return "manifest"
        return None

    @staticmethod
    def _calculate_dependency_risk(
        manifest_contents: List[str], has_lockfile: bool
    ) -> tuple[float, int]:
        unpinned_count = sum(
            len(re.findall(
                r"(?im)(?:==\s*\*|:\s*['\"]?(?:\*|latest)['\"]?|>=\s*\d)",
                content,
            ))
            for content in manifest_contents
        )
        if not manifest_contents:
            return 45.0, unpinned_count
        risk = 25.0 if has_lockfile else 55.0
        risk += min(unpinned_count * 5, 35)
        return GitHubAnalysisService._clamp(risk), unpinned_count

    @staticmethod
    def build_rule_prediction(metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Feed repository-derived indicators into the existing IF-ELSE engine."""
        project_metrics = GitHubAnalysisService.to_project_metrics(metrics)
        baseline = MLService.predict_single(project_metrics)
        prediction = str(baseline["prediction"]).upper()

        risk_factors = list(baseline["top_risk_factors"])
        if metrics.get("code_quality", 0) < 50:
            risk_factors.append(
                "Source-file structure or maintenance markers indicate code-quality risk"
            )
        if metrics.get("dependency_risk", 0) >= 50:
            risk_factors.append(
                "Dependency manifests lack lockfiles or contain unpinned versions"
            )
        if metrics.get("test_files", 0) == 0:
            risk_factors.append("No test files were found in the repository tree")

        positive_factors = list(baseline["top_success_factors"])
        if metrics.get("documentation", 0) >= 60:
            positive_factors.append("README documentation contains useful project guidance")
        if metrics.get("test_files", 0) > 0 and metrics.get("ci_present"):
            positive_factors.append("Test files and CI workflows are both present")
        if metrics.get("dependency_risk", 100) < 50 and metrics.get("dependency_files"):
            positive_factors.append(
                "Dependency files are present with relatively low version-management risk"
            )

        recommendations = list(baseline["recommendations"])
        if metrics.get("code_quality", 0) < 50:
            recommendations.append(
                "Review large source files and resolve TODO/FIXME markers in the sampled source files."
            )
        if metrics.get("dependency_risk", 0) >= 50:
            recommendations.append(
                "Pin dependency versions and commit the ecosystem's lockfile; run dependency vulnerability checks separately."
            )
        if metrics.get("test_files", 0) == 0:
            recommendations.append(
                "Add automated test files for critical repository functionality."
            )
        if metrics.get("documentation", 0) < 60:
            recommendations.append(
                "Expand the README with setup, usage, testing, and contribution instructions."
            )

        return {
            "prediction": prediction,
            "success_probability": baseline["success_probability"],
            "failure_probability": baseline["failure_probability"],
            "risk_score": baseline["risk_score"],
            "health_score": baseline["health_score"],
            "risk_level": baseline["risk_level"],
            "risk_factors": risk_factors or ["No major risk indicators detected at this time"],
            "positive_factors": positive_factors or [
                "Repository activity is stable but should be monitored"
            ],
            "recommendations": recommendations or [
                "Continue the current delivery rhythm and keep monitoring issue, review, and testing discipline."
            ],
            "recovery_plan": GitHubAnalysisService._build_recovery_plan(metrics),
            "motivation": GitHubAnalysisService._build_motivation() if prediction == "SUCCESS" else "",
            "engine_metrics": project_metrics,
            "success_conditions": baseline["success_conditions"],
            "failure_conditions": baseline["failure_conditions"],
            "total_conditions": baseline["total_conditions"],
        }

    @staticmethod
    def _safe_float(value: Any, default: float = 0.0) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
        return max(minimum, min(maximum, value))

    @staticmethod
    def _parse_bool(value: Any) -> bool:
        return bool(value)

    @staticmethod
    def _build_repository_summary(repository_data: Dict[str, Any]) -> Dict[str, Any]:
        created_at = repository_data.get("created_at")
        updated_at = repository_data.get("updated_at")
        language = repository_data.get("language") or "Unknown"

        return {
            "repository_name": repository_data.get("full_name") or repository_data.get("name"),
            "owner": repository_data.get("owner", {}).get("login") if isinstance(repository_data.get("owner"), dict) else "unknown",
            "description": repository_data.get("description") or "No description provided.",
            "primary_language": language,
            "created_at": created_at,
            "last_updated_at": updated_at,
            "stars": repository_data.get("stargazers_count", 0),
            "forks": repository_data.get("forks_count", 0),
            "open_issues": repository_data.get("open_issues_count", 0),
            "watchers": repository_data.get("watchers_count", 0),
            "private": repository_data.get("private", False),
            "default_branch": repository_data.get("default_branch") or "main",
            "size_kb": repository_data.get("size", 0),
            "homepage": repository_data.get("homepage") or "",
        }

    @staticmethod
    def _build_risk_factors(metrics: Dict[str, Any]) -> List[str]:
        risk_factors: List[str] = []
        if metrics.get("activity_score", 50) < 50:
            risk_factors.append("Low recent commit activity")
        if metrics.get("contributor_activity", 50) < 50:
            risk_factors.append("Low contributor activity")
        if metrics.get("issue_resolution", 50) < 50:
            risk_factors.append("Many unresolved issues")
        if metrics.get("pr_activity", 50) < 50:
            risk_factors.append("Stale pull request activity")
        if metrics.get("documentation", 50) < 50:
            risk_factors.append("Weak project documentation")
        if metrics.get("testing_ci", 50) < 50:
            risk_factors.append("Limited testing and CI indicators")
        if metrics.get("recent_activity", 50) < 50:
            risk_factors.append("Long periods of inactivity")
        if metrics.get("development_consistency", 50) < 50:
            risk_factors.append("Inconsistent development rhythm")
        if not risk_factors:
            risk_factors.append("No major risk indicators detected at this time")
        return risk_factors

    @staticmethod
    def _build_positive_factors(metrics: Dict[str, Any]) -> List[str]:
        positives: List[str] = []
        if metrics.get("activity_score", 50) >= 60:
            positives.append("Consistent repository activity")
        if metrics.get("contributor_activity", 50) >= 60:
            positives.append("Healthy contribution pattern")
        if metrics.get("issue_resolution", 50) >= 60:
            positives.append("Issues are being actively managed")
        if metrics.get("pr_activity", 50) >= 60:
            positives.append("Regular pull request activity")
        if metrics.get("documentation", 50) >= 60:
            positives.append("Documentation is present and maintained")
        if metrics.get("testing_ci", 50) >= 60:
            positives.append("Testing and CI practices are visible")
        if metrics.get("recent_activity", 50) >= 60:
            positives.append("Project remains actively maintained")
        if not positives:
            positives.append("Repository activity is stable but should be monitored")
        return positives

    @staticmethod
    def _build_recommendations(metrics: Dict[str, Any]) -> List[str]:
        recs: List[str] = []

        if metrics.get("activity_score", 50) < 50:
            recs.append("Create a short development plan and maintain a consistent commit schedule.")
        if metrics.get("issue_resolution", 50) < 50:
            recs.append("Prioritize and close critical issues before adding new features.")
        if metrics.get("pr_activity", 50) < 50:
            recs.append("Review pending pull requests and establish a clear review and merge process.")
        if metrics.get("contributor_activity", 50) < 50:
            recs.append("Distribute tasks among available contributors and define clear ownership for key workstreams.")
        if metrics.get("documentation", 50) < 50:
            recs.append("Improve the README and add setup, usage, and contribution instructions.")
        if metrics.get("testing_ci", 50) < 50:
            recs.append("Add automated tests for critical functionality and integrate them into the development workflow.")
        if metrics.get("recent_activity", 50) < 50:
            recs.append("Increase project visibility by scheduling short, regular maintenance and delivery cycles.")
        if not recs:
            recs.append("Continue the current delivery rhythm and keep monitoring issue, review, and testing discipline.")
        return recs

    @staticmethod
    def _build_recovery_plan(metrics: Dict[str, Any]) -> List[str]:
        plan: List[str] = []
        if metrics.get("issue_resolution", 50) < 60:
            plan.append("Priority 1: Resolve critical open issues and set a clear triage process.")
        if metrics.get("activity_score", 50) < 60:
            plan.append("Priority 2: Increase development activity with a realistic weekly commit and review cadence.")
        if metrics.get("pr_activity", 50) < 60:
            plan.append("Priority 3: Review pending pull requests and remove review bottlenecks.")
        if metrics.get("testing_ci", 50) < 60:
            plan.append("Priority 4: Improve automated testing and CI coverage for core workflows.")
        if metrics.get("documentation", 50) < 60:
            plan.append("Priority 5: Update project documentation and onboarding guidance.")
        if not plan:
            plan.append("Priority 1: Maintain momentum through steady delivery and issue tracking.")
        return plan

    @staticmethod
    def _build_motivation() -> str:
        return (
            "Great work! The repository shows healthy development activity and a positive delivery pattern. "
            "Keep maintaining the current development discipline and continue monitoring project risks."
        )

    @staticmethod
    def to_project_metrics(metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Map repository indicators to the legacy engine's project input fields."""
        activity = float(metrics.get("activity_score", 50))
        contributors = float(metrics.get("contributor_activity", 50))
        testing = float(metrics.get("testing_ci", 50))
        issue_resolution = float(metrics.get("issue_resolution", 50))
        maintenance = float(metrics.get("maintenance", 50))
        documentation = float(metrics.get("documentation", 50))
        recent_activity = float(metrics.get("recent_activity", 50))
        development_consistency = float(metrics.get("development_consistency", 50))
        commit_frequency = float(metrics.get("commit_frequency", 50))

        project_metrics = {
            "budget": max(20000, min(300000, (activity * 1400) + (maintenance * 600))),
            "duration_days": max(60, min(365, int((100 - recent_activity) * 4 + 120))),
            "team_size": max(2, min(12, int((contributors / 100) * 8 + 2))),
            "team_experience_years": round(max(1.0, min(10.0, (maintenance + development_consistency) / 20.0)), 2),
            "project_complexity": max(1, min(5, int((100 - maintenance) / 25) + 2)),
            "requirement_changes": max(0, int((100 - development_consistency) / 15)),
            "sprint_delays": max(0, int((100 - activity) / 18)),
            "bug_count": max(0, int((100 - issue_resolution) * 1.5)),
            "testing_coverage": round(testing, 2),
            "client_involvement": max(1, min(5, int((documentation + recent_activity) / 40))),
            "resource_availability": round(min(100.0, contributors + (commit_frequency / 2))),
            "customer_satisfaction": max(1, min(5, int((maintenance + documentation + recent_activity) / 60))),
            "project_type": "Web",
        }
        source_pressure = max(0, int(metrics.get("source_files", 0) / 100))
        language_pressure = max(0, int(metrics.get("language_count", 0)) - 1)
        dependency_pressure = int(float(metrics.get("dependency_risk", 0)) >= 70)
        project_metrics["project_complexity"] = max(
            1,
            min(
                5,
                project_metrics["project_complexity"]
                + min(2, source_pressure + language_pressure + dependency_pressure),
            ),
        )

        quality_risk = max(0.0, 60.0 - float(metrics.get("code_quality", 100)))
        sampled_maintenance_markers = min(
            10, int(metrics.get("todo_fixme_count_sampled", 0))
        )
        project_metrics["bug_count"] += int(quality_risk / 10) + sampled_maintenance_markers
        return project_metrics

    @staticmethod
    def build_prediction(metrics: Dict[str, Any]) -> Dict[str, Any]:
        values = [
            float(metrics.get("activity_score", 50)),
            float(metrics.get("contributor_activity", 50)),
            float(metrics.get("commit_frequency", 50)),
            float(metrics.get("issue_resolution", 50)),
            float(metrics.get("pr_activity", 50)),
            float(metrics.get("maintenance", 50)),
            float(metrics.get("documentation", 50)),
            float(metrics.get("testing_ci", 50)),
            float(metrics.get("recent_activity", 50)),
            float(metrics.get("development_consistency", 50)),
        ]

        health_score = sum(values) / len(values)
        success_probability = round(health_score, 2)
        failure_probability = round(100 - success_probability, 2)
        risk_score = round(100 - health_score, 2)

        if risk_score <= 25:
            risk_level = "Low"
        elif risk_score <= 50:
            risk_level = "Medium"
        else:
            risk_level = "High"

        prediction = "SUCCESS" if health_score >= 60 else "FAILURE"

        risk_factors = GitHubAnalysisService._build_risk_factors(metrics)
        positive_factors = GitHubAnalysisService._build_positive_factors(metrics)
        recommendations = GitHubAnalysisService._build_recommendations(metrics)
        recovery_plan = GitHubAnalysisService._build_recovery_plan(metrics)
        motivation = GitHubAnalysisService._build_motivation() if prediction == "SUCCESS" else ""

        return {
            "prediction": prediction,
            "success_probability": round(success_probability, 2),
            "failure_probability": round(failure_probability, 2),
            "risk_score": round(risk_score, 2),
            "health_score": round(health_score, 2),
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "positive_factors": positive_factors,
            "recommendations": recommendations,
            "recovery_plan": recovery_plan,
            "motivation": motivation,
            "engine_metrics": GitHubAnalysisService.to_project_metrics(metrics),
        }

    @staticmethod
    def analyze_repository(repository_url: str, github_token: Optional[str] = None) -> Dict[str, Any]:
        parsed = GitHubAnalysisService.parse_repository_url(repository_url)
        if not parsed:
            raise ValueError("Please enter a valid GitHub repository URL.")

        owner = parsed["owner"]
        repo = parsed["repo"]
        repository_endpoint = f"{GitHubAnalysisService.BASE_URL}/repos/{owner}/{repo}"
        try:
            repository_data = GitHubAnalysisService._request_json(repository_endpoint, github_token)
            if repository_data.get("private"):
                raise GitHubAPIError(
                    "This repository cannot be accessed with the current GitHub configuration.",
                    status_code=403,
                )

            languages = GitHubAnalysisService._request_json(
                f"{repository_endpoint}/languages", github_token
            )
            contributors_total = GitHubAnalysisService._paginated_count(
                f"{repository_endpoint}/contributors", github_token
            )
            commit_count = GitHubAnalysisService._paginated_count(
                f"{repository_endpoint}/commits",
                github_token,
                allow_empty_repository=True,
            )

            open_pulls = GitHubAnalysisService._paginated_count(
                f"{repository_endpoint}/pulls",
                github_token,
                params={"state": "open"},
            )
            closed_pulls = GitHubAnalysisService._paginated_count(
                f"{repository_endpoint}/pulls",
                github_token,
                params={"state": "closed"},
            )
            closed_issues_including_pulls = GitHubAnalysisService._paginated_count(
                f"{repository_endpoint}/issues",
                github_token,
                params={"state": "closed"},
            )
            closed_issues = max(0, closed_issues_including_pulls - closed_pulls)
            open_issues = max(
                0, int(repository_data.get("open_issues_count", 0)) - open_pulls
            )

            recent_cutoff = datetime.now(timezone.utc).timestamp() - 30 * 24 * 60 * 60
            recent_commits = GitHubAnalysisService._request_json(
                f"{repository_endpoint}/commits",
                github_token,
                params={
                    "since": datetime.fromtimestamp(
                        recent_cutoff, tz=timezone.utc
                    ).isoformat(),
                    "per_page": 100,
                },
                allow_empty_repository=True,
            )
            recent_commit_count = len(recent_commits) if isinstance(recent_commits, list) else 0

            repository_summary = GitHubAnalysisService._build_repository_summary(repository_data)
            default_branch = repository_summary["default_branch"]
            tree_payload = GitHubAnalysisService._request_json(
                f"{repository_endpoint}/git/trees/{quote(default_branch, safe='')}?recursive=1",
                github_token,
                allow_missing=True,
                allow_empty_repository=True,
            )
            tree = tree_payload.get("tree", []) if isinstance(tree_payload, dict) else []
            tree_files = [
                item for item in tree
                if isinstance(item, dict) and item.get("type") == "blob"
            ]
            tree_paths = [str(item.get("path", "")) for item in tree_files]

            source_extensions = {
                ".c", ".cc", ".cpp", ".cs", ".css", ".go", ".h", ".hpp",
                ".java", ".js", ".jsx", ".kt", ".php", ".py", ".rb",
                ".rs", ".scala", ".scss", ".sh", ".sql", ".swift", ".ts",
                ".tsx", ".vue",
            }
            test_paths = [path for path in tree_paths if GitHubAnalysisService._is_test_path(path)]
            source_files = [
                item for item in tree_files
                if item.get("path", "").lower().endswith(tuple(source_extensions))
                and not GitHubAnalysisService._is_test_path(str(item.get("path", "")))
            ]
            dependency_paths = [
                (path, GitHubAnalysisService._dependency_kind(path))
                for path in tree_paths
                if GitHubAnalysisService._dependency_kind(path)
            ]
            dependency_paths.sort(key=lambda item: (item[1] != "manifest", item[0].lower()))
            sampled_dependency_paths = dependency_paths[:GitHubAnalysisService.DEPENDENCY_SAMPLE_LIMIT]
            dependency_contents: List[str] = []
            for path, kind in sampled_dependency_paths:
                if kind != "manifest":
                    continue
                content_data = GitHubAnalysisService._request_json(
                    f"{repository_endpoint}/contents/{quote(path, safe='/')}",
                    github_token,
                    allow_missing=True,
                )
                dependency_contents.append(GitHubAnalysisService._decode_content(content_data))

            sampled_source_paths = sorted(
                source_files, key=lambda item: str(item.get("path", "")).lower()
            )[:GitHubAnalysisService.SOURCE_SAMPLE_LIMIT]
            todo_fixme_count = 0
            sampled_source_lines = 0
            for item in sampled_source_paths:
                path = str(item.get("path", ""))
                source_data = GitHubAnalysisService._request_json(
                    f"{repository_endpoint}/contents/{quote(path, safe='/')}",
                    github_token,
                    allow_missing=True,
                )
                source_text = GitHubAnalysisService._decode_content(source_data)
                sampled_source_lines += len(source_text.splitlines())
                todo_fixme_count += len(
                    re.findall(r"\b(?:TODO|FIXME|XXX)\b", source_text, flags=re.IGNORECASE)
                )

            readme_data = GitHubAnalysisService._request_json(
                f"{repository_endpoint}/readme", github_token, allow_missing=True
            )
            readme_text = GitHubAnalysisService._decode_content(readme_data)
            readme_present = isinstance(readme_data, dict)
            readme_sections = len(re.findall(r"(?m)^\s{0,3}#{1,6}\s+\S", readme_text))
            readme_has_setup = bool(re.search(r"\b(install|setup|usage|getting started)\b", readme_text, re.I))

            tree_lower = {path.lower() for path in tree_paths}
            ci_present = any(
                path.startswith(".github/workflows/")
                or path.startswith(".circleci/")
                or path in {".travis.yml", "azure-pipelines.yml", "bitbucket-pipelines.yml"}
                for path in tree_lower
            )
            tests_present = bool(test_paths)

            repository_summary = GitHubAnalysisService._build_repository_summary(repository_data)
            now = datetime.now(timezone.utc)
            created_at = repository_data.get("created_at")
            updated_at = repository_data.get("updated_at")

            def to_dt(value: Optional[str]) -> Optional[datetime]:
                if not value:
                    return None
                try:
                    return datetime.fromisoformat(value.replace("Z", "+00:00"))
                except ValueError:
                    return None

            created_dt = to_dt(created_at)
            updated_dt = to_dt(updated_at)
            days_since_update = (now - (updated_dt or now)).days if updated_dt else 0
            days_since_creation = (now - (created_dt or now)).days if created_dt else 0

            total_issues = open_issues + closed_issues
            issue_resolution = (
                closed_issues / total_issues * 100 if total_issues else 100.0
            )
            total_prs = open_pulls + closed_pulls
            pr_activity = closed_pulls / total_prs * 100 if total_prs else 50.0
            commit_frequency_score = GitHubAnalysisService._clamp(
                recent_commit_count * 10 + (100 - min(days_since_update, 100))
            )
            maintenance_score = GitHubAnalysisService._clamp(
                100 - min(days_since_update, 180) * (100 / 180)
            )
            activity_score = GitHubAnalysisService._clamp(
                recent_commit_count * 8 + contributors_total * 5 + maintenance_score * 0.25
            )
            contribution_score = GitHubAnalysisService._clamp(
                contributors_total * 12 + recent_commit_count * 2
            )
            documentation_score = 20.0 if not readme_present else GitHubAnalysisService._clamp(
                35 + min(len(readme_text) / 20, 35)
                + min(readme_sections * 5, 20)
                + (10 if readme_has_setup else 0)
            )
            source_count = len(source_files)
            test_count = len(test_paths)
            test_ratio = test_count / max(1, source_count)
            testing_ci_score = GitHubAnalysisService._clamp(
                min(test_ratio / 0.1, 1) * 60 + (40 if ci_present else 0)
            )
            recent_activity_score = GitHubAnalysisService._clamp(
                100 - min(days_since_update, 180) * (100 / 180)
                + min(recent_commit_count, 20) * 2
            )
            development_consistency_score = GitHubAnalysisService._clamp(
                (commit_frequency_score + maintenance_score) / 2
            )
            large_source_files = sum(
                1 for item in source_files if int(item.get("size", 0) or 0) >= 100_000
            )
            source_sample_count = len(sampled_source_paths)
            code_quality_score = (
                GitHubAnalysisService._clamp(
                    100
                    - large_source_files / max(1, source_count) * 50
                    - min(todo_fixme_count * 2, 30)
                )
                if source_count and source_sample_count
                else (30.0 if source_count else 0.0)
            )
            has_lockfile = any(kind == "lockfile" for _, kind in dependency_paths)
            dependency_risk, unpinned_dependency_count = (
                GitHubAnalysisService._calculate_dependency_risk(
                    dependency_contents, has_lockfile
                )
            )
            languages = languages if isinstance(languages, dict) else {}

            metrics = {
                "activity_score": round(activity_score, 2),
                "contributor_activity": round(contribution_score, 2),
                "commit_frequency": round(commit_frequency_score, 2),
                "issue_resolution": round(issue_resolution, 2),
                "pr_activity": round(pr_activity, 2),
                "maintenance": round(maintenance_score, 2),
                "documentation": round(documentation_score, 2),
                "testing_ci": round(testing_ci_score, 2),
                "recent_activity": round(recent_activity_score, 2),
                "development_consistency": round(development_consistency_score, 2),
                "days_since_update": days_since_update,
                "days_since_creation": days_since_creation,
                "contributors": contributors_total,
                "commits": commit_count,
                "recent_commits_30d": recent_commit_count,
                "open_pull_requests": open_pulls,
                "closed_pull_requests": closed_pulls,
                "open_issues": open_issues,
                "closed_issues": closed_issues,
                "languages": languages,
                "language_count": len(languages),
                "source_files": source_count,
                "test_files": test_count,
                "source_test_ratio": round(source_count / max(1, test_count), 2),
                "source_files_sampled": source_sample_count,
                "sampled_source_lines": sampled_source_lines,
                "todo_fixme_count_sampled": todo_fixme_count,
                "large_source_files": large_source_files,
                "code_quality": round(code_quality_score, 2),
                "dependency_files": [path for path, _ in dependency_paths],
                "lockfile_present": has_lockfile,
                "unpinned_dependency_count_sampled": unpinned_dependency_count,
                "dependency_risk": round(dependency_risk, 2),
                "readme_present": readme_present,
                "readme_characters": len(readme_text),
                "readme_sections": readme_sections,
                "readme_has_setup_guidance": readme_has_setup,
                "tests_present": tests_present,
                "ci_present": ci_present,
                "repository_tree_truncated": bool(
                    tree_payload.get("truncated", False)
                    if isinstance(tree_payload, dict)
                    else False
                ),
                "analysis_limits": [
                    f"Inspected up to {GitHubAnalysisService.SOURCE_SAMPLE_LIMIT} source files for TODO/FIXME markers.",
                    f"Inspected up to {GitHubAnalysisService.DEPENDENCY_SAMPLE_LIMIT} dependency files.",
                    "Dependency risk measures version pinning and lockfile signals; it is not a vulnerability scan.",
                    "Repository signals are mapped to the existing project-input IF-ELSE rules; business-only inputs remain estimates.",
                ],
            }

            return {
                "repository": repository_summary,
                "metrics": metrics,
                "analysis_status": "success",
                "status": "success",
                "message": "Repository analysis completed successfully.",
            }
        except GitHubAPIError:
            raise
        except requests.Timeout as exc:
            raise GitHubAPIError(
                "GitHub did not respond before the analysis timed out. Please try again.",
                status_code=504,
            ) from exc
        except requests.RequestException as exc:
            raise GitHubAPIError(
                "Unable to connect to GitHub. Please try again shortly."
            ) from exc
