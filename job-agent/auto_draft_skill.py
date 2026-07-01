# ---------------------------------------------------------------------------
# AUTO-DRAFT SKILL - job-agent/auto_draft_skill.py
# ---------------------------------------------------------------------------

def auto_draft_all_p1_jobs(ask_llm_func, list_jobs_func) -> None:
    """Generate drafts for all P1 jobs."""
    rows = list_jobs_func("", 100)
    p1_jobs = [r for r in rows if r["priority"] == 1 and r["status"] != "closed"]
    
    if not p1_jobs:
        print("No P1 jobs found.")
        return
    
    print(f"📝 Generating drafts for {len(p1_jobs)} P1 jobs...")
    for job in p1_jobs:
        print(f"\n--- Job #{job['id']}: {job['title']} ---")
        draft = ask_llm_func(
            f"Generate a concise recruiter reply for job #{job['id']}.",
            job_db_id=job["id"]
        )
        print(draft)
        print("\n" + "-" * 50)
