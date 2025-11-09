# 1️⃣ Clone your project repo (if not yet)
#git clone https://github.com/Kalyan2002/ai-admin-agent.git
#cd ai-admin-agent
# Navigate to your project folder
Set-Location -Path 'C:\Users\kalya\Edu\AIops\ai-admin-agent'

# 1️⃣ Create & activate virtual environment
python -m venv venv
venv\Scripts\Activate.ps1

# 2️⃣ Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 3️⃣ Copy environment template
Copy-Item .env.template .env

# 4️⃣ Open .env in Notepad (edit your keys)
notepad .env

# 5️⃣ (Optional) Verify AWS CLI installed
aws --version
# If you get "aws not recognized", install it:
# msiexec /i https://awscli.amazonaws.com/AWSCLIV2.msi

# 6️⃣ Run your app in dry-run mode (safe)
python main_agent.py --monitor --run-once

# 7️⃣ Simulate incident
python main_agent.py --incident-json '{"type":"disk_high","value":92}'

# 8️⃣ View logs
python main_agent.py --show-logs
# 9️⃣ Deactivate venv when done
#deactivate