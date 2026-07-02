#!/usr/bin/env python3
"""
BATCH IMPORT SKILL - Import multiple jobs from text

This module provides functionality to parse and import job data from various
text formats including JSON, SQL INSERT, CSV, and key:value blocks.
"""

import json
import re
import logging
from pathlib import Path
from typing import Any, Dict, Callable, List, Optional, Union

# Configure logging
logger = logging.getLogger(__name__)

# Constants
DEFAULT_PRIORITY = 3
DEFAULT_STATUS = "lead"
DEFAULT_PORTAL_URL = "https://ustechsolutions.com/search-vacancies/"


def batch_import_jobs_from_text(
    text: str,
    add_job_func: Optional[Callable] = None
) -> int:
    """
    Parse job data from text and insert multiple jobs.

    Supports multiple formats:
    - JSON: {"jobs": [{"company": "...", "title": "...", ...}]}
    - SQL INSERT: INSERT INTO jobs (company, title) VALUES ('...', '...')
    - CSV: company,title,location,rate
    - Key:value blocks: company: US Tech Solutions\ntitle: Data Engineer

    Args:
        text: The text to parse
        add_job_func: Optional function to add a job. If not provided,
                      will try to find it from the calling context.

    Returns:
        Number of jobs successfully imported
    """
    if add_job_func is None:
        add_job_func = _get_add_job_function()

    text = text.strip()
    if not text:
        print("⚠️ No text provided for import.")
        return 0

    inserted = 0

    # Try parsing in order of complexity
    parsers = [
        _parse_json,
        _parse_sql_insert,
        _parse_csv,
        _parse_key_value_blocks
    ]

    for parser in parsers:
        try:
            result = parser(text, add_job_func)
            if result > 0:
                inserted = result
                break
        except Exception as e:
            logger.debug(f"Parser {parser.__name__} failed: {e}")
            continue

    if inserted == 0:
        print("⚠️ No valid job data found in the input.")
        print("   Supported formats: JSON, SQL INSERT, CSV, or key:value blocks.")

    return inserted


def _get_add_job_function() -> Callable:
    """Retrieve the add_job function from the calling context."""
    try:
        from batch_import_skill import add_job as default_add_job
        return default_add_job
    except ImportError:
        import sys
        if 'add_job' in sys.modules.get('__main__', {}).__dict__:
            return sys.modules['__main__'].__dict__['add_job']
        raise RuntimeError("Could not find add_job function")


def _parse_json(text: str, add_job_func: Callable) -> int:
    """Parse JSON format: {"jobs": [...]} or [...]."""
    try:
        data = json.loads(text)

        if isinstance(data, dict) and "jobs" in data:
            data = data["jobs"]

        if not isinstance(data, list):
            return 0

        inserted = 0
        for item in data:
            if isinstance(item, dict):
                fields = _extract_fields_from_json(item)
                if fields:
                    add_job_func(fields)
                    inserted += 1

        if inserted > 0:
            print(f"✅ Imported {inserted} job(s) from JSON format.")

        return inserted

    except json.JSONDecodeError:
        return 0


def _extract_fields_from_json(item: Dict[str, Any]) -> Dict[str, Any]:
    """Extract fields from a JSON job object."""
    field_mapping = {
        "company": ["company", "Company"],
        "title": ["title", "Title"],
        "client": ["client", "Client"],
        "job_id": ["job_id", "JobID", "Job ID"],
        "source": ["source", "Source"],
        "location": ["location", "Location"],
        "work_mode": ["work_mode", "WorkMode", "Work Mode"],
        "tax_term": ["tax_term", "TaxTerm", "Tax Term"],
        "rate": ["rate", "Rate"],
        "duration": ["duration", "Duration"],
        "priority": ["priority", "Priority"],
        "status": ["status", "Status"],
        "recruiter_name": ["recruiter_name", "RecruiterName", "Recruiter"],
        "recruiter_email": ["recruiter_email", "RecruiterEmail"],
        "portal_url": ["portal_url", "PortalURL"],
        "notes": ["notes", "Notes"],
        "jd_text": ["jd_text", "JDText", "Description"],
    }

    fields = {}
    for target, keys in field_mapping.items():
        for key in keys:
            if key in item and item[key]:
                value = item[key]
                if target == "priority":
                    try:
                        value = int(value)
                    except (ValueError, TypeError):
                        value = DEFAULT_PRIORITY
                elif target == "status" and not value:
                    value = DEFAULT_STATUS
                fields[target] = value
                break

    # Set defaults for required fields
    if "priority" not in fields:
        fields["priority"] = DEFAULT_PRIORITY
    if "status" not in fields:
        fields["status"] = DEFAULT_STATUS

    return fields


