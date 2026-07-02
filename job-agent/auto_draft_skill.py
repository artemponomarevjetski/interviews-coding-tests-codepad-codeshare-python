#!/usr/bin/env python3
"""
AUTO-DRAFT SKILL - Generate recruiter replies for all P1 jobs

This module provides functionality to automatically generate concise,
recruiter-ready replies for all high-priority (P1) jobs in the database.
"""

import logging
from typing import Callable, List, Any, Dict

# Configure minimal logging
logger = logging.getLogger(__name__)


def auto_draft_all_p1_jobs(ask_llm_func: Callable, list_jobs_func: Callable) -> None:
    """
    Generate drafts for all P1 (highest priority) jobs.

    Args:
        ask_llm_func: Function that calls the LLM to generate a draft
        list_jobs_func: Function that retrieves jobs from the database

    Returns:
        None (prints results directly to console)
    """
    try:
        # Fetch all jobs
        rows = list_jobs_func("", 100)

        # Filter for P1 jobs that are not closed
        p1_jobs = [
            r for r in rows
            if r.get("priority") == 1 and r.get("status") != "closed"
        ]

        if not p1_jobs:
            print("✅ No P1 jobs found. All caught up!")
            return

        print(f"📝 Generating drafts for {len(p1_jobs)} P1 job(s)...")
        print("-" * 60)

        for idx, job in enumerate(p1_jobs, 1):
            job_id = job.get("id", "Unknown")
            job_title = job.get("title", "Untitled Role")
            company = job.get("company", "Unknown Company")

            print(f"\n📌 Job {idx}/{len(p1_jobs)}: #{job_id} | {company} | {job_title[:50]}...")

            try:
                draft = ask_llm_func(
                    f"Generate a concise, professional recruiter reply for job #{job_id}: {job_title} at {company}. "
                    "Include confirmation of interest, strongest skills match, availability, and a clear next-step ask.",
                    job_db_id=job_id
                )
                print(f"\n📄 Draft:\n{draft}")
            except Exception as e:
                logger.error(f"Failed to generate draft for job #{job_id}: {e}")
                print(f"❌ Error generating draft for job #{job_id}: {e}")

            print("-" * 50)

    except Exception as e:
        logger.error(f"Error in auto_draft_all_p1_jobs: {e}")
        print(f"❌ Error: {e}")


def get_p1_jobs(list_jobs_func: Callable) -> List[Any]:
    """
    Helper function to retrieve only P1 jobs.

    Args:
        list_jobs_func: Function that retrieves jobs from the database

    Returns:
        List of P1 jobs
    """
    rows = list_jobs_func("", 100)
    return [r for r in rows if r.get("priority") == 1 and r.get("status") != "closed"]


if __name__ == "__main__":
    print("This module is intended to be used with the Job Application AI Assistant.")
    print("Import it and use auto_draft_all_p1_jobs() with the appropriate functions.")
