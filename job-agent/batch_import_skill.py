# ---------------------------------------------------------------------------
# BATCH IMPORT SKILL - job-agent/batch_import_skill.py
# ---------------------------------------------------------------------------

import json
import re
from pathlib import Path
from typing import Any, Dict, Callable

def batch_import_jobs_from_text(text: str, add_job_func: Callable = None) -> int:
    """
    Parses job data from a text block and inserts multiple jobs.
    Supports: JSON, SQL INSERT, CSV, key:value blocks.
    
    Args:
        text: The text to parse
        add_job_func: Optional function to add a job (for backward compatibility)
    """
    # If add_job_func is provided, use it; otherwise import from main
    if add_job_func is None:
        # Try to get add_job from the calling context
        try:
            from batch_import_skill import add_job as default_add_job
            add_job_func = default_add_job
        except ImportError:
            # If we can't import, we'll try to get it from the globals
            import sys
            if 'add_job' in sys.modules.get('__main__').__dict__:
                add_job_func = sys.modules.get('__main__').__dict__['add_job']
            else:
                raise RuntimeError("Could not find add_job function")
    
    text = text.strip()
    inserted = 0

    # Try JSON
    try:
        data = json.loads(text)
        if isinstance(data, dict) and "jobs" in data:
            data = data["jobs"]
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    fields = {
                        "company": item.get("company", item.get("Company", "")),
                        "title": item.get("title", item.get("Title", "")),
                        "client": item.get("client", item.get("Client", "")),
                        "job_id": item.get("job_id", item.get("JobID", item.get("Job ID", ""))),
                        "source": item.get("source", item.get("Source", "Batch Import")),
                        "location": item.get("location", item.get("Location", "")),
                        "work_mode": item.get("work_mode", item.get("WorkMode", item.get("Work Mode", ""))),
                        "tax_term": item.get("tax_term", item.get("TaxTerm", item.get("Tax Term", "W2"))),
                        "rate": item.get("rate", item.get("Rate", "")),
                        "duration": item.get("duration", item.get("Duration", "")),
                        "priority": int(item.get("priority", item.get("Priority", 3))),
                        "status": item.get("status", item.get("Status", "lead")),
                        "recruiter_name": item.get("recruiter_name", item.get("RecruiterName", item.get("Recruiter", ""))),
                        "recruiter_email": item.get("recruiter_email", item.get("RecruiterEmail", "")),
                        "portal_url": item.get("portal_url", item.get("PortalURL", "https://ustechsolutions.com/search-vacancies/")),
                        "notes": item.get("notes", item.get("Notes", "")),
                        "jd_text": item.get("jd_text", item.get("JDText", item.get("Description", ""))),
                    }
                    fields = {k: v for k, v in fields.items() if v}
                    add_job_func(fields)
                    inserted += 1
            return inserted
    except json.JSONDecodeError:
        pass

    # Try SQL INSERT statements
    insert_pattern = re.compile(r"INSERT\s+INTO\s+\w+\s*\(([^)]+)\)\s*VALUES\s*\(([^)]+)\)", re.IGNORECASE)
    matches = insert_pattern.findall(text)

    if matches:
        for columns_str, values_str in matches:
            columns = [c.strip().strip('"').strip("'") for c in columns_str.split(",")]
            values = [v.strip().strip('"').strip("'") for v in values_str.split(",")]
            if len(columns) == len(values):
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
                            try: val = int(val)
                            except: val = 3
                        job_fields[key] = val
                if job_fields:
                    add_job_func(job_fields)
                    inserted += 1
        return inserted

    # Try CSV
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if lines and "," in lines[0]:
        headers = [h.strip().lower().replace(" ", "_") for h in lines[0].split(",")]
        header_map = {
            "company": "company", "title": "title", "client": "client",
            "job_id": "job_id", "source": "source", "location": "location",
            "work_mode": "work_mode", "tax_term": "tax_term", "rate": "rate",
            "duration": "duration", "priority": "priority", "status": "status",
            "notes": "notes",
        }
        for line in lines[1:]:
            values = [v.strip() for v in line.split(",")]
            if len(values) == len(headers):
                fields = {}
                for idx, header in enumerate(headers):
                    if header in header_map:
                        key = header_map[header]
                        val = values[idx] if idx < len(values) else ""
                        if key == "priority":
                            try: val = int(val)
                            except: val = 3
                        fields[key] = val
                if fields:
                    add_job_func(fields)
                    inserted += 1
        return inserted

    # Try key:value blocks
    blocks = re.split(r"\n\s*\n", text)
    for block in blocks:
        if ":" in block:
            fields = {}
            for line in block.splitlines():
                if ":" in line:
                    key, val = line.split(":", 1)
                    key = key.strip().lower().replace(" ", "_")
                    val = val.strip()
                    field_map = {
                        "company": "company", "title": "title", "client": "client",
                        "job_id": "job_id", "source": "source", "location": "location",
                        "work_mode": "work_mode", "tax_term": "tax_term", "rate": "rate",
                        "duration": "duration", "priority": "priority", "status": "status",
                        "notes": "notes",
                    }
                    if key in field_map:
                        fkey = field_map[key]
                        if fkey == "priority":
                            try: val = int(val)
                            except: val = 3
                        fields[fkey] = val
            if fields:
                add_job_func(fields)
                inserted += 1

    return inserted
