import unittest
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

import build


class FrontMatterTests(unittest.TestCase):
    def test_parses_fields(self):
        meta, body = build.parse_front_matter("---\ntitle: Hello: World\ndate: 2026-10-01\ntags: a, b\n---\nBody text")
        self.assertEqual(meta["title"], "Hello: World")   # only the first colon splits
        self.assertEqual(body, "Body text")

    def test_missing_block_or_field(self):
        with self.assertRaises(ValueError):
            build.parse_front_matter("No front matter here")
        with self.assertRaises(ValueError):
            build.parse_front_matter("---\ntitle: x\n---\nbody")

    def test_slugify(self):
        self.assertEqual(build.slugify("Ornstein & Smough: A Guide!"), "ornstein-smough-a-guide")


class SiteTests(unittest.TestCase):
    def test_posts_load_sorted_newest_first(self):
        posts = build.load_posts()
        self.assertGreaterEqual(len(posts), 5)
        self.assertEqual(posts, sorted(posts, key=lambda p: p.date, reverse=True))
        for p in posts:
            self.assertTrue(p.title and p.summary and p.tags)
            self.assertGreaterEqual(p.reading_minutes, 1)

    def test_build_writes_every_page(self):
        with TemporaryDirectory() as tmp:
            original = build.OUT
            build.OUT = Path(tmp) / "docs"
            try:
                files = build.build()
                names = {f.relative_to(build.OUT).as_posix() for f in files}
                self.assertIn("index.html", names)
                self.assertIn("feed.xml", names)
                self.assertIn("posts/first-hours-in-lordran.html", names)
                self.assertIn("tags/guide.html", names)
                page = (build.OUT / "posts/age-of-fire-explained.html").read_text()
                self.assertIn("The Age of Fire, Explained", page)
                self.assertIn('id="the-first-flame"', page)   # headings get anchors for the table of contents
            finally:
                build.OUT = original

    def test_reading_time(self):
        post = build.Post("t", date(2026, 1, 1), "t", [], "", "", words=450)
        self.assertEqual(post.reading_minutes, 3)


if __name__ == "__main__":
    unittest.main()
