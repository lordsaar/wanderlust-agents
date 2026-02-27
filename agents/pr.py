import os
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
    print(f"  ✓ PR created: {pr_html}")
    
    # Merge PR
    merge_url = f"https://api.github.com/repos/{org}/{repo}/pulls/{pr_number}/merge"
    merge_response = requests.put(merge_url, json={"merge_method": "merge"}, headers=headers)
    
    if merge_response.status_code != 200:
        print(f"  ✗ Merge failed: {merge_response.json().get('message')}")
        return False
    
    print(f"  ✓ PR #{pr_number} merged")
    return True
