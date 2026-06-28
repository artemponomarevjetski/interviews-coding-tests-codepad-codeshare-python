#!/usr/bin/env python3
"""
JOB APPLICATION AI ASSISTANT

A local, interactive assistant for:
- job-application tracking in SQLite
- recruiter/email text processing
- recruiter reply and follow-up generation
- safe browser-assisted Gmail and job-portal workflows
- US Tech / JobDiva portal support

Security model:
- Never stores, prints, or asks for portal/Gmail passwords.
- Browser login is manual. The script opens Chrome/Chromium and pauses.
- Session cookies may be stored under ./portal_sessions/ if Playwright is used.
- Do not commit .env, portal_sessions/, jobs.db, or exported emails.
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import os
import re
import shlex
import sqlite3
import subprocess
import sys
import textwrap
import urllib.parse
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

try:
    from openai import OpenAI
except Exception:
    OpenAI = None  # type: ignore


APP_NAME = "Job Application AI Assistant"
APP_ROOT = Path.cwd()
DB_PATH = APP_ROOT / "jobs.db"
OUTPUT_DIR = APP_ROOT / "outputs"
EMAIL_DIR = APP_ROOT / "emails"
DOC_DIR = APP_ROOT / "documents"
PORTAL_SESSION_DIR = APP_ROOT / "portal_sessions"

DEFAULT_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")
MAX_CONTEXT_CHARS = int(os.environ.get("JOB_AGENT_MAX_CONTEXT_CHARS", "70000"))

SAFE_DIRS = [OUTPUT_DIR, EMAIL_DIR, DOC_DIR, PORTAL_SESSION_DIR]

INSTRUCTION_FILES = [
    "instructions.jobs.md",
    "instructions.ustech.md",
    "candidate_profile.md",
]


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def ensure_dirs() -> None:
    for d in SAFE_DIRS:
        d.mkdir(exist_ok=True)


def now_iso() -> str:
    return dt.datetime.now().replace(microsecond=0).isoformat()


def today() -> str:
    return dt.date.today().isoformat()


def print_header(title: str) -> None:
    print("\n" + "=" * 88)
    print(title)
    print("=" * 88)


def print_box(text: str) -> None:
    print("\n" + "-" * 88)
    print(text.strip())
    print("-" * 88 + "\n")


def read_text(path: Path, limit: Optional[int] = None) -> str:
    try:
        data = path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return ""
    if limit is not None:
        return data[:limit]
    return data


def write_text(path: Path, data: str) -> None:
    path.parent.mkdir(exist_ok=True, parents=True)
    path.write_text(data, encoding="utf-8")


def slugify(value: str, max_len: int = 80) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-")
    return value[:max_len] or "item"


def truncate(text: str, n: int) -> str:
    if len(text) <= n:
        return text
    return text[:n] + "\n\n...[TRUNCATED]..."


def parse_env_file(path: Path = APP_ROOT / ".env") -> Dict[str, str]:
    env: Dict[str, str] = {}
    if not path.exists():
        return env
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        if k:
            env[k] = v
    return env


def load_api_key() -> Optional[str]:
    """
    Accepts several names because Codex CLI / OpenAI scripts are often configured differently.
    Preferred: OPENAI_API_KEY.
    Also accepted: CODEX_API_KEY, OPENAI_CODEX_API_KEY.
    """
    env_file = parse_env_file()
    merged = dict(os.environ)
    merged.update(env_file)

    for name in [
        "OPENAI_API_KEY",
        "CODEX_API_KEY",
        "OPENAI_CODEX_API_KEY",
        "OPENAI_API_KEY_CODEX",
    ]:
        val = merged.get(name)
        if val:
            os.environ.setdefault("OPENAI_API_KEY", val)
            return val
    return None


def make_client() -> Any:
    if OpenAI is None:
        raise RuntimeError("openai package is not installed. Run: pip install openai")
    key = load_api_key()
    if not key:
        raise RuntimeError(
            "No API key found. Put OPENAI_API_KEY=... in .env. "
            "If your key is named CODEX_API_KEY, this script will also accept that."
        )
    return OpenAI(api_key=key)


# ---------------------------------------------------------------------------
# SQLite database
# ---------------------------------------------------------------------------

SCHEMA = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company TEXT NOT NULL DEFAULT '',
    title TEXT NOT NULL DEFAULT '',
    client TEXT NOT NULL DEFAULT '',
    job_id TEXT NOT NULL DEFAULT '',
    source TEXT NOT NULL DEFAULT '',
    location TEXT NOT NULL DEFAULT '',
    work_mode TEXT NOT NULL DEFAULT '',
    tax_term TEXT NOT NULL DEFAULT '',
    rate TEXT NOT NULL DEFAULT '',
    duration TEXT NOT NULL DEFAULT '',
    priority INTEGER NOT NULL DEFAULT 3,
    status TEXT NOT NULL DEFAULT 'lead',
    recruiter_name TEXT NOT NULL DEFAULT '',
    recruiter_email TEXT NOT NULL DEFAULT '',
    portal_url TEXT NOT NULL DEFAULT '',
    jd_text TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company TEXT NOT NULL DEFAULT '',
    name TEXT NOT NULL DEFAULT '',
    email TEXT NOT NULL DEFAULT '',
    phone TEXT NOT NULL DEFAULT '',
    role TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'active',
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER,
    company TEXT NOT NULL DEFAULT '',
    contact_email TEXT NOT NULL DEFAULT '',
    contact_name TEXT NOT NULL DEFAULT '',
    channel TEXT NOT NULL DEFAULT '',
    direction TEXT NOT NULL DEFAULT '',
    subject TEXT NOT NULL DEFAULT '',
    body TEXT NOT NULL DEFAULT '',
    occurred_at TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT '',
    FOREIGN KEY(job_id) REFERENCES jobs(id)
);

CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL,
    submitted_on TEXT NOT NULL DEFAULT '',
    submitted_via TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'planned',
    confirmation TEXT NOT NULL DEFAULT '',
    next_action TEXT NOT NULL DEFAULT '',
    next_action_due TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL DEFAULT '',
    FOREIGN KEY(job_id) REFERENCES jobs(id)
);

CREATE TABLE IF NOT EXISTS portal_accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    portal_key TEXT NOT NULL DEFAULT '',
    company TEXT NOT NULL DEFAULT '',
    portal_url TEXT NOT NULL DEFAULT '',
    username TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'unknown',
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_type TEXT NOT NULL DEFAULT '',
    label TEXT NOT NULL DEFAULT '',
    path TEXT NOT NULL DEFAULT '',
    safe_for_application INTEGER NOT NULL DEFAULT 0,
    safe_for_onboarding INTEGER NOT NULL DEFAULT 0,
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL DEFAULT ''
);
"""


