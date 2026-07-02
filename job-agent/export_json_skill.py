#!/usr/bin/env python3
"""
EXPORT JSON SKILL - Export job data to JSON format

This module provides functionality to export all job data from the database
to a structured JSON file for backup, analysis, or sharing.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Callable, Any, List, Dict, Optional

# Configure logging
logger = logging.getLogger(__name__)


def export_jobs_json(
    path: Path,
    list_jobs_func: Callable,
    init_db_func: Callable,
    include_metadata: bool = True
) -> None:
    """
    Export all jobs as JSON.

    Args:
        path: File path to save the JSON export
        list_jobs_func: Function that retrieves jobs from the database
        init_db_func: Function that initializes the database connection
        include_metadata: Whether to include export metadata in the output

    Returns:
        None (prints confirmation or error message)
    """
    try:
        # Initialize database
        init_db_func()

        # Fetch all jobs
        rows = list_jobs_func("", 500)

        if not rows:
            print("ℹ️ No jobs to export.")
            return

        # Convert rows to dictionaries
        data = []
        for r in rows:
            job_dict = dict(r)
            # Convert None values to empty strings for cleaner JSON
            for key, value in job_dict.items():
                if value is None:
                    job_dict[key] = ""
            data.append(job_dict)

        # Build export object
        export_obj: Dict[str, Any] = {
            "jobs": data
        }

        if include_metadata:
            export_obj["metadata"] = {
                "export_date": datetime.now().isoformat(),
                "total_jobs": len(data),
                "export_script": "export_json_skill.py",
                "version": "1.0"
            }

        # Write to file
        with path.open("w", encoding="utf-8") as f:
            json.dump(export_obj, f, indent=2, default=str)

        print(f"✅ Exported {len(data)} jobs to: {path}")

    except PermissionError:
        print(f"❌ Permission denied: Cannot write to {path}")
        logger.error(f"Permission denied: {path}")
    except json.JSONEncodeError as e:
        print(f"❌ JSON encoding error: {e}")
        logger.error(f"JSON encoding error: {e}")
    except Exception as e:
        print(f"❌ Error exporting jobs: {e}")
        logger.error(f"Error exporting jobs: {e}")


def export_jobs_json_with_timestamp(
    list_jobs_func: Callable,
    init_db_func: Callable,
    base_dir: Optional[Path] = None
) -> Path:
    """
    Export jobs to a timestamped JSON file.

    Args:
        list_jobs_func: Function that retrieves jobs from the database
        init_db_func: Function that initializes the database connection
        base_dir: Directory to save the export (defaults to current directory)

    Returns:
        Path to the created file
    """
    if base_dir is None:
        base_dir = Path.cwd()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = base_dir / f"jobs_export_{timestamp}.json"

    export_jobs_json(path, list_jobs_func, init_db_func)

    return path


if __name__ == "__main__":
    print("This module is intended to be used with the Job Application AI Assistant.")
    print("Import it and use export_jobs_json() with the appropriate functions.")
