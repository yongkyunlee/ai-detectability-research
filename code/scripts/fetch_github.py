#!/usr/bin/env python3
"""Fetch GitHub issues and releases for a project, saving as markdown.

Usage:
    python scripts/fetch_github.py --project crewai --since 2026-03-11
    python scripts/fetch_github.py --project duckdb --since 2026-03-11 --before 2026-03-18

Requires GITHUB_TOKEN environment variable.
Output: data/context/{project}/issues/*.md, data/context/{project}/releases/*.md
"""
from __future__ import annotations

import argparse
import asyncio
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx
import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "configs" / "projects"
DATA_DIR = ROOT / "data" / "context"

GITHUB_API = "https://api.github.com"
TOKEN = os.environ.get("GITHUB_TOKEN", "")
if not TOKEN:
    print("Error: GITHUB_TOKEN environment variable is required.")
    print("Create one at: https://github.com/settings/tokens")
    sys.exit(1)

HEADERS = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {TOKEN}",
}

SEM = asyncio.Semaphore(10)


def load_project(project: str) -> dict:
    path = CONFIG_DIR / f"{project}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Project config not found: {path}")
    with open(path) as f:
        return yaml.safe_load(f)


def _parse_day(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)


def _parse_github_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _in_window(dt: datetime, since: datetime | None, before: datetime | None) -> bool:
    if since and dt < since:
        return False
    if before and dt >= before:
        return False
    return True


def _clean_text(text: str) -> str:
    """Strip marketing copy and clean up for factual context."""
    if not text:
        return ""
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    # Collapse multiple newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text[:80].strip("-")


# -- HTTP helpers -----------------------------------------------------------

async def paginate(client: httpx.AsyncClient, url: str, params: dict | None = None,
                   label: str = "", early_stop=None) -> list:
    results = []
    params = dict(params or {})
    params.setdefault("per_page", 100)
    page = 1
    while True:
        params["page"] = page
        if label:
            print(f"  {label}: page {page}...", flush=True)
        resp = await client.get(url, params=params, headers=HEADERS)
        if resp.status_code == 403:
            reset = int(resp.headers.get("X-RateLimit-Reset", time.time() + 60))
            wait = max(reset - int(time.time()), 1)
            print(f"  Rate limited. Waiting {wait}s...", flush=True)
            await asyncio.sleep(wait)
            continue
        resp.raise_for_status()
        data = resp.json()
        if not data:
            break
        results.extend(data)
        if early_stop and early_stop(data):
            break
        page += 1
        remaining = int(resp.headers.get("X-RateLimit-Remaining", 100))
        if remaining < 10:
            await asyncio.sleep(2)
    return results


async def fetch_comments(client: httpx.AsyncClient, url: str) -> list:
    async with SEM:
        return await paginate(client, url)


# -- Issue → markdown ------------------------------------------------------

def issue_to_markdown(issue: dict, comments: list[dict]) -> str:
    lines = [
        f"# {issue['title']}",
        "",
        f"**Issue #{issue['number']}** | State: {issue['state']} | "
        f"Created: {issue.get('created_at', '')[:10]} | "
        f"Updated: {issue.get('updated_at', '')[:10]}",
        f"**Author:** {issue.get('user', {}).get('login', 'unknown')}",
    ]
    labels = [l.get("name", "") for l in issue.get("labels", [])]
    if labels:
        lines.append(f"**Labels:** {', '.join(labels)}")
    lines.append("")

    body = _clean_text(issue.get("body") or "")
    if body:
        lines.append(body)
        lines.append("")

    if comments:
        lines.append("## Comments")
        lines.append("")
        for c in comments[:10]:  # top 10 comments
            author = c.get("user", {}).get("login", "unknown")
            body = _clean_text(c.get("body", ""))
            if body:
                lines.append(f"**{author}:**")
                lines.append(body)
                lines.append("")

    return "\n".join(lines)


# -- Release → markdown ----------------------------------------------------

