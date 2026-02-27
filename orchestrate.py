import os
import sys
from dotenv import load_dotenv
from agents.planner import run_planner
from agents.coder import run_coder, validate_tsx
from agents.context import get_backend_context, get_frontend_context
from agents.pr import create_and_merge_pr

load_dotenv()

FRONTEND_BASE = os.path.expanduser("~/projects/wanderlust-frontend")
AUTO = "--auto" in sys.argv

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

    print("\n[Coding Agent] Implementing changes...")

    impressum_path = f"{FRONTEND_BASE}/app/impressum/page.tsx"
    current_content = read_file(impressum_path)

    new_content = run_coder(
        task=f"Update the impressum page as described: {feature_request}",
        file_path=impressum_path,
        current_content=current_content,
        context="Keep all existing content, only make the requested changes."
    )

    if not AUTO:
        print("\n[Coding Agent] Preview:")
        print("-" * 40)
        print(new_content[:500] + "...")
        print("-" * 40)

    if not validate_tsx(new_content):
        print("  ✗ Generated file appears truncated — aborting")
        return

    if confirm("Write this file?"):
        write_file(impressum_path, new_content)

        print("\n[Test Agent] Running tests...")
        result = os.system(f"cd {FRONTEND_BASE} && npm test --silent")
        if result != 0:
            print("  ✗ Tests failed — aborting deployment")
            return
        print("  ✓ Tests passed")

        print("\n[PR Agent] Committing and deploying...")
        os.system(f"cd {FRONTEND_BASE} && git add app/impressum/page.tsx")
        os.system(f'cd {FRONTEND_BASE} && git commit -m "feat: {feature_request[:60]}"')
        os.system(f"cd {FRONTEND_BASE} && git push origin develop")
        create_and_merge_pr(
            title=f"feat: {feature_request[:60]}",
            body="Automated change via Wanderlust Agent Orchestrator"
        )
        print("\n✓ Deployed to production")
    else:
        print("Cancelled.")

if __name__ == "__main__":
    main()
