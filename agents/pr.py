import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

def create_and_merge_pr(title: str, body: str, head: str = "develop", base: str = "main") -> bool:
    token = os.getenv("GITHUB_TOKEN")
    org = os.getenv("GITHUB_ORG")
    repo = os.getenv("FRONTEND_REPO")
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Create PR
    pr_url = f"https://api.github.com/repos/{org}/{repo}/pulls"
    pr_data = {"title": title, "body": body, "head": head, "base": base}
    pr_response = requests.post(pr_url, json=pr_data, headers=headers)
    
    if pr_response.status_code != 201:
        print(f"  ✗ PR creation failed: {pr_response.json().get('message')}")
        return False
    
    pr_number = pr_response.json()["number"]
    pr_html = pr_response.json()["html_url"]
    sha = pr_response.json()["head"]["sha"]
    print(f"  ✓ PR created: {pr_html}")
    
    # Wait for CI
    print(f"  [CI] Waiting for checks on {sha[:8]}...")
    ci_result = wait_for_ci(org, repo, sha, headers)
    
    if not ci_result:
        print(f"  ✗ CI failed — not merging. Check: {pr_html}")
        return False
    
    # Merge PR
    merge_url = f"https://api.github.com/repos/{org}/{repo}/pulls/{pr_number}/merge"
    merge_response = requests.put(merge_url, json={"merge_method": "merge"}, headers=headers)
    
    if merge_response.status_code != 200:
        print(f"  ✗ Merge failed: {merge_response.json().get('message')}")
        return False
    
    print(f"  ✓ PR #{pr_number} merged")
    return True

def wait_for_ci(org: str, repo: str, sha: str, headers: dict, timeout: int = 300) -> bool:
    """Poll GitHub checks until all pass or any fail. Returns True if all pass."""
    url = f"https://api.github.com/repos/{org}/{repo}/commits/{sha}/check-runs"
    start = time.time()
    
    while time.time() - start < timeout:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"  [CI] Could not fetch checks: {response.status_code}")
            time.sleep(10)
            continue
        
        data = response.json()
        runs = data.get("check_runs", [])
        
        if not runs:
            print(f"  [CI] No checks yet, waiting...")
            time.sleep(10)
            continue
        
        statuses = [(r["name"], r["status"], r.get("conclusion")) for r in runs]
        
        # Check if any failed
        failed = [r for r in statuses if r[2] in ("failure", "cancelled", "timed_out")]
        if failed:
            for name, _, conclusion in failed:
                print(f"  ✗ Check failed: {name} → {conclusion}")
            return False
        
        # Check if all completed successfully
        completed = [r for r in statuses if r[1] == "completed"]
        pending = [r for r in statuses if r[1] in ("queued", "in_progress")]
        
        if pending:
            names = [r[0] for r in pending]
            elapsed = int(time.time() - start)
            print(f"  [CI] Waiting ({elapsed}s): {', '.join(names)}")
            time.sleep(15)
            continue
        
        # All completed - check all passed
        passed = all(r[2] in ("success", "skipped") for r in completed)
        if passed:
            print(f"  ✓ All CI checks passed")
            return True
        
        # Some unexpected conclusion
        for name, _, conclusion in completed:
            if conclusion not in ("success", "skipped"):
                print(f"  ✗ Check {name}: {conclusion}")
        return False
    
    print(f"  ✗ CI timeout after {timeout}s")
    return False