def _parse_sql_insert(text: str, add_job_func: Callable) -> int:
    """Parse SQL INSERT statements."""
    pattern = re.compile(
        r"INSERT\s+INTO\s+\w+\s*\(([^)]+)\)\s*VALUES\s*\(([^)]+)\)",
        re.IGNORECASE
    )
    matches = pattern.findall(text)

    if not matches:
        return 0

    inserted = 0
    for columns_str, values_str in matches:
        columns = [c.strip().strip('"').strip("'") for c in columns_str.split(",")]
        values = [v.strip().strip('"').strip("'") for v in values_str.split(",")]

        if len(columns) != len(values):
            continue

        fields = dict(zip(columns, values))

        field_map = {
            "company": "company", "title": "title", "client": "client",
            "job_id": "job_id", "source": "source", "location": "location",
            "work_mode": "work_mode", "tax_term": "tax_term", "rate": "rate",
            "duration": "duration", "priority": "priority", "status": "status",
            "recruiter_name": "recruiter_name", "recruiter_email": "recruiter_email",
            "portal_url": "portal_url", "notes": "notes", "jd_text": "jd_text",
        }

        job_fields = {}
        for db_col, val in fields.items():
            if db_col in field_map:
                key = field_map[db_col]
                if key == "priority":
                    try:
                        val = int(val)
                    except (ValueError, TypeError):
                        val = DEFAULT_PRIORITY
                job_fields[key] = val

        if job_fields:
            if "priority" not in job_fields:
                job_fields["priority"] = DEFAULT_PRIORITY
            add_job_func(job_fields)
            inserted += 1

    if inserted > 0:
        print(f"✅ Imported {inserted} job(s) from SQL format.")

    return inserted


def _parse_csv(text: str, add_job_func: Callable) -> int:
    """Parse CSV format with header row."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    if not lines or "," not in lines[0]:
        return 0

    headers = [h.strip().lower().replace(" ", "_") for h in lines[0].split(",")]

    header_map = {
        "company": "company", "title": "title", "client": "client",
        "job_id": "job_id", "source": "source", "location": "location",
        "work_mode": "work_mode", "tax_term": "tax_term", "rate": "rate",
        "duration": "duration", "priority": "priority", "status": "status",
        "notes": "notes",
    }

    inserted = 0
    for line in lines[1:]:
        values = [v.strip() for v in line.split(",")]

        if len(values) != len(headers):
            continue

        fields = {}
        for idx, header in enumerate(headers):
            if header in header_map:
                key = header_map[header]
                val = values[idx] if idx < len(values) else ""
                if key == "priority":
                    try:
                        val = int(val)
                    except (ValueError, TypeError):
                        val = DEFAULT_PRIORITY
                if key == "status" and not val:
                    val = DEFAULT_STATUS
                fields[key] = val

        if fields:
            if "priority" not in fields:
                fields["priority"] = DEFAULT_PRIORITY
            if "status" not in fields:
                fields["status"] = DEFAULT_STATUS
            add_job_func(fields)
            inserted += 1

    if inserted > 0:
        print(f"✅ Imported {inserted} job(s) from CSV format.")

    return inserted


def _parse_key_value_blocks(text: str, add_job_func: Callable) -> int:
    """Parse key:value blocks separated by blank lines."""
    blocks = re.split(r"\n\s*\n", text)

    field_map = {
        "company": "company", "title": "title", "client": "client",
        "job_id": "job_id", "source": "source", "location": "location",
        "work_mode": "work_mode", "tax_term": "tax_term", "rate": "rate",
        "duration": "duration", "priority": "priority", "status": "status",
        "notes": "notes",
    }

    inserted = 0
    for block in blocks:
        if ":" not in block:
            continue

        fields = {}
        for line in block.splitlines():
            if ":" not in line:
                continue

            key, val = line.split(":", 1)
            key = key.strip().lower().replace(" ", "_")
            val = val.strip()

            if key in field_map:
                fkey = field_map[key]
                if fkey == "priority":
                    try:
                        val = int(val)
                    except (ValueError, TypeError):
                        val = DEFAULT_PRIORITY
                if fkey == "status" and not val:
                    val = DEFAULT_STATUS
                fields[fkey] = val

        if fields:
            if "priority" not in fields:
                fields["priority"] = DEFAULT_PRIORITY
            if "status" not in fields:
                fields["status"] = DEFAULT_STATUS
            add_job_func(fields)
            inserted += 1

    if inserted > 0:
        print(f"✅ Imported {inserted} job(s) from key:value format.")

    return inserted


if __name__ == "__main__":
    print("This module is intended to be used with the Job Application AI Assistant.")
    print("Import it and use batch_import_jobs_from_text() with the appropriate functions.")
