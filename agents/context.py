import os

def read_file(path: str) -> str:
    try:
        with open(path, 'r') as f:
            return f.read()
    except:
        return ""

def get_backend_context() -> str:
    base = os.path.expanduser("~/projects/wanderlust-backend")
    return f"""
CLAUDE.md:
{read_file(f"{base}/CLAUDE.md")}

API Routes:
{read_file(f"{base}/app/api/routes/stories.py")}

Models:
{read_file(f"{base}/app/models/story.py")}
"""

def get_frontend_context() -> str:
    base = os.path.expanduser("~/projects/wanderlust-frontend")
    return f"""
CLAUDE.md:
{read_file(f"{base}/CLAUDE.md")}

Main page:
{read_file(f"{base}/app/page.tsx")}
"""
