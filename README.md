# ai-admin-agent

An AI-powered incident management system that monitors system health across local, AWS, and Azure resources, detects issues like high CPU or low disk space, and sends incident data to an agent (Groq-hosted `gpt-oss-20b`) to generate a diagnosis and a fix plan. Steps with confidence scores above 0.7 are executed automatically (bash/PowerShell/AWS/Azure actions, behind a command whitelist and dry-run mode), while lower-confidence plans are surfaced for manual review instead of executed. Also available as an interactive CLI (`--ask` / `--interactive`) for ad-hoc admin requests outside the monitoring loop.

## Quickstart (local)

1. Create a virtual env and install dependencies:

   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. Set `GROQ_API_KEY` in your `.env`. Email alerting (optional) needs `EMAIL_SENDER`, `EMAIL_PASSWORD`, `EMAIL_RECEIVER`, `SMTP_SERVER`, `SMTP_PORT`.

3. Run the monitor/agent:

   ```bash
   python main_agent.py
   ```
