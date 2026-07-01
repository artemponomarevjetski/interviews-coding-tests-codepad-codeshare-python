-- Job Application Database Schema
-- SQLite 3

PRAGMA foreign_keys = ON;

-- Jobs table
CREATE TABLE jobs (
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
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Contacts table
CREATE TABLE contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company TEXT NOT NULL DEFAULT '',
    name TEXT NOT NULL DEFAULT '',
    email TEXT NOT NULL DEFAULT '',
    phone TEXT NOT NULL DEFAULT '',
    role TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'active',
    notes TEXT NOT NULL DEFAULT '',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Interactions table
CREATE TABLE interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER,
    company TEXT NOT NULL DEFAULT '',
    contact_email TEXT NOT NULL DEFAULT '',
    contact_name TEXT NOT NULL DEFAULT '',
    channel TEXT NOT NULL DEFAULT '',
    direction TEXT NOT NULL DEFAULT '',
    subject TEXT NOT NULL DEFAULT '',
    body TEXT NOT NULL DEFAULT '',
    occurred_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE SET NULL
);

-- Applications table
CREATE TABLE applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL,
    submitted_on DATETIME DEFAULT CURRENT_TIMESTAMP,
    submitted_via TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'planned',
    confirmation TEXT NOT NULL DEFAULT '',
    next_action TEXT NOT NULL DEFAULT '',
    next_action_due DATETIME,
    notes TEXT NOT NULL DEFAULT '',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
);

-- Portal accounts table
CREATE TABLE portal_accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    portal_key TEXT NOT NULL DEFAULT '',
    company TEXT NOT NULL DEFAULT '',
    portal_url TEXT NOT NULL DEFAULT '',
    username TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'unknown',
    notes TEXT NOT NULL DEFAULT '',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Documents table
CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_type TEXT NOT NULL DEFAULT '',
    label TEXT NOT NULL DEFAULT '',
    path TEXT NOT NULL DEFAULT '',
    safe_for_application INTEGER NOT NULL DEFAULT 0,
    safe_for_onboarding INTEGER NOT NULL DEFAULT 0,
    notes TEXT NOT NULL DEFAULT '',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_priority ON jobs(priority);
CREATE INDEX idx_jobs_recruiter ON jobs(recruiter_email);
CREATE INDEX idx_contacts_email ON contacts(email);
CREATE INDEX idx_interactions_job ON interactions(job_id);
CREATE INDEX idx_applications_job ON applications(job_id);

-- Trigger to update updated_at timestamp
CREATE TRIGGER update_jobs_updated_at 
AFTER UPDATE ON jobs 
BEGIN 
    UPDATE jobs SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id; 
END;

CREATE TRIGGER update_contacts_updated_at 
AFTER UPDATE ON contacts 
BEGIN 
    UPDATE contacts SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id; 
END;

CREATE TRIGGER update_applications_updated_at 
AFTER UPDATE ON applications 
BEGIN 
    UPDATE applications SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id; 
END;
