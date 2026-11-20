from sqlalchemy import Column, Date, Integer, String

from app.core.database import Base


class GitHubAnalysisQuota(Base):
    __tablename__ = "github_analysis_quotas"

    scope_type = Column(String(16), primary_key=True)
    scope_id = Column(Integer, primary_key=True)
    usage_date = Column(Date, primary_key=True)
    usage_count = Column(Integer, nullable=False, default=0)
