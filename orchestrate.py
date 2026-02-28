import os
import sys
from dotenv import load_dotenv
from agents.planner import run_planner
from agents.coder import run_multi_file_coder, validate_tsx
from agents.context import get_backend_context, get_frontend_context
from agents.pr import create_and_merge_pr

load_dotenv()

FRONTEND_BASE = os.path.expanduser("~/projects/wanderlust-frontend")
AUTO = "--auto" in sys.argv
MAX_RETRIES = 3

def read_file(path: str) -> str:
    try:
        with open(path, 'r') as f:
            return f.read()
    except:
        return "(file not found)"

def write_file(path: str, content: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write(content)
    print(f"  ✓ Written: {path}")

def confirm(prompt: str) -> bool:
    if AUTO:
        print(f"  [AUTO] {prompt} → yes")
        return True
    return input(f"\n{prompt} (yes/no): ").lower() == "yes"

def get_full_context() -> str:
    base = FRONTEND_BASE
    files_to_read = [
        "CLAUDE.md",
        "app/page.tsx",
        "app/providers.tsx",
        "app/layout.tsx",
        "package.json",
    ]
    context = ""
    for f in files_to_read:
        path = f"{base}/{f}"
        content = read_file(path)
        if content != "(file not found)":
            context += f"\n\n=== {f} ===\n{content}"
    return context

def main():
    mode = "AUTO" if AUTO else "INTERACTIVE"
    print(f"=== Wanderlust Agent Orchestrator [{mode}] ===\n")

    args = [a for a in sys.argv[1:] if a != "--auto"]
    if args:
        feature_request = args[0]
        print(f"Feature: {feature_request}")
    else:
        feature_request = input("Describe the feature you want to build: ")

    print("\n[Planner Agent] Reading codebase context...")
    backend_ctx = get_backend_context()
    frontend_ctx = get_frontend_context()

    print("[Planner Agent] Generating implementation plan...\n")
    plan = run_planner(feature_request, backend_ctx, frontend_ctx)

    print("=" * 60)
    print("IMPLEMENTATION PLAN")
    print("=" * 60)
    print(plan)
    print("=" * 60)

    if not confirm("Proceed with implementation?"):
        print("Aborted.")
        return

    full_context = get_full_context()
    extra_context = ""
    written_paths = []

    for attempt in range(1, MAX_RETRIES + 1):
        print(f"\n[Coding Agent] Attempt {attempt}/{MAX_RETRIES}...")

        files = run_multi_file_coder(feature_request, full_context, extra_context)

        if not files:
            print("  ✗ No files generated")
            extra_context = "CRITICAL: Output files using ===FILE: path=== ... ===END=== format."
            continue

        print(f"  → {len(files)} file(s) to write:")
        
        # Validate all files first
        truncated = []
        for f in files:
            print(f"    {f['path']} ({len(f['content'])} chars)")
            if f['path'].endswith(('.tsx', '.ts')) and not validate_tsx(f['content']):
                truncated.append(f['path'])

        if truncated:
            print(f"  ✗ Truncated files: {truncated}")
            extra_context = f"CRITICAL: These files were truncated: {truncated}. Output COMPLETE files."
            continue

        # Write all files
        written_paths = []
        for f in files:
            full_path = f"{FRONTEND_BASE}/{f['path']}"
            write_file(full_path, f['content'])
            written_paths.append(f['path'])

        # Run tests
        print("\n[Test Agent] Running tests...")
        result = os.system(f"cd {FRONTEND_BASE} && npm test --silent")
        if result != 0:
            print("  ✗ Tests failed — retrying")
            extra_context = "CRITICAL: Previous attempt broke tests. Fix carefully."
            for p in written_paths:
                os.system(f"cd {FRONTEND_BASE} && git checkout {p} 2>/dev/null || true")
            continue
        print("  ✓ Tests passed")

        # Commit and deploy
        print("\n[PR Agent] Committing and deploying...")
        os.system(f"cd {FRONTEND_BASE} && git add -A")
        os.system(f'cd {FRONTEND_BASE} && git commit -m "feat: {feature_request[:60]} (attempt {attempt})"')
        os.system(f"cd {FRONTEND_BASE} && git push origin develop")

        success = create_and_merge_pr(
            title=f"feat: {feature_request[:60]}",
            body=f"Automated change via Wanderlust Agent Orchestrator (attempt {attempt})\n\nFiles changed:\n" + "\n".join(f"- {p}" for p in written_paths)
        )

        if success:
            print("\n✓ Deployed to production")
            return
        else:
            print(f"  ✗ CI failed on attempt {attempt} — retrying")
            extra_context = "CRITICAL: Previous attempt failed CI build. Likely a syntax error or truncated file. Output COMPLETE files."
            os.system(f"cd {FRONTEND_BASE} && git checkout develop")

    print(f"\n✗ Failed after {MAX_RETRIES} attempts. Manual intervention required.")

if __name__ == "__main__":
    main()
