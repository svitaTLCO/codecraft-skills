#!/usr/bin/env python3
"""Content-security scan for codecraft-skills. Stdlib only.

Shipped SKILL.md text is auto-injected into agents, so this repo gates on
content hygiene as much as structure. The scan looks for things that must
never appear in skill text or repo docs: secret-looking literals,
credential assignments, remote-exec pipes (fetch piped into a shell), exfiltration-
shaped imperatives pointing at URLs, URLs off the allowlist, and classic
prompt-injection tells. Findings are hard-gated: any hit exits nonzero.

Usage: python3 scripts/security_scan.py [repo_root]
Exits 0 when clean, 1 otherwise.
"""

import re
import sys
from pathlib import Path

EXCLUDE_DIRS = {".git"}
MAX_FILE_BYTES = 1_000_000

ALLOWED_URL_HOSTS = {
    "anthropic.com",
    "refactoring.guru",
    "www.refactoring.guru",
    "shields.io",
    "img.shields.io",
    "example.com",
    "example.org",
    "example.net",
    "localhost",
    "127.0.0.1",
}
# github.com is allowed only for paths under the project's own org prefix.
ALLOWED_GITHUB_PATH_PREFIXES = ("/svitaTLCO/",)

SECRET_RE = re.compile(
    r"sk-[A-Za-z0-9]{16,}"
    r"|\bghp_[A-Za-z0-9]{20,}\b"
    r"|\bAKIA[A-Z0-9]{16}\b"
    r"|\bxox[baprs]-[A-Za-z0-9-]{10,}\b"
    r"|AIza[0-9A-Za-z_-]{35}"
    r"|-----BEGIN([ A-Z])*PRIVATE KEY-----"
)
CREDENTIAL_RE = re.compile(
    r"(?i)\b(password|passwd|secret|api_?key|auth_?token|access_?token)\b"
    r"\s*[:=]\s*['\"]?[A-Za-z0-9+/=_\-]{12,}"
)
REMOTE_EXEC_RE = re.compile(
    r"\b(curl|wget)\b[^\n|]{0,120}\|\s*(?:sudo\s+)?(?:ba|z|da|tc|fi)?sh\b"
)
EXFIL_RE = re.compile(
    r"(?i)\b(post|upload|send|transmit|copy|forward)\s+"
    r"(?:all\s+|these?\s+|the\s+|any\s+)?"
    r"[a-z]*(data|files?|env|environment|configs?|secrets?|keys?|credentials|"
    r"logs?|history|prompts?|contexts?|memories?|sessions?)\b"
    r"[^\n]{0,60}\b(to|at)\s+[\"']?https?://"
)
INJECTION_RE = re.compile(
    r"(?i)(ignore|disregard|forget|override|bypass)\s+(?:all\s+)?"
    r"(?:previous|prior|above|earlier|original)\s+(?:instructions|rules|guidelines|context|prompts?|system)"
    r"|(?:reveal|print|show|leak|output|echo)\s+(?:your|the|my)\s+"
    r"(?:full\s+|entire\s+|complete\s+|system\s+)?(?:system\s+)?(?:prompt|instructions|message)"
    r"|\bdo\s+not\s+tell\s+the\s+user\b"
)
URL_RE = re.compile(r"https?://[^\s)\"'<>\]]+")


def url_allowed(url):
    m = re.match(r"https?://([^/]+)(/.*)?$", url)
    if not m:
        return False
    host = m.group(1).lower()
    path = m.group(2) or ""
    if host in ALLOWED_URL_HOSTS:
        return True
    if host == "github.com":
        return any(path.startswith(p) for p in ALLOWED_GITHUB_PATH_PREFIXES)
    return False


def collect_files(root):
    files = []
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        if any(part in EXCLUDE_DIRS for part in p.parent.parts):
            continue
        try:
            if p.stat().st_size > MAX_FILE_BYTES:
                continue
        except OSError:
            continue
        files.append(p)
    return files


def scan_file(path, root):
    findings = []
    rel = path.relative_to(root)
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (UnicodeDecodeError, OSError):
        return findings
    for lineno, line in enumerate(lines, 1):
        for name, rx in (
            ("secret literal", SECRET_RE),
            ("credential assignment", CREDENTIAL_RE),
            ("remote-exec pipe", REMOTE_EXEC_RE),
            ("exfiltration imperative", EXFIL_RE),
            ("injection tell", INJECTION_RE),
        ):
            m = rx.search(line)
            if m:
                findings.append(f"{rel}:{lineno}: {name}: {line.strip()[:100]}")
        for um in URL_RE.finditer(line):
            if not url_allowed(um.group(0)):
                findings.append(
                    f"{rel}:{lineno}: off-whitelist URL: {um.group(0)[:80]}"
                )
    return findings


def main():
    root = (
        Path(sys.argv[1]) if len(sys.argv) > 1
        else Path(__file__).resolve().parent.parent
    )
    files = collect_files(root)
    all_findings = []
    for f in files:
        all_findings.extend(scan_file(f, root))
    print(f"security scan: {len(files)} files checked")
    if all_findings:
        for item in all_findings[:10]:
            print(f"FAIL  {item}")
        if len(all_findings) > 10:
            print(f"      ... and {len(all_findings) - 10} more")
        return 1
    print("PASS  no secret literals, credential assignments, remote-exec "
          "pipes, exfiltration imperatives, off-whitelist URLs, or injection tells")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
