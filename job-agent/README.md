# Job Application AI Assistant

Local assistant for job applications, recruiter email processing, job database tracking, and safe portal/Gmail browser workflows.

## Setup

```bash
mkdir -p ~/job-agent
cd ~/job-agent

python3 -m venv .venv
source .venv/bin/activate

pip install openai
# Optional but recommended for portal browser helper:
pip install playwright
python -m playwright install chromium
```

Copy files into `~/job-agent/`:

```text
job-application-ai-assistant.py
instructions.jobs.md
instructions.ustech.md
instructions.ustech.mmd
candidate_profile.md
.env
```

`.env` should contain one of:

```bash
OPENAI_API_KEY=...
```

or, if your local Codex setup uses this name:

```bash
CODEX_API_KEY=...
```

The script maps `CODEX_API_KEY` to the OpenAI client internally.

## Run

```bash
chmod +x job-application-ai-assistant.py
./job-application-ai-assistant.py
```

## First commands

```text
/db-init
/preload-ustech
/db-summary
/list-jobs US Tech
/ustech
/ustech-portal
```

## Typical US Tech workflow

```text
/preload-ustech
/list-jobs US Tech
/match 1
/draft 1
/gmail-search label:USTech newer_than:7d
/ustech-portal
```

## Security

Do not commit:

```text
.env
jobs.db
portal_sessions/
outputs/
emails/
documents/
```

Portal and Gmail login are manual. The assistant does not store passwords.
