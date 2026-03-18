#!/usr/bin/env python3
"""Fetch Hacker News threads mentioning a project, saving as markdown.

Uses the HN Algolia API (free, no auth required).

Usage:
    python scripts/fetch_hn.py --project crewai --since 2026-03-11
    python scripts/fetch_hn.py --project duckdb --since 2026-03-11 --before 2026-03-18

Output: data/context/{project}/community/hn-*.md
"""
from __future__ import annotations

import argparse
import asyncio
import re
from datetime import datetime, timezone
from pathlib import Path

import httpx
import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "configs" / "projects"
DATA_DIR = ROOT / "data" / "context"

HN_API = "https://hn.algolia.com/api/v1"


def load_project(project: str) -> dict:
    path = CONFIG_DIR / f"{project}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Project config not found: {path}")
    with open(path) as f:
        return yaml.safe_load(f)


def _date_to_ts(date_str: str) -> int:
    return int(datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())


def _build_numeric_filters(since: str | None, before: str | None) -> str:
    filters = []
    if since:
        filters.append(f"created_at_i>{_date_to_ts(since)}")
    if before:
        filters.append(f"created_at_i<{_date_to_ts(before)}")
    return ",".join(filters) if filters else "created_at_i>0"


def _clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"&#x27;", "'", text)
    text = re.sub(r"&quot;", '"', text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text[:80].strip("-")


async def search_stories(
    client: httpx.AsyncClient, query: str, limit: int = 50,
    since: str | None = None, before: str | None = None,
) -> list[dict]:
    params = {
        "query": query,
        "tags": "story",
        "hitsPerPage": min(limit, 50),
        "numericFilters": _build_numeric_filters(since, before),
    }
    resp = await client.get(f"{HN_API}/search", params=params)
    resp.raise_for_status()
    return resp.json().get("hits", [])


async def fetch_item_comments(
    client: httpx.AsyncClient, item_id: int, limit: int = 10,
) -> list[dict]:
    resp = await client.get(f"{HN_API}/items/{item_id}")
    resp.raise_for_status()
    item = resp.json()
    children = item.get("children", [])[:limit]
    return [
        {
            "author": c.get("author"),
            "text": c.get("text", ""),
        }
        for c in children
        if c.get("text")
    ]


def story_to_markdown(story: dict, comments: list[dict] | None = None) -> str:
    title = story.get("title", "Untitled")
    created = story.get("created_at", "")[:10]
    points = story.get("points", 0)
    num_comments = story.get("num_comments", 0)
    author = story.get("author", "unknown")
    url = story.get("url", "")
    hn_url = f"https://news.ycombinator.com/item?id={story.get('objectID', '')}"

    lines = [
        f"# {title}",
        "",
        f"**HN** | Points: {points} | Comments: {num_comments} | Date: {created}",
        f"**Author:** {author}",
        f"**HN URL:** {hn_url}",
    ]
    if url:
        lines.append(f"**Link:** {url}")
    lines.append("")

    story_text = _clean_text(story.get("story_text", ""))
    if story_text:
        lines.append(story_text)
        lines.append("")

    if comments:
        lines.append("## Top Comments")
        lines.append("")
        for c in comments:
            text = _clean_text(c.get("text", ""))
            if text:
                lines.append(f"**{c.get('author', 'anon')}:**")
                lines.append(text)
                lines.append("")

    return "\n".join(lines)


async def async_main():
    parser = argparse.ArgumentParser(description="Fetch HN threads for a project")
    parser.add_argument("--project", required=True, help="Project key (crewai, duckdb, langchain)")
    parser.add_argument("--limit", type=int, default=30, help="Max stories per keyword")
    parser.add_argument("--num-comments", type=int, default=10, help="Max comments per story")
    parser.add_argument("--since", help="Only items after this date (YYYY-MM-DD)")
    parser.add_argument("--before", help="Only items before this date (YYYY-MM-DD)")
    args = parser.parse_args()

    config = load_project(args.project)
    keywords = config.get("hn_keywords", [])
    if not keywords:
        print(f"No hn_keywords configured for '{args.project}'")
        return

    community_dir = DATA_DIR / args.project / "community"
    community_dir.mkdir(parents=True, exist_ok=True)

    seen_ids: set[str] = set()
    all_stories: list[dict] = []

    async with httpx.AsyncClient(timeout=30) as client:
        for keyword in keywords:
            print(f"Searching HN for: {keyword}")
            stories = await search_stories(client, keyword, args.limit, args.since, args.before)
            new_stories = [s for s in stories if s["objectID"] not in seen_ids]
            seen_ids.update(s["objectID"] for s in stories)
            print(f"  -> {len(stories)} results, {len(new_stories)} new")
            all_stories.extend(new_stories)

        # Fetch comments for all stories
        if all_stories:
            print(f"Fetching comments for {len(all_stories)} stories...")
            comment_results = await asyncio.gather(*(
                fetch_item_comments(client, int(s["objectID"]), args.num_comments)
                for s in all_stories
            ))
            for story, comments in zip(all_stories, comment_results):
                story["_comments"] = comments

    # Save as markdown
    saved = 0
    for story in all_stories:
        slug = _slugify(story.get("title", "untitled"))
        oid = story["objectID"]
        filename = f"hn-{oid}-{slug}.md"
        md = story_to_markdown(story, story.get("_comments"))
        (community_dir / filename).write_text(md)
        saved += 1

    print(f"\nDone. Saved {saved} stories to {community_dir}/")


if __name__ == "__main__":
    asyncio.run(async_main())
