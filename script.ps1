# -------------------------------------------------------------------
# 0️⃣ Navigate to your project folder
# -------------------------------------------------------------------
Set-Location -Path 'C:\Users\kalya\Edu\AIops\ai-admin-agent'


# -------------------------------------------------------------------
# 1️⃣ Create & activate virtual environment
# -------------------------------------------------------------------
python -m venv venv
venv\Scripts\Activate.ps1


# -------------------------------------------------------------------
# 2️⃣ Install dependencies
# -------------------------------------------------------------------
pip install --upgrade pip
pip install -r requirements.txt


# -------------------------------------------------------------------
# 3️⃣ Copy environment template
# -------------------------------------------------------------------
Copy-Item .env.template .env -Force


# -------------------------------------------------------------------
# 4️⃣ Edit environment variables
# -------------------------------------------------------------------
notepad .env
# Make sure these are set:
# GROQ_API_KEY
# AZURE_SUBSCRIPTION_ID
# (optional) AZURE_RESOURCE_GROUP
# AWS credentials if you use AWS


# -------------------------------------------------------------------
# 5️⃣ (Optional) Verify CLIs (NOT required for SDK usage)
# -------------------------------------------------------------------
aws --version
# az --version   # optional; NOT required anymore


# -------------------------------------------------------------------
# 6️⃣ Run SAFE one-time health check (dry-run)
# -------------------------------------------------------------------
python main_agent.py --monitor --run-once --dry-run


# -------------------------------------------------------------------
# 7️⃣ Start INTERACTIVE MODE (recommended)
# -------------------------------------------------------------------
python main_agent.py --interactive
# In interactive mode, you can type commands like:
# "List all Azure VMs"
# "Show me the top 5 processes on the server"
# "What is the disk usage on the server?"