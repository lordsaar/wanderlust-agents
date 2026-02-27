import os
import anthropic
from dotenv import load_dotenv

load_dotenv()

def run_coder(task: str, file_path: str, current_content: str, context: str) -> str:
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=8000,
        system="""You are a Coding Agent for the Wanderlust travel story generator app.
You receive a specific task and produce the complete file content as output.

Rules:
- Output ONLY the complete file content, no explanations
- No markdown code blocks, no backticks
- The output will be written directly to the file
- Follow existing code style and conventions
- Use TypeScript for frontend files
- Match the existing dark theme (slate-900, blue-950, slate-800)
- CRITICAL: Always output the COMPLETE file. Never truncate. The file must end with the closing tags.""",
        messages=[
            {
                "role": "user",
                "content": f"""Task: {task}

File to modify: {file_path}

Current file content:
{current_content}

Additional context:
{context}

Output the complete new file content. Make sure the file is complete and ends properly:"""
            }
        ]
    )
    
    return response.content[0].text

def validate_tsx(content: str) -> bool:
    """Basic validation that TSX file is not truncated."""
    content = content.strip()
    return content.endswith('}') or content.endswith('>')
