# Databricks notebook source
# DBTITLE 1,Configuration
import requests
import base64
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- Configuration ---
GITHUB_REPO = "databricks-solutions/ai-dev-kit"
GITHUB_BRANCH = "main"
GITHUB_SKILLS_PATH = "databricks-skills"
GITHUB_RAW_BASE = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}"
GITHUB_API_BASE = f"https://api.github.com/repos/{GITHUB_REPO}/contents"

# Workspace target: /Users/<username>/.assistant/skills/<skill-name>/
USERNAME = spark.sql("SELECT current_user()").collect()[0][0]
WORKSPACE_SKILLS_DIR = f"/Users/{USERNAME}/.assistant/skills"

# Databricks API setup
from dbruntime.databricks_repl_context import get_context
ctx = get_context()
DB_HOST = ctx.browserHostName
DB_TOKEN = ctx.apiToken
DB_HEADERS = {"Authorization": f"Bearer {DB_TOKEN}", "Content-Type": "application/json"}

# Skills to skip (not actual skills)
SKIP_DIRS = {"TEMPLATE", "README.md", "install_skills.sh"}

print(f"Target workspace path: /Workspace{WORKSPACE_SKILLS_DIR}")
print(f"Source: {GITHUB_RAW_BASE}/{GITHUB_SKILLS_PATH}")
print(f"User: {USERNAME}")

# COMMAND ----------

# DBTITLE 1,Helper functions: workspace + GitHub
def ws_mkdirs(path):
    """Create workspace directory (recursively)."""
    resp = requests.post(
        f"https://{DB_HOST}/api/2.0/workspace/mkdirs",
        headers=DB_HEADERS,
        json={"path": f"/Workspace{path}"}
    )
    resp.raise_for_status()

def ws_upload_file(path, content_bytes):
    """Upload a file to the workspace using the Import API."""
    b64_content = base64.b64encode(content_bytes).decode("utf-8")
    resp = requests.post(
        f"https://{DB_HOST}/api/2.0/workspace/import",
        headers=DB_HEADERS,
        json={
            "path": f"/Workspace{path}",
            "format": "AUTO",
            "language": None,
            "content": b64_content,
            "overwrite": True
        }
    )
    resp.raise_for_status()

def github_list_dir(path):
    """List contents of a GitHub directory."""
    url = f"{GITHUB_API_BASE}/{path}?ref={GITHUB_BRANCH}"
    resp = requests.get(url)
    if resp.status_code == 403:
        # Rate limited — wait and retry
        time.sleep(5)
        resp = requests.get(url)
    resp.raise_for_status()
    return resp.json()

def github_download_file(path):
    """Download raw file content from GitHub."""
    url = f"{GITHUB_RAW_BASE}/{path}"
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.content

print("Helper functions defined.")

# COMMAND ----------

# DBTITLE 1,Skill installer function
def install_skill(skill_name, skill_gh_path):
    """Recursively download a skill directory from GitHub and upload to workspace."""
    target_dir = f"{WORKSPACE_SKILLS_DIR}/{skill_name}"
    ws_mkdirs(target_dir)
    
    files_uploaded = []
    
    def process_directory(gh_dir_path, ws_dir_path):
        items = github_list_dir(gh_dir_path)
        for item in items:
            if item["type"] == "file":
                content = github_download_file(item["path"])
                ws_file_path = f"{ws_dir_path}/{item['name']}"
                ws_upload_file(ws_file_path, content)
                files_uploaded.append(ws_file_path)
            elif item["type"] == "dir":
                sub_ws_dir = f"{ws_dir_path}/{item['name']}"
                ws_mkdirs(sub_ws_dir)
                process_directory(item["path"], sub_ws_dir)
    
    process_directory(skill_gh_path, target_dir)
    return files_uploaded

print("Skill installer function defined.")

# COMMAND ----------

# DBTITLE 1,Discover available skills
# List all available skills from GitHub
items = github_list_dir(GITHUB_SKILLS_PATH)
skill_dirs = [
    item for item in items 
    if item["type"] == "dir" and item["name"] not in SKIP_DIRS
]

print(f"Found {len(skill_dirs)} skills to install:")
for s in skill_dirs:
    print(f"  - {s['name']}")

# COMMAND ----------

# DBTITLE 1,Install all skills
# Create the base skills directory
ws_mkdirs(WORKSPACE_SKILLS_DIR)

total = len(skill_dirs)
succeeded = []
failed = []

for i, skill in enumerate(skill_dirs, 1):
    skill_name = skill["name"]
    skill_gh_path = skill["path"]
    print(f"[{i}/{total}] Installing {skill_name}...", end=" ")
    try:
        files = install_skill(skill_name, skill_gh_path)
        succeeded.append((skill_name, len(files)))
        print(f"OK ({len(files)} files)")
    except Exception as e:
        failed.append((skill_name, str(e)))
        print(f"FAILED: {e}")

print(f"\n{'='*50}")
print(f"Installation complete!")
print(f"  Succeeded: {len(succeeded)}/{total}")
print(f"  Failed:    {len(failed)}/{total}")
print(f"  Location:  /Workspace{WORKSPACE_SKILLS_DIR}")

if failed:
    print(f"\nFailed skills:")
    for name, err in failed:
        print(f"  - {name}: {err}")