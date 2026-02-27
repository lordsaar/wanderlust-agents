import anthropic

def run_planner(feature_request: str, backend_context: str, frontend_context: str) -> str:
    client = anthropic.Anthropic()
    
    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=2000,
        system="""You are a Planning Agent for the Wanderlust travel story generator app.
Your job is to break down a feature request into concrete, actionable tasks.

The system has two repos:
- wanderlust-backend: FastAPI, Python, PostgreSQL, SQLAlchemy
- wanderlust-frontend: Next.js 16, TypeScript, Tailwind CSS, Auth.js

Output your plan as a structured list with sections:
BACKEND TASKS: (list changes needed in the backend repo)
FRONTEND TASKS: (list changes needed in the frontend repo)
DATABASE CHANGES: (yes/no - does this need a migration?)
ESTIMATED COMPLEXITY: (low/medium/high)
RISKS: (any potential issues to watch for)""",
        messages=[
            {
                "role": "user",
                "content": f"""Feature request: {feature_request}

Backend codebase summary:
{backend_context}

Frontend codebase summary:
{frontend_context}

Please produce a detailed implementation plan."""
            }
        ]
    )
    
    return response.content[0].text
