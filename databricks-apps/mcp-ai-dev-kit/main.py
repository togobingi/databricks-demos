"""Databricks App: AI Dev Kit MCP Server.

Clones the AI Dev Kit from GitHub, registers all MCP tools and
skills (as MCP prompts), distributes skills to the workspace for
Genie Code, then serves over Streamable HTTP.
"""

import io
import logging
import os
import subprocess
import sys
import time
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CLONE_DIR = Path("/tmp/ai-dev-kit")
REPO_URL = os.environ.get(
    "GITHUB_REPO_URL",
    "https://github.com/databricks-solutions/ai-dev-kit.git",
)
BRANCH = os.environ.get("GITHUB_BRANCH", "main")
MAX_RETRIES = 3


# --- Phase 1: Clone and set up imports ---


def _bootstrap():
    """Clone the AI Dev Kit repo and add packages to sys.path.

    Retries up to MAX_RETRIES times with exponential backoff (all within
    ~1 minute). If all retries fail and a previous clone exists, proceeds
    with stale code. If no previous clone exists, raises RuntimeError.
    """
    clone_succeeded = False

    has_valid_clone = (
        CLONE_DIR.exists() and (CLONE_DIR / ".git").is_dir()
    )

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            if has_valid_clone:
                subprocess.run(
                    ["git", "-C", str(CLONE_DIR), "pull", "--ff-only"],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                logger.info("Pulled latest in %s", CLONE_DIR)
            else:
                # Remove any partial clone from a previous failed attempt
                if CLONE_DIR.exists():
                    import shutil

                    shutil.rmtree(CLONE_DIR)
                    logger.info("Removed incomplete clone at %s", CLONE_DIR)
                subprocess.run(
                    [
                        "git",
                        "clone",
                        "--depth",
                        "1",
                        "--branch",
                        BRANCH,
                        REPO_URL,
                        str(CLONE_DIR),
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                has_valid_clone = True
                logger.info("Cloned %s → %s", REPO_URL, CLONE_DIR)
            clone_succeeded = True
            break
        except subprocess.CalledProcessError as e:
            logger.warning(
                "Git attempt %d/%d failed: %s",
                attempt,
                MAX_RETRIES,
                e.stderr.strip() if e.stderr else str(e),
            )
            if attempt < MAX_RETRIES:
                delay = 2**attempt  # 2s, 4s, 8s — total wait ~14s
                logger.info("Retrying in %ds...", delay)
                time.sleep(delay)

    if not clone_succeeded:
        if CLONE_DIR.exists() and (CLONE_DIR / ".git").is_dir():
            logger.warning(
                "All %d clone/pull attempts failed. "
                "Proceeding with previously cloned code in %s.",
                MAX_RETRIES,
                CLONE_DIR,
            )
        else:
            raise RuntimeError(
                f"Failed to clone {REPO_URL} after {MAX_RETRIES} attempts "
                f"and no previous clone exists at {CLONE_DIR}. "
                f"Check network connectivity and repo availability."
            )

    for pkg in ["databricks-tools-core", "databricks-mcp-server"]:
        path = str(CLONE_DIR / pkg)
        if path not in sys.path:
            sys.path.insert(0, path)


_bootstrap()

# Import the FastMCP server instance — this auto-registers all tools
# via @mcp.tool decorators in the server module
from databricks_mcp_server.server import mcp  # noqa: E402


# --- Phase 2: Register skills as MCP prompts ---


def _make_prompt_fn(skill_content):
    """Create a unique prompt function for each skill.

    Using a factory avoids the fragile pattern of redefining the same
    function name in a loop, which risks deduplication if FastMCP
    indexes by __name__.
    """

    def prompt_fn() -> str:
        return skill_content

    return prompt_fn


def _register_skills():
    """Load each skill markdown file and register as an MCP prompt.

    Skills are in databricks-skills/<name>/SKILL.md with YAML frontmatter:
        ---
        name: skill-name
        description: Brief description
        ---
        <markdown content with instructions, examples, patterns>

    Registered as MCP prompts so Genie Code can discover and use them.
    """
    import yaml

    skills_dir = CLONE_DIR / "databricks-skills"
    if not skills_dir.exists():
        logger.warning("Skills directory not found: %s", skills_dir)
        return

    count = 0
    for skill_dir in sorted(skills_dir.iterdir()):
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            continue

        content = skill_file.read_text(encoding="utf-8")

        # Parse YAML frontmatter
        name = skill_dir.name
        description = f"AI Dev Kit skill: {name}"
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                try:
                    meta = yaml.safe_load(parts[1])
                    name = meta.get("name", name)
                    description = meta.get("description", description)
                    content = parts[2].strip()
                except yaml.YAMLError:
                    pass

        # Register with a unique function per skill via factory
        mcp.prompt(name=name, description=description)(
            _make_prompt_fn(content)
        )
        count += 1

    logger.info("Registered %d skills as MCP prompts", count)


_register_skills()


# --- Phase 2b: Distribute skills to workspace for Genie Code ---
# Genie Code reads skills from Workspace/.assistant/skills/<name>/SKILL.md
# (workspace-level skills, accessible to all users).
# We upload all skills there so Genie Code can use them natively without MCP.
#
# Three sources:
#   1. Databricks skills — from the cloned ai-dev-kit repo
#   2. MLflow skills — from github.com/mlflow/skills
#   3. APX skills — from github.com/databricks-solutions/apx

MLFLOW_SKILLS_BASE_URL = "https://raw.githubusercontent.com/mlflow/skills/main"
MLFLOW_SKILL_NAMES = [
    "agent-evaluation",
    "analyze-mlflow-chat-session",
    "analyze-mlflow-trace",
    "instrumenting-with-mlflow-tracing",
    "mlflow-onboarding",
    "querying-mlflow-metrics",
    "retrieving-mlflow-traces",
    "searching-mlflow-docs",
]

APX_SKILLS_BASE_URL = "https://raw.githubusercontent.com/databricks-solutions/apx/main/skills/apx"
APX_SKILL_FILES = [
    "SKILL.md",
    "backend-patterns.md",
    "frontend-patterns.md",
]

WORKSPACE_SKILLS_DIR = "/Workspace/.assistant/skills"
SKIP_SKILLS = {"TEMPLATE"}


def _upload_skill_file(w, target_path, content_bytes):
    """Upload a single file to the workspace using the import API.

    Uses workspace.import_() with RAW format, which works for arbitrary
    files at any workspace path (unlike workspace.upload() which fails
    at certain paths like .assistant/skills/).
    """
    import base64
    from databricks.sdk.service.workspace import ImportFormat

    w.workspace.import_(
        path=target_path,
        content=base64.b64encode(content_bytes).decode(),
        format=ImportFormat.RAW,
        overwrite=True,
    )


def _distribute_skills():
    """Upload all AI Dev Kit skills to the workspace for Genie Code.

    Runs best-effort — failures are logged but don't prevent the app
    from starting. Skills that already exist are overwritten to ensure
    the latest version.
    """
    import httpx
    from databricks.sdk import WorkspaceClient

    try:
        w = WorkspaceClient()
    except Exception as e:
        logger.warning("Could not create WorkspaceClient for skill distribution: %s", e)
        return

    total = 0

    # 1. Databricks skills (from cloned repo)
    skills_dir = CLONE_DIR / "databricks-skills"
    if skills_dir.exists():
        for skill_dir in sorted(skills_dir.iterdir()):
            if not skill_dir.is_dir() or skill_dir.name in SKIP_SKILLS:
                continue
            try:
                target_dir = f"{WORKSPACE_SKILLS_DIR}/{skill_dir.name}"
                w.workspace.mkdirs(target_dir)
                for f in skill_dir.iterdir():
                    if f.is_file() and not f.name.startswith("."):
                        _upload_skill_file(
                            w,
                            f"{target_dir}/{f.name}",
                            f.read_bytes(),
                        )
                total += 1
            except Exception as e:
                logger.warning("Failed to upload skill %s: %s", skill_dir.name, e)

    # 2. MLflow skills (fetched from GitHub)
    for skill_name in MLFLOW_SKILL_NAMES:
        try:
            url = f"{MLFLOW_SKILLS_BASE_URL}/{skill_name}/SKILL.md"
            resp = httpx.get(url, timeout=15, follow_redirects=True)
            resp.raise_for_status()
            target_dir = f"{WORKSPACE_SKILLS_DIR}/{skill_name}"
            w.workspace.mkdirs(target_dir)
            _upload_skill_file(w, f"{target_dir}/SKILL.md", resp.content)
            total += 1
        except Exception as e:
            logger.warning("Failed to fetch MLflow skill %s: %s", skill_name, e)

    # 3. APX skill (fetched from GitHub — has multiple files)
    try:
        target_dir = f"{WORKSPACE_SKILLS_DIR}/databricks-app-apx"
        w.workspace.mkdirs(target_dir)
        for filename in APX_SKILL_FILES:
            url = f"{APX_SKILLS_BASE_URL}/{filename}"
            resp = httpx.get(url, timeout=15, follow_redirects=True)
            resp.raise_for_status()
            _upload_skill_file(w, f"{target_dir}/{filename}", resp.content)
        total += 1
    except Exception as e:
        logger.warning("Failed to fetch APX skill: %s", e)

    logger.info("Distributed %d skills to %s", total, WORKSPACE_SKILLS_DIR)


_distribute_skills()


# --- Phase 3: Create ASGI app per Genie Code requirements ---
# Per https://docs.databricks.com/aws/en/genie-code/mcp:
#   1. App must be stateless: stateless_http=True
#   2. MCP endpoint must be at /mcp: path="/mcp"
#   3. CORS must be scoped to workspace URL

from starlette.middleware import Middleware  # noqa: E402
from starlette.middleware.cors import CORSMiddleware  # noqa: E402

# DATABRICKS_HOST is auto-injected by the Databricks Apps platform.
# It may or may not include the https:// scheme, so normalize it.
_host = os.environ.get("DATABRICKS_HOST", "")
if _host and not _host.startswith("https://"):
    _host = f"https://{_host}"
WORKSPACE_URL = _host.rstrip("/")

app = mcp.http_app(
    path="/mcp",
    stateless_http=True,
    middleware=[
        Middleware(
            CORSMiddleware,
            allow_origins=[WORKSPACE_URL] if WORKSPACE_URL else ["*"],
            allow_credentials=bool(WORKSPACE_URL),
            allow_methods=["*"],
            allow_headers=["*"],
        )
    ],
)

if __name__ == "__main__":
    import uvicorn  # noqa: E402

    logger.info("Starting MCP server (stateless, CORS enabled)...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
