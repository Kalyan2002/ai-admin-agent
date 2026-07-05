# ai-admin-agent

An AI-powered incident management system that monitors system health, detects issues like high CPU or low disk space, and sends incident data to an agent that uses GPT-5 to generate a diagnosis and a fix plan. Safe steps with confidence scores above 0.7 are executed automatically, while others require manual approval through a CLI.

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
