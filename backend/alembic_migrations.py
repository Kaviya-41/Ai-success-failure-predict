"""
Database migration script to add new tables for ML upgrade.

Run this to create PredictionHistory, GitHubRepository, and ModelVersion tables.
"""

import os
import sys
from sqlalchemy import inspect
from app.core.database import Base, engine
from app.models.prediction_history import PredictionHistory, GitHubRepository, ModelVersion
from app.models.github_analysis_report import GitHubAnalysisReport
from app.models.github_analysis_quota import GitHubAnalysisQuota
from app.models import *

def run_migrations():
    """Create all new tables in the database."""
    
    print("🔧 Starting database migration...")
    print(f"Database: {engine.url}")
    
    # Get existing tables
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    print(f"\n📋 Existing tables: {existing_tables}")
    
    # Tables to create
    new_tables = {
        "prediction_history": PredictionHistory,
        "github_repositories": GitHubRepository,
        "model_versions": ModelVersion,
        "github_analysis_reports": GitHubAnalysisReport,
        "github_analysis_quotas": GitHubAnalysisQuota,
    }
    
    # Create missing tables
    created = []
    for table_name, model in new_tables.items():
        if table_name not in existing_tables:
            print(f"\n✏️  Creating table: {table_name}")
            try:
                model.__table__.create(engine, checkfirst=True)
                created.append(table_name)
                print(f"✅ Created: {table_name}")
            except Exception as e:
                print(f"❌ Error creating {table_name}: {str(e)}")
        else:
            print(f"⏭️  Table already exists: {table_name}")
    
    # Verify creation
    inspector = inspect(engine)
    final_tables = set(inspector.get_table_names())
    print(f"\n✅ Migration complete!")
    print(f"📋 Final tables: {final_tables}")
    
    # Summary
    if created:
        print(f"\n🎉 Created tables: {', '.join(created)}")
    else:
        print("\n📌 No new tables created (all already exist)")
    
    return len(created) > 0


if __name__ == "__main__":
    try:
        success = run_migrations()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n💥 Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