def db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = db()
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()


def upsert_contact(company: str, name: str, email: str, phone: str = "", role: str = "", notes: str = "") -> None:
    init_db()
    conn = db()
    existing = conn.execute("SELECT id FROM contacts WHERE lower(email)=lower(?)", (email,)).fetchone()
    ts = now_iso()
    if existing:
        conn.execute(
            """
            UPDATE contacts
            SET company=?, name=?, phone=?, role=?, notes=?, updated_at=?
            WHERE id=?
            """,
            (company, name, phone, role, notes, ts, existing["id"]),
        )
    else:
        conn.execute(
            """
            INSERT INTO contacts(company, name, email, phone, role, notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (company, name, email, phone, role, notes, ts, ts),
        )
    conn.commit()
    conn.close()


def add_job(fields: Dict[str, Any]) -> int:
    init_db()
    conn = db()
    ts = now_iso()
    clean = {
        "company": fields.get("company", ""),
        "title": fields.get("title", ""),
        "client": fields.get("client", ""),
        "job_id": fields.get("job_id", ""),
        "source": fields.get("source", ""),
        "location": fields.get("location", ""),
        "work_mode": fields.get("work_mode", ""),
        "tax_term": fields.get("tax_term", ""),
        "rate": fields.get("rate", ""),
        "duration": fields.get("duration", ""),
        "priority": int(fields.get("priority", 3) or 3),
        "status": fields.get("status", "lead"),
        "recruiter_name": fields.get("recruiter_name", ""),
        "recruiter_email": fields.get("recruiter_email", ""),
        "portal_url": fields.get("portal_url", ""),
        "jd_text": fields.get("jd_text", ""),
        "notes": fields.get("notes", ""),
        "created_at": fields.get("created_at", ts),
        "updated_at": ts,
    }
    cur = conn.execute(
        """
        INSERT INTO jobs(
            company, title, client, job_id, source, location, work_mode, tax_term,
            rate, duration, priority, status, recruiter_name, recruiter_email,
            portal_url, jd_text, notes, created_at, updated_at
        )
        VALUES (
            :company, :title, :client, :job_id, :source, :location, :work_mode, :tax_term,
            :rate, :duration, :priority, :status, :recruiter_name, :recruiter_email,
            :portal_url, :jd_text, :notes, :created_at, :updated_at
        )
        """,
        clean,
    )
    conn.commit()
    jid = int(cur.lastrowid)
    conn.close()
    return jid


def update_job_status(job_db_id: int, status: str, notes: str = "") -> None:
    init_db()
    conn = db()
    row = conn.execute("SELECT notes FROM jobs WHERE id=?", (job_db_id,)).fetchone()
    if not row:
        print(f"⚠️ No job with id={job_db_id}")
        conn.close()
        return
    merged_notes = row["notes"] or ""
    if notes:
        merged_notes += f"\n[{today()}] {notes}"
    conn.execute(
        "UPDATE jobs SET status=?, notes=?, updated_at=? WHERE id=?",
        (status, merged_notes, now_iso(), job_db_id),
    )
    conn.commit()
    conn.close()


def get_job(job_db_id: int) -> Optional[sqlite3.Row]:
    init_db()
    conn = db()
    row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_db_id,)).fetchone()
    conn.close()
    return row


def list_jobs(filter_text: str = "", limit: int = 50) -> List[sqlite3.Row]:
    init_db()
    conn = db()
    if filter_text:
        like = f"%{filter_text.lower()}%"
        rows = conn.execute(
            """
            SELECT * FROM jobs
            WHERE lower(company || ' ' || title || ' ' || client || ' ' || job_id || ' ' || recruiter_email || ' ' || status) LIKE ?
            ORDER BY priority ASC, updated_at DESC, id DESC
            LIMIT ?
            """,
            (like, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM jobs ORDER BY priority ASC, updated_at DESC, id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    conn.close()
    return rows


def db_summary_text() -> str:
    init_db()
    conn = db()
    counts = {}
    for table in ["jobs", "contacts", "interactions", "applications", "portal_accounts", "documents"]:
        counts[table] = conn.execute(f"SELECT count(*) AS n FROM {table}").fetchone()["n"]
    by_status = conn.execute("SELECT status, count(*) AS n FROM jobs GROUP BY status ORDER BY n DESC").fetchall()
    top_jobs = conn.execute(
        """
        SELECT id, company, title, client, job_id, status, priority, recruiter_email
        FROM jobs ORDER BY priority ASC, updated_at DESC, id DESC LIMIT 10
        """
    ).fetchall()
    conn.close()

    lines = ["Database summary:", ""]
    for k, v in counts.items():
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("Jobs by status:")
    for r in by_status:
        lines.append(f"- {r['status']}: {r['n']}")
    lines.append("")
    lines.append("Top jobs:")
    for r in top_jobs:
        lines.append(
            f"- #{r['id']} P{r['priority']} {r['company']} | {r['title']} | "
            f"client={r['client']} | job_id={r['job_id']} | status={r['status']} | {r['recruiter_email']}"
        )
    return "\n".join(lines)


def export_jobs_csv(path: Path) -> None:
    init_db()
    conn = db()
    rows = conn.execute("SELECT * FROM jobs ORDER BY id").fetchall()
    conn.close()
    if not rows:
        print("No jobs to export.")
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        for r in rows:
            writer.writerow(dict(r))
    print(f"✅ Exported {len(rows)} jobs to {path}")


# ---------------------------------------------------------------------------
# Context and LLM
# ---------------------------------------------------------------------------

def load_context_files() -> Dict[str, str]:
    files: Dict[str, str] = {}
    for name in INSTRUCTION_FILES:
        p = APP_ROOT / name
        if p.exists():
            files[name] = read_text(p)
    return files


def jobs_context(limit: int = 25) -> str:
    rows = list_jobs(limit=limit)
    if not rows:
        return "No jobs in database."
    out = []
    for r in rows:
        out.append(
            f"#{r['id']} | P{r['priority']} | {r['status']} | {r['company']} | "
            f"{r['title']} | client={r['client']} | job_id={r['job_id']} | "
            f"location={r['location']} | recruiter={r['recruiter_email']}"
        )
    return "\n".join(out)


def build_prompt(question: str, job_db_id: Optional[int] = None, extra: str = "") -> str:
    context_files = load_context_files()
    sections = []
    for name, data in context_files.items():
        sections.append(f"=== {name} ===\n{data}")

    sections.append(f"=== JOB DATABASE SUMMARY ===\n{db_summary_text()}")
    sections.append(f"=== TOP JOBS ===\n{jobs_context()}")

    if job_db_id is not None:
        row = get_job(job_db_id)
        if row:
            sections.append(f"=== SELECTED JOB #{job_db_id} ===\n{json.dumps(dict(row), indent=2)}")

    if extra.strip():
        sections.append(f"=== EXTRA CONTEXT ===\n{extra}")

    sections.append(f"=== QUESTION ===\n{question}")

    prompt = "\n\n".join(sections)
    return truncate(prompt, MAX_CONTEXT_CHARS)


def ask_llm(question: str, job_db_id: Optional[int] = None, extra: str = "", max_tokens: int = 2500) -> str:
    client = make_client()
    prompt = build_prompt(question, job_db_id=job_db_id, extra=extra)

    system = read_text(APP_ROOT / "instructions.jobs.md")
    if not system:
        system = (
            "You are a job-application operations assistant. "
            "Generate accurate, concise recruiter/application materials. "
            "Never ask for or store passwords. Never recommend uploading sensitive onboarding documents "
            "unless the user confirms onboarding/compliance stage."
        )

    response = client.chat.completions.create(
        model=os.environ.get("OPENAI_MODEL", DEFAULT_MODEL),
        messages=[
            {"role": "system", "content": system[:20000]},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content or ""


def ask_llm_json(question: str, extra: str = "", max_tokens: int = 1600) -> Dict[str, Any]:
    client = make_client()
    prompt = build_prompt(
        question + "\nReturn ONLY valid JSON. No markdown.",
        extra=extra,
    )

    response = client.chat.completions.create(
        model=os.environ.get("OPENAI_MODEL", DEFAULT_MODEL),
        messages=[
            {
                "role": "system",
                "content": (
                    "You extract structured job-application data. "
                    "Return only JSON. Do not include markdown. "
                    "No passwords or secrets."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0,
        max_tokens=max_tokens,
        response_format={"type": "json_object"},
    )
    raw = response.choices[0].message.content or "{}"
    try:
        return json.loads(raw)
    except Exception:
        return {"raw": raw}


# ---------------------------------------------------------------------------
# Email ingestion
# ---------------------------------------------------------------------------

EMAIL_RE = re.compile(r"[\w.\-+%]+@[\w.\-]+\.[A-Za-z]{2,}")
JOB_ID_RE = re.compile(r"\b(?:Job\s*ID|JobDiva\s*#|Req(?:uisition)?\s*ID|ID)\s*[:#-]?\s*([A-Za-z0-9._-]+)", re.I)


def rough_email_metadata(text: str) -> Dict[str, str]:
    data = {"from": "", "to": "", "subject": "", "date": ""}
    for line in text.splitlines()[:60]:
        lower = line.lower()
        if lower.startswith("from:"):
            data["from"] = line.split(":", 1)[1].strip()
        elif lower.startswith("to:"):
            data["to"] = line.split(":", 1)[1].strip()
        elif lower.startswith("subject:"):
            data["subject"] = line.split(":", 1)[1].strip()
        elif lower.startswith("date:"):
            data["date"] = line.split(":", 1)[1].strip()
    return data


def ingest_email_text(path: Path) -> Dict[str, Any]:
    text = read_text(path)
    if not text:
        raise FileNotFoundError(path)

    meta = rough_email_metadata(text)
    emails = EMAIL_RE.findall(text)
    job_id_match = JOB_ID_RE.search(text)
    job_id = job_id_match.group(1) if job_id_match else ""

    question = """
Extract a job lead from this recruiter email.

Return JSON with:
company, title, client, job_id, source, location, work_mode, tax_term, rate, duration,
priority as integer 1-5, status, recruiter_name, recruiter_email, portal_url, notes,
jd_text.

If not a job lead, set status="non-job-email" and explain in notes.
"""
    extracted = ask_llm_json(question, extra=text[:20000])

    fields = {
        "company": extracted.get("company") or "Unknown",
        "title": extracted.get("title") or meta.get("subject", ""),
        "client": extracted.get("client", ""),
        "job_id": extracted.get("job_id") or job_id,
        "source": extracted.get("source") or str(path),
        "location": extracted.get("location", ""),
        "work_mode": extracted.get("work_mode", ""),
        "tax_term": extracted.get("tax_term", ""),
        "rate": extracted.get("rate", ""),
        "duration": extracted.get("duration", ""),
        "priority": int(extracted.get("priority") or 3),
        "status": extracted.get("status") or "lead",
        "recruiter_name": extracted.get("recruiter_name", ""),
        "recruiter_email": extracted.get("recruiter_email") or (emails[0] if emails else ""),
        "portal_url": extracted.get("portal_url", ""),
        "jd_text": extracted.get("jd_text") or text[:10000],
        "notes": extracted.get("notes", ""),
    }

    job_db_id = add_job(fields)

    conn = db()
    conn.execute(
        """
        INSERT INTO interactions(job_id, company, contact_email, contact_name, channel, direction, subject, body, occurred_at, created_at)
        VALUES (?, ?, ?, ?, 'email', 'inbound', ?, ?, ?, ?)
        """,
        (
            job_db_id,
            fields["company"],
            fields["recruiter_email"],
            fields["recruiter_name"],
            meta.get("subject", ""),
            text[:30000],
            meta.get("date", ""),
            now_iso(),
        ),
    )
    conn.commit()
    conn.close()

    return {"job_db_id": job_db_id, "fields": fields}


# ---------------------------------------------------------------------------
# Browser / portal helpers
# ---------------------------------------------------------------------------

def open_url(url: str) -> None:
    print(f"Opening: {url}")
    webbrowser.open(url)


def open_gmail() -> None:
    open_url("https://mail.google.com/mail/u/0/#inbox")


def open_gmail_search(query: str) -> None:
    encoded = urllib.parse.quote(query)
    open_url(f"https://mail.google.com/mail/u/0/#search/{encoded}")


def install_playwright_hint() -> str:
    return (
        "Playwright is not installed. Install it with:\n"
        "  pip install playwright\n"
        "  python -m playwright install chromium\n"
        "Then rerun this command."
    )


def launch_browser_assisted_portal(
    url: str,
    session_key: str = "general",
    post_login_search: Optional[str] = None,
    click_text: Optional[str] = None,
) -> None:
    """
    Opens a headed browser. The user performs login manually.
    If click_text is provided, tries to click a link/button such as "Search on our portal".
    If post_login_search is provided, after user presses Enter, tries to search for it.
    """
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        print(install_playwright_hint())
        print("\nFalling back to default browser.")
        open_url(url)
        return

    print_box(
        """
        SECURITY NOTE:
        - This browser helper does not ask for, read, print, or store your password.
        - You type credentials manually into the browser.
        - The local browser session may store cookies under ./portal_sessions/.
        - Keep ./portal_sessions/ out of git.
        """
    )

    session_dir = PORTAL_SESSION_DIR / slugify(session_key)
    session_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        # Use installed Chrome if available; otherwise bundled Chromium.
        try:
            context = p.chromium.launch_persistent_context(
                str(session_dir),
                headless=False,
                channel="chrome",
                viewport={"width": 1450, "height": 1000},
            )
        except Exception:
            context = p.chromium.launch_persistent_context(
                str(session_dir),
                headless=False,
                viewport={"width": 1450, "height": 1000},
            )

        page = context.pages[0] if context.pages else context.new_page()
        page.goto(url, wait_until="domcontentloaded")
        print(f"Opened: {page.url}")

        if click_text:
            try:
                print(f"Trying to click: {click_text}")
                page.get_by_text(click_text, exact=False).first.click(timeout=8000)
                page.wait_for_load_state("domcontentloaded", timeout=10000)
                print(f"After click: {page.url}")
            except Exception as e:
                print(f"Could not auto-click '{click_text}': {e}")
                print("Click it manually if needed.")

        print("\nManual step: log in / reset password in the browser.")
        print("After you are logged in and can see the portal, return here and press Enter.")
        input("Press Enter after manual login, or Ctrl+C to stop... ")

        if post_login_search:
            print(f"Trying to search for: {post_login_search}")
            selectors = [
                "input[type='search']",
                "input[name*='keyword' i]",
                "input[name*='search' i]",
                "input[placeholder*='keyword' i]",
                "input[placeholder*='search' i]",
                "input",
            ]
            searched = False
            for selector in selectors:
                loc = page.locator(selector).first
                try:
                    if loc.count() and loc.is_visible(timeout=1000):
                        loc.fill(post_login_search)
                        page.keyboard.press("Enter")
                        searched = True
                        print("Search submitted. Review results manually.")
                        break
                except Exception:
                    continue
            if not searched:
                print("Could not find a search box automatically. Search manually.")

        print("Review the portal manually. Stop before final submit unless you are sure.")
        try:
            input("Press Enter to close browser context, or leave it open and Ctrl+C... ")
        finally:
            context.close()


def open_ustech_portal() -> None:
    launch_browser_assisted_portal(
        url="https://ustechsolutions.com/search-vacancies/",
        session_key="ustechsolutions",
        click_text="Search on our portal",
        post_login_search="15565",
    )


def open_generic_portal(url: str, search: Optional[str] = None) -> None:
    launch_browser_assisted_portal(
        url=url,
        session_key=urllib.parse.urlparse(url).netloc or "portal",
        post_login_search=search,
    )


# ---------------------------------------------------------------------------
# US Tech preload / workflow
# ---------------------------------------------------------------------------

def preload_ustech_jobs() -> None:
    init_db()

    jobs = [
        {
            "company": "US Tech Solutions",
            "title": "Machine Learning Engineer / AI Engineer",
            "client": "US Bank",
            "job_id": "15565",
            "source": "Gmail recruiter thread",
            "location": "Hybrid: San Francisco, CA / Concord, CA / Minneapolis / Atlanta / NYC / Chicago / Irving / Charlotte / Cincinnati",
            "work_mode": "Hybrid",
            "tax_term": "W2",
            "rate": "$70-80/hr W2",
            "duration": "6+ months with extension",
            "priority": 1,
            "status": "applied-email",
            "recruiter_name": "Shubham Singhal",
            "recruiter_email": "shubham.singhal@ustechsolutionsinc.com",
            "portal_url": "https://ustechsolutions.com/search-vacancies/",
            "jd_text": "Python, LLMs, prompt engineering, Azure OpenAI SDKs/APIs, agentic systems, MCP, REST APIs, Docker/Kubernetes, enterprise AI, RAG, vector databases, data pipelines, security/compliance.",
            "notes": "Best current USTech lead. Call Shubham and push for same-day submission. Avoid duplicate submission.",
        },
        {
            "company": "US Tech Solutions",
            "title": "Research & Development / AI-powered Workflows",
            "client": "",
            "job_id": "",
            "source": "Amit / redeployment",
            "location": "",
            "work_mode": "",
            "tax_term": "W2 preferred",
            "rate": "",
            "duration": "6+ months",
            "priority": 1,
            "status": "lead",
            "recruiter_name": "Amit Kumar",
            "recruiter_email": "kumar.amit@ustechsolutionsinc.com",
            "portal_url": "https://ustechsolutions.com/search-vacancies/",
            "jd_text": "Engineering role focused on AI-powered workflows and automation using Claude, ChatGPT, Cursor, Python scripting, and engineering automation.",
            "notes": "Strong match. Amit called and gave portal link. Use portal plus phone follow-up.",
        },
        {
            "company": "US Tech Solutions",
            "title": "Agentic LLM / RAG Developer",
            "client": "",
            "job_id": "",
            "source": "Nitesh Singh email",
            "location": "San Jose, CA",
            "work_mode": "Hybrid",
            "tax_term": "W2",
            "rate": "",
            "duration": "12+ months",
            "priority": 2,
            "status": "lead",
            "recruiter_name": "Nitesh Singh",
            "recruiter_email": "nitesh.s@ustechsolutionsinc.com",
            "portal_url": "https://ustechsolutions.com/search-vacancies/",
            "jd_text": "Python, Pandas, NumPy, SQL, LLM/RAG development, LangChain/LangGraph/AutoGen/CrewAI, LoRA, inference optimization, vLLM/TGI/Triton, GPU/accelerators.",
            "notes": "Strong Bay Area AI match. Follow up after Shubham/Amit to avoid bulk sending.",
        },
        {
            "company": "US Tech Solutions",
            "title": "Data Scientist - AI",
            "client": "",
            "job_id": "",
            "source": "Mohd Rehan email",
            "location": "Washington DC",
            "work_mode": "Hybrid, 4 days office",
            "tax_term": "C2C/W2",
            "rate": "",
            "duration": "Long term",
            "priority": 3,
            "status": "lead",
            "recruiter_name": "Mohd Rehan",
            "recruiter_email": "MRehan@ustechsolutionsinc.com",
            "portal_url": "https://ustechsolutions.com/search-vacancies/",
            "jd_text": "RAG, Azure AI/Search, MCP tools/servers, AutoGen/CrewAI/Agno, Azure OpenAI, APIM, Key Vault, Event Hub, App Insights, CI/CD.",
            "notes": "Technically strong but location less favorable.",
        },
        {
            "company": "US Tech Solutions",
            "title": "Senior AI Engineer with Infrastructure",
            "client": "",
            "job_id": "",
            "source": "Akram Khan email",
            "location": "Washington DC",
            "work_mode": "4 days onsite",
            "tax_term": "C2C",
            "rate": "",
            "duration": "6+ months with extension",
            "priority": 4,
            "status": "lead",
            "recruiter_name": "Akram Khan",
            "recruiter_email": "akram@ustechsolutionsinc.com",
            "portal_url": "https://ustechsolutions.com/search-vacancies/",
            "jd_text": "Python, infrastructure, Linux/Windows system administration, ServiceNow/autopilot integration, automation, cloud.",
            "notes": "Lower priority due to onsite DC and C2C framing.",
        },
    ]

    existing = {(r["company"], r["title"], r["job_id"]) for r in list_jobs("US Tech", limit=500)}
    inserted = 0
    for j in jobs:
        key = (j["company"], j["title"], j["job_id"])
        if key not in existing:
            add_job(j)
            inserted += 1

    contacts = [
        ("US Tech Solutions", "Amit Kumar", "kumar.amit@ustechsolutionsinc.com", "", "Redeployment / recruiter", "Amit called and provided portal link."),
        ("US Tech Solutions", "Shubham Singhal", "shubham.singhal@ustechsolutionsinc.com", "(551) 230-1579 Ext.7887", "Recruiter", "Job ID 15565 US Bank ML/AI Engineer."),
        ("US Tech Solutions", "Karan", "karanm@ustechsolutionsinc.com", "", "Backup contact", "Devesh auto-reply points here."),
        ("US Tech Solutions", "Nitesh Singh", "nitesh.s@ustechsolutionsinc.com", "", "Recruiter", "Agentic LLM/RAG and AMD threads."),
        ("US Tech Solutions", "Mohd Rehan", "MRehan@ustechsolutionsinc.com", "", "Recruiter", "Data Scientist - AI."),
        ("US Tech Solutions", "Akram Khan", "akram@ustechsolutionsinc.com", "", "Recruiter", "Senior AI Engineer / infrastructure."),
    ]
    for c in contacts:
        upsert_contact(*c)

    print(f"✅ US Tech preload complete. Inserted {inserted} new jobs.")


def ustech_next_actions() -> str:
    return textwrap.dedent(
        """
        US Tech next actions:

        1. Call Shubham for Job ID 15565.
           Script:
           Hi Shubham, this is Art Ponomarev. I replied to your email for Job ID 15565,
           Machine Learning Engineer / AI Engineer for US Bank. I am a strong match for
           Python, LLM/RAG, Azure OpenAI, MCP, Docker/Kubernetes, vector databases, and
           enterprise AI. San Francisco or Concord hybrid works, W2 is fine, and I am
           available immediately. Can you confirm what you need to submit me today?

        2. Use Amit as the redeployment owner and portal confirmer.
           Ask him to confirm he sees your portal profile and resume.

        3. Use the portal for system-of-record application.
           Open /ustech-portal, log in manually, search 15565 first.

        4. Do not use deepakk@ustechsolutionsinc.com.
           It bounced. Sayantani's forwarding appears broken.

        5. Avoid rapid bulk email.
           Use targeted phone + one short follow-up per recruiter/job thread.
        """
    ).strip()


# ---------------------------------------------------------------------------
# Command parsing
# ---------------------------------------------------------------------------

HELP = """
Commands:

Core:
  /help
  /exit
  /db-init
  /db-summary
  /list-jobs [filter]
  /status <job_db_id> <status> [notes...]
  /export-csv [path]

Job data:
  /add-job
  /ingest-email <path_to_txt_or_eml>
  /preload-ustech
  /ustech

Generation:
  /draft <job_db_id>              recruiter reply / application note
  /followup <job_db_id>           concise follow-up
  /match <job_db_id>              fit/gap and submission strategy
  /cover <job_db_id>              cover letter / cover note
  /profile-summary [job_db_id]    5-6 sentence profile summary
  free text                       ask the assistant using instructions + DB

Browser helpers:
  /gmail
  /gmail-search <query>
  /portal <url> [search terms]
  /ustech-portal                  opens US Tech jobs page, clicks portal if possible,
                                  pauses for manual login, then searches 15565

Output:
  /save <filename>                saves last response to outputs/<filename>

Rules:
  - No passwords in this script.
  - No passport/W-2/background-check/reference uploads unless onboarding/compliance is confirmed.
  - Portal login is manual.
"""


def interactive_add_job() -> None:
    print("Enter job fields. Leave blank if unknown.")
    fields: Dict[str, Any] = {}
    for name in [
        "company", "title", "client", "job_id", "source", "location", "work_mode",
        "tax_term", "rate", "duration", "recruiter_name", "recruiter_email", "portal_url",
    ]:
        fields[name] = input(f"{name}: ").strip()
    priority = input("priority 1-5 [3]: ").strip()
    fields["priority"] = int(priority) if priority.isdigit() else 3
    fields["status"] = input("status [lead]: ").strip() or "lead"
    print("Paste JD text. End with a single line containing only END.")
    lines = []
    while True:
        line = input()
        if line.strip() == "END":
            break
        lines.append(line)
    fields["jd_text"] = "\n".join(lines)
    fields["notes"] = input("notes: ").strip()
    jid = add_job(fields)
    print(f"✅ Added job #{jid}")


def parse_job_id_arg(arg: str) -> Optional[int]:
    try:
        return int(arg.strip())
    except Exception:
        print("Expected numeric job_db_id.")
        return None


def command_loop() -> None:
    ensure_dirs()
    init_db()
    last_response = ""

    print_header(f"🧠 {APP_NAME}")
    print(f"Working directory: {APP_ROOT}")
    print(f"Database: {DB_PATH}")
    if load_api_key():
        print("✅ API key detected in environment/.env.")
    else:
        print("⚠️ No API key detected yet. Generation commands need OPENAI_API_KEY or CODEX_API_KEY.")
    print(HELP)

    while True:
        try:
            raw = input("\n💼 job-ai> ").strip()
            if not raw:
                continue

            if raw in ["/exit", "exit", "quit", "/quit"]:
                print("👋 Bye.")
                break

            if raw == "/help":
                print(HELP)
                continue

            if raw == "/db-init":
                init_db()
                print("✅ Database initialized.")
                continue

            if raw == "/db-summary":
                print(db_summary_text())
                continue

            if raw.startswith("/list-jobs"):
                filt = raw[len("/list-jobs"):].strip()
                rows = list_jobs(filt, limit=100)
                if not rows:
                    print("No jobs found.")
                for r in rows:
                    print(
                        f"#{r['id']:>3} P{r['priority']} {r['status']:<16} "
                        f"{r['company'][:20]:<20} | {r['title'][:45]:<45} | "
                        f"job_id={r['job_id']:<10} | {r['recruiter_email']}"
                    )
                continue

            if raw.startswith("/status "):
                parts = shlex.split(raw)
                if len(parts) < 3:
                    print("Usage: /status <job_db_id> <status> [notes...]")
                    continue
                jid = parse_job_id_arg(parts[1])
                if jid is None:
                    continue
                status = parts[2]
                notes = " ".join(parts[3:]) if len(parts) > 3 else ""
                update_job_status(jid, status, notes)
                print("✅ Updated.")
                continue

            if raw.startswith("/export-csv"):
                parts = shlex.split(raw)
                path = Path(parts[1]) if len(parts) > 1 else OUTPUT_DIR / f"jobs_export_{today()}.csv"
                export_jobs_csv(path)
                continue

            if raw == "/add-job":
                interactive_add_job()
                continue

            if raw.startswith("/ingest-email "):
                parts = shlex.split(raw)
                if len(parts) < 2:
                    print("Usage: /ingest-email <path>")
                    continue
                result = ingest_email_text(Path(parts[1]).expanduser())
                print(f"✅ Ingested email as job #{result['job_db_id']}")
                print(json.dumps(result["fields"], indent=2))
                continue

            if raw == "/preload-ustech":
                preload_ustech_jobs()
                continue

            if raw == "/ustech":
                preload_ustech_jobs()
                last_response = ustech_next_actions()
                print_box(last_response)
                continue

            if raw == "/gmail":
                open_gmail()
                continue

            if raw.startswith("/gmail-search "):
                query = raw[len("/gmail-search "):].strip()
                open_gmail_search(query)
                continue

            if raw.startswith("/portal "):
                rest = raw[len("/portal "):].strip()
                parts = shlex.split(rest)
                if not parts:
                    print("Usage: /portal <url> [search terms]")
                    continue
                url = parts[0]
                search = " ".join(parts[1:]) if len(parts) > 1 else None
                open_generic_portal(url, search=search)
                continue

            if raw == "/ustech-portal":
                open_ustech_portal()
                continue

            if raw.startswith("/draft "):
                parts = shlex.split(raw)
                jid = parse_job_id_arg(parts[1]) if len(parts) > 1 else None
                if jid is None:
                    continue
                last_response = ask_llm(
                    "Draft a concise recruiter reply/application note for this job. "
                    "Include confirmation of interest, strongest fit, work mode/rate alignment, "
                    "availability, and next-step ask. Do not overstate. No markdown table.",
                    job_db_id=jid,
                )
                print_box(last_response)
                continue

            if raw.startswith("/followup "):
                parts = shlex.split(raw)
                jid = parse_job_id_arg(parts[1]) if len(parts) > 1 else None
                if jid is None:
                    continue
                last_response = ask_llm(
                    "Draft a short follow-up email for this job. Goal: confirm receipt, ask for submission status, "
                    "ask what is needed next. Keep it under 120 words.",
                    job_db_id=jid,
                )
                print_box(last_response)
                continue

            if raw.startswith("/match "):
                parts = shlex.split(raw)
                jid = parse_job_id_arg(parts[1]) if len(parts) > 1 else None
                if jid is None:
                    continue
                last_response = ask_llm(
                    "Analyze fit for this job. Include: strongest matches, gaps/risks, exact positioning, "
                    "submission strategy, and 3 recruiter call talking points.",
                    job_db_id=jid,
                )
                print_box(last_response)
                continue

            if raw.startswith("/cover "):
                parts = shlex.split(raw)
                jid = parse_job_id_arg(parts[1]) if len(parts) > 1 else None
                if jid is None:
                    continue
                last_response = ask_llm(
                    "Generate a compact cover note for this job. Make it recruiter-ready and ATS-safe. "
                    "Do not invent unprovided facts.",
                    job_db_id=jid,
                )
                print_box(last_response)
                continue

            if raw.startswith("/profile-summary"):
                parts = shlex.split(raw)
                jid = parse_job_id_arg(parts[1]) if len(parts) > 1 else None
                last_response = ask_llm(
                    "Generate a 5-6 sentence recruiter profile summary. "
                    "Tailor it to the selected job if one is selected. Use concrete ML/AI/MLOps strengths.",
                    job_db_id=jid,
                )
                print_box(last_response)
                continue

            if raw.startswith("/save "):
                filename = raw[len("/save "):].strip()
                if not filename:
                    print("Usage: /save <filename>")
                    continue
                if not last_response:
                    print("⚠️ No response to save.")
                    continue
                path = OUTPUT_DIR / filename
                write_text(path, last_response)
                print(f"✅ Saved to {path}")
                continue

            # Freeform question
            last_response = ask_llm(raw)
            print_box(last_response)

        except KeyboardInterrupt:
            print("\n👋 Bye.")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")


if __name__ == "__main__":
    command_loop()