def release_to_markdown(release: dict) -> str:
    lines = [
        f"# {release.get('name') or release.get('tag_name', 'Release')}",
        "",
        f"**Tag:** {release.get('tag_name', '')} | "
        f"**Date:** {release.get('created_at', '')[:10]}",
        "",
    ]
    body = _clean_text(release.get("body") or "")
    if body:
        lines.append(body)
    return "\n".join(lines)


# -- Fetchers --------------------------------------------------------------

async def fetch_issues(
    client: httpx.AsyncClient, repo: str,
    since: str | None, before: str | None,
) -> list[tuple[dict, list[dict]]]:
    params = {"state": "all", "sort": "updated", "direction": "desc"}
    if since:
        params["since"] = f"{since}T00:00:00Z"

    url = f"{GITHUB_API}/repos/{repo}/issues"
    raw = await paginate(client, url, params, label=f"{repo} issues")

    since_dt = _parse_day(since)
    before_dt = _parse_day(before)
    issues = [
        i for i in raw
        if "pull_request" not in i
        and _in_window(_parse_github_dt(i["updated_at"]), since_dt, before_dt)
    ]

    results = []
    tasks = []
    task_issues = []
    for issue in issues:
        if issue.get("comments", 0) > 0:
            comments_url = f"{GITHUB_API}/repos/{repo}/issues/{issue['number']}/comments"
            tasks.append(fetch_comments(client, comments_url))
            task_issues.append(issue)
        else:
            results.append((issue, []))

    if tasks:
        print(f"  {repo}: fetching comments for {len(tasks)} issues...", flush=True)
        fetched = await asyncio.gather(*tasks)
        for issue, comments in zip(task_issues, fetched):
            results.append((issue, comments))

    return results


async def fetch_releases(
    client: httpx.AsyncClient, repo: str,
    since: str | None, before: str | None,
) -> list[dict]:
    releases = await paginate(client, f"{GITHUB_API}/repos/{repo}/releases", label=f"{repo} releases")
    since_dt = _parse_day(since)
    before_dt = _parse_day(before)
    return [
        r for r in releases
        if r.get("created_at")
        and _in_window(_parse_github_dt(r["created_at"]), since_dt, before_dt)
    ]


# -- Main -------------------------------------------------------------------

async def amain(project: str, since: str | None, before: str | None):
    config = load_project(project)
    repos = config.get("github", [])
    if not repos:
        print(f"No github repos configured for '{project}'")
        return

    issues_dir = DATA_DIR / project / "issues"
    releases_dir = DATA_DIR / project / "releases"
    issues_dir.mkdir(parents=True, exist_ok=True)
    releases_dir.mkdir(parents=True, exist_ok=True)

    async with httpx.AsyncClient(timeout=30) as client:
        for repo in repos:
            print(f"Fetching {repo}...", flush=True)

            # Issues
            issues = await fetch_issues(client, repo, since, before)
            for issue, comments in issues:
                slug = _slugify(issue["title"])
                filename = f"issue-{issue['number']}-{slug}.md"
                md = issue_to_markdown(issue, comments)
                (issues_dir / filename).write_text(md)
            print(f"  Saved {len(issues)} issues to {issues_dir}/", flush=True)

            # Releases
            releases = await fetch_releases(client, repo, since, before)
            for release in releases:
                tag = release.get("tag_name", "unknown")
                safe_tag = re.sub(r"[^\w.-]", "_", tag)
                filename = f"release-{safe_tag}.md"
                md = release_to_markdown(release)
                (releases_dir / filename).write_text(md)
            print(f"  Saved {len(releases)} releases to {releases_dir}/", flush=True)


def main():
    parser = argparse.ArgumentParser(description="Fetch GitHub issues & releases for a project")
    parser.add_argument("--project", required=True, help="Project key (crewai, duckdb, langchain)")
    parser.add_argument("--since", help="Only items updated since this date (YYYY-MM-DD)")
    parser.add_argument("--before", help="Only items updated before this date (YYYY-MM-DD)")
    args = parser.parse_args()
    asyncio.run(amain(args.project, args.since, args.before))


if __name__ == "__main__":
    main()
