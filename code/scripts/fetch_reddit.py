#!/usr/bin/env python3
"""Fetch Reddit posts mentioning a project, saving as markdown.

Usage:
    python scripts/fetch_reddit.py --project crewai --since 2026-03-11
    python scripts/fetch_reddit.py --project duckdb --since 2026-03-11 --fetch-comments

No API key required (uses public JSON endpoints).
Output: data/context/{project}/community/reddit-*.md
"""
from __future__ import annotations

import argparse
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx
import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "configs" / "projects"
DATA_DIR = ROOT / "data" / "context"

USER_AGENT = "ai-detectability-research/0.1 (research bot)"


def load_project(project: str) -> dict:
    path = CONFIG_DIR / f"{project}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Project config not found: {path}")
    with open(path) as f:
        return yaml.safe_load(f)


def _date_to_ts(date_str: str) -> float:
    return datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp()


def _clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text[:80].strip("-")


def search_reddit(
    client: httpx.Client, query: str, limit: int = 25,
    since: str | None = None, before: str | None = None,
) -> list[dict]:
    url = "https://www.reddit.com/search.json"
    params = {
        "q": query,
        "sort": "relevance",
        "t": "all" if (since or before) else "year",
        "limit": min(limit, 100),
    }
    for attempt in range(5):
        resp = client.get(url, params=params)
        if resp.status_code != 429:
            break
        wait = 60 * (attempt + 1)
        print(f"  Rate limited. Waiting {wait}s... (attempt {attempt + 1}/5)")
        time.sleep(wait)
    if resp.status_code != 200:
        print(f"  Failed to search Reddit: {resp.status_code}")
        return []

    since_ts = _date_to_ts(since) if since else None
    before_ts = _date_to_ts(before) if before else None

    posts = []
    for child in resp.json().get("data", {}).get("children", []):
        post = child["data"]
        created = post.get("created_utc", 0)
        if since_ts and created < since_ts:
            continue
        if before_ts and created >= before_ts:
            continue
        posts.append({
            "id": post["id"],
            "subreddit": post.get("subreddit", ""),
            "title": post.get("title", ""),
            "selftext": post.get("selftext", ""),
            "permalink": post.get("permalink", ""),
            "score": post.get("score", 0),
            "num_comments": post.get("num_comments", 0),
            "created_utc": created,
            "author": post.get("author", ""),
        })
    return posts


def fetch_post_comments(client: httpx.Client, permalink: str, limit: int = 10) -> list[dict]:
    url = f"https://www.reddit.com{permalink}.json"
    params = {"limit": limit, "sort": "best"}
    for attempt in range(5):
        resp = client.get(url, params=params)
        if resp.status_code != 429:
            break
        wait = 60 * (attempt + 1)
        print(f"    Rate limited. Waiting {wait}s... (attempt {attempt + 1}/5)")
        time.sleep(wait)
    if resp.status_code != 200:
        return []

    data = resp.json()
    if len(data) < 2:
        return []

    comments = []
    for child in data[1].get("data", {}).get("children", []):
        if child["kind"] != "t1":
            continue
        c = child["data"]
        comments.append({
            "author": c.get("author", ""),
            "body": c.get("body", ""),
            "score": c.get("score", 0),
        })
    return comments


def post_to_markdown(post: dict, comments: list[dict] | None = None) -> str:
    created = datetime.fromtimestamp(post["created_utc"], tz=timezone.utc).strftime("%Y-%m-%d")
    lines = [
        f"# {post['title']}",
        "",
        f"**r/{post['subreddit']}** | Score: {post['score']} | "
        f"Comments: {post['num_comments']} | Date: {created}",
        f"**Author:** {post['author']}",
        f"**URL:** https://www.reddit.com{post['permalink']}",
        "",
    ]

    body = _clean_text(post.get("selftext", ""))
    if body:
        lines.append(body)
        lines.append("")

    if comments:
        lines.append("## Top Comments")
        lines.append("")
        for c in comments:
            body = _clean_text(c.get("body", ""))
            if body:
                lines.append(f"**{c['author']}** (score: {c['score']}):")
                lines.append(body)
                lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Fetch Reddit posts for a project")
    parser.add_argument("--project", required=True, help="Project key (crewai, duckdb, langchain)")
    parser.add_argument("--limit", type=int, default=25, help="Max posts per query")
    parser.add_argument("--fetch-comments", action="store_true", help="Also fetch top comments")
    parser.add_argument("--since", help="Only posts after this date (YYYY-MM-DD)")
    parser.add_argument("--before", help="Only posts before this date (YYYY-MM-DD)")
    args = parser.parse_args()

    config = load_project(args.project)
    keywords = config.get("reddit_keywords", [])
    if not keywords:
        print(f"No reddit_keywords configured for '{args.project}'")
        return

    community_dir = DATA_DIR / args.project / "community"
    community_dir.mkdir(parents=True, exist_ok=True)

    seen_ids: set[str] = set()
    saved = 0

    headers = {"User-Agent": USER_AGENT}
    with httpx.Client(timeout=30, headers=headers, follow_redirects=True) as client:
        for term in keywords:
            print(f"Searching Reddit for: {term}")
            posts = search_reddit(client, term, args.limit, args.since, args.before)
            new_posts = [p for p in posts if p["id"] not in seen_ids]
            seen_ids.update(p["id"] for p in posts)
            print(f"  -> {len(posts)} results, {len(new_posts)} new")

            for post in new_posts:
                comments = []
                if args.fetch_comments and post["num_comments"] > 0:
                    comments = fetch_post_comments(client, post["permalink"])
                    time.sleep(1)

                slug = _slugify(post["title"])
                filename = f"reddit-{post['id']}-{slug}.md"
                md = post_to_markdown(post, comments)
                (community_dir / filename).write_text(md)
                saved += 1

            time.sleep(2)  # rate limit between queries

    print(f"\nDone. Saved {saved} posts to {community_dir}/")


if __name__ == "__main__":
    main()
