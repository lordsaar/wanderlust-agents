import os
import anthropic
from dotenv import load_dotenv

load_dotenv()

def run_coder(task: str, file_path: str, current_content: str, context: str) -> str:
    """Single file coder - kept for simple tasks."""
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=8000,
        system="""You are a Coding Agent for the Wanderlust travel story generator app.
Output ONLY the complete file content, no explanations, no markdown code blocks.
CRITICAL: Always output the COMPLETE file. Never truncate.""",
        messages=[{"role": "user", "content": f"""Task: {task}
File: {file_path}
Current content:
{current_content}
Context: {context}
Output the complete new file content:"""}]
    )
    return response.content[0].text

def run_multi_file_coder(task: str, repo_context: str, extra_context: str = "") -> list[dict]:
    """Multi-file coder - returns list of {path, content} dicts."""
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=16000,
        system="""You are a Coding Agent for the Wanderlust travel story generator app (Next.js 16, TypeScript, Tailwind).
You implement features that may require creating or modifying multiple files.

Output format - use this EXACT structure for each file:
===FILE: path/to/file.tsx===
<complete file content here>
===END===

Rules:
- Output ONLY the file blocks, no explanations
- Always output COMPLETE file contents, never truncate
- Each file must end with ===END===
- Paths are relative to the repo root (e.g. app/page.tsx, lib/i18n/translations.ts)
- Use TypeScript for all .ts/.tsx files
- Match dark theme: slate-900, blue-950, slate-800""",
        messages=[{"role": "user", "content": f"""Task: {task}

Codebase context:
{repo_context}

{extra_context}

Output all required files using the ===FILE: path=== ... ===END=== format:"""}]
    )
    
    return parse_multi_file_output(response.content[0].text)

def parse_multi_file_output(output: str) -> list[dict]:
    """Parse ===FILE: path=== ... ===END=== blocks."""
    files = []
    lines = output.split('\n')
    current_path = None
    current_lines = []
    
    for line in lines:
        if line.startswith('===FILE:') and line.endswith('==='):
            if current_path and current_lines:
                files.append({'path': current_path, 'content': '\n'.join(current_lines)})
            current_path = line[8:-3].strip()
            current_lines = []
        elif line == '===END===' and current_path:
            files.append({'path': current_path, 'content': '\n'.join(current_lines)})
            current_path = None
            current_lines = []
        elif current_path is not None:
            current_lines.append(line)
    
    return files

def validate_tsx(content: str) -> bool:
    """Basic validation that TSX/TS file is not truncated."""
    content = content.strip()
    return content.endswith('}') or content.endswith('>') or content.endswith('"') or content.endswith("'")
