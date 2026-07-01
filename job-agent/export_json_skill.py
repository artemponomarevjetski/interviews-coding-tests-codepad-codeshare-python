# ---------------------------------------------------------------------------
# EXPORT JSON SKILL - job-agent/export_json_skill.py
# ---------------------------------------------------------------------------

import json
from pathlib import Path

def export_jobs_json(path: Path, list_jobs_func, init_db_func) -> None:
    """Export all jobs as JSON."""
    init_db_func()
    rows = list_jobs_func("", 500)
    if not rows:
        print("No jobs to export.")
        return
    data = []
    for r in rows:
        data.append(dict(r))
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
    print(f"✅ Exported {len(rows)} jobs to {path}")
