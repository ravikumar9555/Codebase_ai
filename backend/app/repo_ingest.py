import hashlib
import re
import shutil
import subprocess
from pathlib import Path
from urllib.parse import urlparse
from .config import settings

ALLOWED_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".kt", ".go", ".rs",
    ".c", ".h", ".cpp", ".hpp", ".cs", ".php", ".rb", ".swift", ".scala",
    ".sql", ".html", ".css", ".scss", ".json", ".yaml", ".yml", ".toml",
    ".md", ".txt", ".xml", ".sh", ".properties", ".gradle"
}
IGNORED_DIRS = {
    ".git", "node_modules", "vendor", "dist", "build", "target",
    ".next", ".venv", "venv", "__pycache__", "coverage"
}
SECRET_NAMES = {
    ".env", ".env.local", ".env.production", "id_rsa", "id_ed25519",
    "credentials.json", "secrets.yaml", "secrets.yml"
}

def parse_github_url(url: str) -> tuple[str, str]:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != "github.com":
        raise ValueError("Only HTTPS URLs hosted on github.com are supported.")
    parts = [p for p in parsed.path.strip("/").split("/") if p]
    if len(parts) < 2:
        raise ValueError("URL must look like https://github.com/owner/repository")
    owner, name = parts[0], re.sub(r"\.git$", "", parts[1])
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", owner) or not re.fullmatch(r"[A-Za-z0-9_.-]+", name):
        raise ValueError("Invalid GitHub owner or repository name.")
    return owner, name


def safe_clone(url: str, branch: str | None, repo_id: str) -> tuple[Path, str, str, str]:
    owner, name = parse_github_url(url)
    target = Path(settings.repo_dir).resolve() / repo_id

    if target.exists():
        shutil.rmtree(target)

    target.parent.mkdir(parents=True, exist_ok=True)

    # If no branch was specified, let Git clone the repository's default branch.
    base_command = [
        "git",
        "-c", "protocol.ext.allow=never",
        "-c", "http.version=HTTP/1.1",
        "clone",
        "--depth", "1",
        "--no-tags",
    ]

    repository_url = f"https://github.com/{owner}/{name}.git"

    if branch and branch.strip():
        command = base_command + [
            "--branch", branch.strip(),
            "--",
            repository_url,
            str(target),
        ]
    else:
        command = base_command + [
            "--",
            repository_url,
            str(target),
        ]

    try:
        subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            timeout=180,
        )
    except subprocess.TimeoutExpired as e:
        shutil.rmtree(target, ignore_errors=True)
        raise ValueError("Repository clone timed out.") from e
    except subprocess.CalledProcessError as e:
        shutil.rmtree(target, ignore_errors=True)
        message = (e.stderr or "git clone failed")[-1200:]
        raise ValueError(f"Could not clone repository: {message}") from e

    sha = subprocess.run(
        ["git", "-C", str(target), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    ).stdout.strip()

    actual_branch = subprocess.run(
        ["git", "-C", str(target), "branch", "--show-current"],
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    ).stdout.strip()

    return target, owner, name, sha


def iter_source_files(root: Path):
    count = 0
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if any(part in IGNORED_DIRS for part in rel.parts):
            continue
        if path.name.lower() in SECRET_NAMES or path.name.startswith(".env"):
            continue
        if path.suffix.lower() not in ALLOWED_EXTENSIONS:
            continue
        try:
            if path.stat().st_size > settings.max_file_bytes:
                continue
            raw = path.read_bytes()
            if b"\x00" in raw:
                continue
            text = raw.decode("utf-8", errors="strict")
        except (OSError, UnicodeDecodeError):
            continue
        # Basic heuristic to avoid likely private key blocks / secret-bearing files.
        if "-----BEGIN PRIVATE KEY-----" in text or "-----BEGIN RSA PRIVATE KEY-----" in text:
            continue
        yield rel.as_posix(), text
        count += 1
        if count >= settings.max_files:
            break

def chunk_text(file_path: str, text: str):
    lines = text.splitlines()
    if not lines:
        return []
    size = max(10, settings.chunk_lines)
    overlap = min(max(0, settings.chunk_overlap), size - 1)
    chunks = []
    start = 0
    while start < len(lines):
        end = min(start + size, len(lines))
        content = "\n".join(lines[start:end]).strip()
        if content:
            digest = hashlib.sha256((file_path + str(start + 1) + content).encode()).hexdigest()
            chunks.append({
                "id": digest,
                "file_path": file_path,
                "start_line": start + 1,
                "end_line": end,
                "content": content,
            })
        if end == len(lines):
            break
        start = end - overlap
    return chunks
