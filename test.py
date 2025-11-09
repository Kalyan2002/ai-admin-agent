from ai_controllers import AIController

# Create AI controller (make sure you set GROQ_API_KEY in your .env)
ai = AIController()

# Simulate a system incident (example: high disk usage)
incident = {"type": "disk_high", "value": 95, "description": "Disk usage exceeded 90% on root volume"}

incident = {"type": "disk_high", "value": 95, "description": "Disk usage exceeded 90% on root volume"}

# Generate reasoning and plan
plan = ai.generate_plan(incident)

# Print AI output
print(plan)

