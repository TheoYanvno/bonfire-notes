"""Static site generator: turns Markdown posts into a blog in docs/ (ready for GitHub Pages).

Usage:  python build.py
"""
import html
import math
import re
import shutil
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import markdown
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).parent
POSTS = ROOT / "posts"
OUT = ROOT / "docs"
SITE = {"title": "Bonfire Notes", "tagline": "A Dark Souls fan blog: guides, lore and stories from Lordran", "url": "https://theoyanvno.github.io/bonfire-notes"}


@dataclass
class Post:
    title: str
    date: date
    slug: str
    tags: list[str]
    summary: str
    body_html: str
    words: int
    headings: list[tuple[str, str]] = field(default_factory=list)

    @property
    def reading_minutes(self) -> int:
        return max(1, math.ceil(self.words / 220))


def slugify(text: str) -> str:
    text = re.sub(r"[^a-z0-9\s-]", "", text.lower())
    return re.sub(r"[\s-]+", "-", text).strip("-")


def parse_front_matter(raw: str) -> tuple[dict, str]:
    """Reads the '---' block at the top of a post into a dict."""
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", raw, re.S)
    if not match:
        raise ValueError("Post is missing its --- front matter block")
    meta = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip()
    for required in ("title", "date"):
        if required not in meta:
            raise ValueError(f"Front matter needs a '{required}'")
    return meta, match.group(2)


def load_post(path: Path) -> Post:
    meta, body = parse_front_matter(path.read_text(encoding="utf-8"))
    md = markdown.Markdown(extensions=["toc", "smarty"])
    body_html = md.convert(body)
    # slug comes from the file name without the date prefix: 2026-10-05-first-hours.md -> first-hours
    slug = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", path.stem)
    headings = [(t["id"], t["name"]) for t in md.toc_tokens if t["level"] == 2]
    return Post(
        title=meta["title"],
        date=date.fromisoformat(meta["date"]),
        slug=slug,
        tags=[slugify(t) for t in meta.get("tags", "").split(",") if t.strip()],
        summary=meta.get("summary", ""),
        body_html=body_html,
        words=len(re.findall(r"\w+", body)),
        headings=headings,
    )


def load_posts() -> list[Post]:
    posts = [load_post(p) for p in POSTS.glob("*.md")]
    return sorted(posts, key=lambda p: p.date, reverse=True)


def rss(posts: list[Post]) -> str:
    items = "".join(
        f"<item><title>{html.escape(p.title)}</title><link>{SITE['url']}/posts/{p.slug}.html</link>"
        f"<guid>{SITE['url']}/posts/{p.slug}.html</guid><pubDate>{p.date.strftime('%a, %d %b %Y')} 00:00:00 GMT</pubDate>"
        f"<description>{html.escape(p.summary)}</description></item>"
        for p in posts
    )
    return (f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>{SITE["title"]}</title>'
            f"<link>{SITE['url']}</link><description>{html.escape(SITE['tagline'])}</description>{items}</channel></rss>")


def build() -> list[Path]:
    posts = load_posts()
    env = Environment(loader=FileSystemLoader(ROOT / "templates"), autoescape=select_autoescape(["html"]))
    tags = sorted({t for p in posts for t in p.tags})
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "posts").mkdir(parents=True)
    (OUT / "tags").mkdir()
    shutil.copytree(ROOT / "static", OUT / "static")
    written = []

    def write(rel: str, text: str):
        path = OUT / rel
        path.write_text(text, encoding="utf-8")
        written.append(path)

    common = {"site": SITE, "tags": tags, "year": date.today().year}
    write("index.html", env.get_template("index.html").render(posts=posts, root=".", heading=None, **common))
    for i, post in enumerate(posts):
        newer = posts[i - 1] if i > 0 else None
        older = posts[i + 1] if i + 1 < len(posts) else None
        write(f"posts/{post.slug}.html", env.get_template("post.html").render(post=post, newer=newer, older=older, root="..", **common))
    for tag in tags:
        tagged = [p for p in posts if tag in p.tags]
        write(f"tags/{tag}.html", env.get_template("index.html").render(posts=tagged, root="..", heading=f"Tagged “{tag}”", **common))
    write("about.html", env.get_template("about.html").render(root=".", **common))
    write("feed.xml", rss(posts))
    (OUT / ".nojekyll").touch()
    return written


if __name__ == "__main__":
    files = build()
    print(f"Built {len(files)} pages into {OUT.relative_to(ROOT)}/")
