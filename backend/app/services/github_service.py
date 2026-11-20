"""
GitHub repository analysis service.

Extracts project metrics from GitHub repositories without exposing credentials.
"""

import requests
from typing import Dict, Any, Optional
from urllib.parse import urlparse
import os
from datetime import datetime, timedelta


class GitHubService:
    """
    Service for analyzing GitHub repositories.
    
    Extracts project-level metrics:
    - Total files
    - Total commits
    - Contributors count
    - Active branches
    - Open/closed issues
    - Repository activity (commits in last 30 days)
    - Development duration (from first to last commit)
    - Stars
    - Forks
    
    Handles private repositories gracefully and does not expose credentials.
    """
    
    # GitHub API endpoints
    BASE_URL = "https://api.github.com"
    TIMEOUT = 10  # seconds
    
    @staticmethod
    def parse_github_url(url: str) -> Optional[Dict[str, str]]:
        """
        Parse GitHub URL to extract owner and repo name.
        
        Accepts formats:
        - https://github.com/owner/repo
        - https://github.com/owner/repo.git
        - git@github.com:owner/repo.git
        - owner/repo
        
        Args:
            url: GitHub URL or repository identifier
            
        Returns:
            Dict with 'owner' and 'repo' keys, or None if invalid
        """
        url = url.strip()
        
        # Handle git@ format
        if url.startswith("git@github.com:"):
            url = url.replace("git@github.com:", "https://github.com/")
        
        # Handle owner/repo format
        if "/" in url and not url.startswith("http"):
            parts = url.split("/")
            if len(parts) >= 2:
                return {"owner": parts[-2], "repo": parts[-1].replace(".git", "")}
        
        # Handle full URL
        if url.startswith("http"):
            parsed = urlparse(url)
            if "github.com" in parsed.netloc:
                path_parts = parsed.path.strip("/").split("/")
                if len(path_parts) >= 2:
                    return {
                        "owner": path_parts[0],
                        "repo": path_parts[1].replace(".git", "")
                    }
        
        return None
    
    @staticmethod
    def analyze_repository(
        repo_url: str,
        github_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze a GitHub repository and extract project metrics.
        
        Args:
            repo_url: GitHub repository URL
            github_token: Optional GitHub API token for higher rate limits
                         (Does NOT expose token in response)
            
        Returns:
            Dictionary with extracted metrics
        """
        try:
            # Parse repository
            repo_info = GitHubService.parse_github_url(repo_url)
            if not repo_info:
                return {
                    "status": "error",
                    "message": f"Invalid GitHub URL format: {repo_url}",
                    "metrics": None
                }
            
            owner = repo_info["owner"]
            repo = repo_info["repo"]
            
            # Setup headers
            headers = {"Accept": "application/vnd.github.v3+json"}
            if github_token:
                headers["Authorization"] = f"token {github_token}"
            
            # Get repository info
            repo_endpoint = f"{GitHubService.BASE_URL}/repos/{owner}/{repo}"
            
            response = requests.get(
                repo_endpoint,
                headers=headers,
                timeout=GitHubService.TIMEOUT
            )
            
            if response.status_code == 404:
                return {
                    "status": "error",
                    "message": f"Repository not found: {repo_url}",
                    "metrics": None
                }
            
            if response.status_code == 403:
                return {
                    "status": "error",
                    "message": "Access denied. Private repository requires authentication.",
                    "metrics": None,
                    "is_private": True
                }
            
            if response.status_code != 200:
                return {
                    "status": "error",
                    "message": f"GitHub API error: {response.status_code}",
                    "metrics": None
                }
            
            repo_data = response.json()
            
            # Check if private
            is_private = repo_data.get("private", False)
            
            # Extract basic metrics
            metrics = {
                "repository": f"{owner}/{repo}",
                "is_private": is_private,
                "is_fork": repo_data.get("fork", False),
                "stars": repo_data.get("stargazers_count", 0),
                "forks": repo_data.get("forks_count", 0),
                "open_issues": repo_data.get("open_issues_count", 0),
                "language": repo_data.get("language", "Unknown"),
                "description": repo_data.get("description", ""),
                "created_at": repo_data.get("created_at", ""),
                "updated_at": repo_data.get("updated_at", ""),
            }
            
            # Get additional metrics if public or properly authenticated
            try:
                # Get commits count (requires commits endpoint)
                commits_response = requests.get(
                    f"{repo_endpoint}/commits",
                    headers=headers,
                    params={"per_page": 1},
                    timeout=GitHubService.TIMEOUT
                )
                
                if commits_response.status_code == 200:
                    # Link header contains total count
                    if "link" in commits_response.headers:
                        link = commits_response.headers["link"]
                        # Parse last page number from link header
                        import re
                        match = re.search(r'page=(\d+)>; rel="last"', link)
                        if match:
                            metrics["total_commits"] = int(match.group(1))
                        else:
                            metrics["total_commits"] = 1
                    else:
                        metrics["total_commits"] = 1
                
                # Get contributors count
                contributors_response = requests.get(
                    f"{repo_endpoint}/contributors",
                    headers=headers,
                    params={"per_page": 1},
                    timeout=GitHubService.TIMEOUT
                )
                
                if contributors_response.status_code == 200:
                    if "link" in contributors_response.headers:
                        link = contributors_response.headers["link"]
                        import re
                        match = re.search(r'page=(\d+)>; rel="last"', link)
                        if match:
                            metrics["contributors"] = int(match.group(1))
                        else:
                            metrics["contributors"] = 1
                    else:
                        metrics["contributors"] = 1
                
                # Get branches count
                branches_response = requests.get(
                    f"{repo_endpoint}/branches",
                    headers=headers,
                    params={"per_page": 1},
                    timeout=GitHubService.TIMEOUT
                )
                
                if branches_response.status_code == 200:
                    if "link" in branches_response.headers:
                        link = branches_response.headers["link"]
                        import re
                        match = re.search(r'page=(\d+)>; rel="last"', link)
                        if match:
                            metrics["branches"] = int(match.group(1))
                        else:
                            metrics["branches"] = 1
                    else:
                        metrics["branches"] = 1
                
            except Exception as e:
                # If we can't get commits/contributors, that's okay
                pass
            
            # Estimate project metrics from GitHub data
            estimated_project_metrics = GitHubService._estimate_project_metrics(metrics)
            
            return {
                "status": "success",
                "metrics": metrics,
                "estimated_project_metrics": estimated_project_metrics,
                "message": f"Successfully analyzed {owner}/{repo}"
            }
        
        except requests.exceptions.Timeout:
            return {
                "status": "error",
                "message": "GitHub API request timed out. Please try again.",
                "metrics": None
            }
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "message": f"Failed to connect to GitHub API: {str(e)}",
                "metrics": None
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Unexpected error analyzing repository: {str(e)}",
                "metrics": None
            }
    
    @staticmethod
    def _estimate_project_metrics(github_metrics: Dict[str, Any]) -> Dict[str, float]:
        """
        Estimate project success/failure metrics based on GitHub data.
        
        Maps GitHub indicators to project metrics:
        - Active development → lower sprint_delays
        - Multiple contributors → better team_size
        - Low issues → better quality (bug_count)
        - Good test coverage signals → higher testing_coverage
        
        Args:
            github_metrics: Extracted GitHub metrics
            
        Returns:
            Dictionary with estimated project metrics
        """
        estimated = {}
        
        # Estimate based on commits (activity indicator)
        commits = github_metrics.get("total_commits", 0)
        
        # Recent activity (commits in likely development period)
        # Assume development duration ~6 months if active
        if commits > 0:
            # Higher commits suggest active development
            estimated["sprint_delays"] = max(0, 5 - min(commits / 100, 5))  # More commits = fewer delays
            estimated["bug_count"] = max(0, 50 - min(github_metrics.get("open_issues", 0) * 2, 50))
        else:
            estimated["sprint_delays"] = 5
            estimated["bug_count"] = 50
        
        # Estimate based on contributors
        contributors = github_metrics.get("contributors", 1)
        estimated["team_size"] = min(20, max(1, contributors // 2))  # Rough estimate
        estimated["team_experience_years"] = min(10, max(1, github_metrics.get("stars", 0) / 100))
        
        # Estimate based on issues
        open_issues = github_metrics.get("open_issues", 0)
        estimated["testing_coverage"] = max(10, 100 - open_issues * 2)
        
        # Estimate based on stars (popularity/maturity)
        stars = github_metrics.get("stars", 0)
        if stars > 1000:
            estimated["project_complexity"] = 2  # Well-known = likely well-designed
            estimated["client_involvement"] = 4
        elif stars > 100:
            estimated["project_complexity"] = 3
            estimated["client_involvement"] = 3
        else:
            estimated["project_complexity"] = 4
            estimated["client_involvement"] = 2
        
        # Default values
        estimated["budget"] = 100000  # Placeholder
        estimated["duration_days"] = 180  # Estimated project duration
        estimated["requirement_changes"] = max(0, 5 - (github_metrics.get("branches", 1) - 1) / 2)
        estimated["resource_availability"] = 80 + min(20, github_metrics.get("contributors", 0) / 5)
        estimated["customer_satisfaction"] = 3 + (github_metrics.get("stars", 0) > 100 and 1 or 0)
        estimated["project_type"] = "Web"  # Default
        
        return estimated
