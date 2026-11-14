from email.message import Message
import io
import json
from pathlib import Path
import tempfile
import unittest
from scripts.refresh_cards import refresh, validate_svg

GOOD = b'<svg xmlns="http://www.w3.org/2000/svg" width="400" height="100"><text>Followers: 21</text><text>Repositories: 14</text></svg>'
SOURCE = [{"file": "test.svg", "url": "https://example.com/card.svg", "markers": ["Followers"]}]


class Response(io.BytesIO):
    def __init__(self, body, content_type="image/svg+xml"):
        super().__init__(body)
        self.headers = Message()
        self.headers["Content-Type"] = content_type


class CardTests(unittest.TestCase):
    def test_real_metrics_are_required(self):
        self.assertIn("Followers: 21", validate_svg(GOOD, ["Followers"]))
        for body in [b"<html>Not found</html>", GOOD.replace(b"Followers", b"Visitors"), GOOD.replace(b"Followers: 21", b"Something went wrong")]:
            with self.assertRaises(ValueError):
                validate_svg(body, ["Followers"])

    def test_malformed_or_active_svg_is_refused(self):
        unsafe = [GOOD[:-6], GOOD.replace(b"<text>", b'<text onload="alert(1)">', 1), GOOD.replace(b"</svg>", b'<script>alert(1)</script></svg>'), b'<!DOCTYPE svg [<!ENTITY x SYSTEM "file:///etc/passwd">]>' + GOOD, GOOD.replace(b"</svg>", b'<image href="https://example.com/pixel.png"/></svg>')]
        for body in unsafe:
            with self.assertRaises(ValueError):
                validate_svg(body, ["Followers"])

    def test_activity_graph_can_use_an_inert_xhtml_heading(self):
        label = b'<foreignObject><h1 xmlns="http://www.w3.org/1999/xhtml">Followers: 21</h1></foreignObject>'
        self.assertIn("foreignObject", validate_svg(GOOD.replace(b"</svg>", label + b"</svg>"), ["Followers"]))
        for element in [b'<iframe src="https://example.com"/>', b'<img src="https://example.com"/>']:
            with self.assertRaises(ValueError):
                validate_svg(GOOD.replace(b"</svg>", b'<foreignObject><div xmlns="http://www.w3.org/1999/xhtml">' + element + b'</div></foreignObject></svg>'), ["Followers"])

    def test_success_records_provenance_and_normalizes_whitespace(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            result = refresh(root, SOURCE, lambda *a, **k: Response(GOOD), "2026-11-25T00:00:00+00:00")
            self.assertEqual(result, [("test.svg", "updated")])
            self.assertEqual((root / "assets/test.svg").read_text(), GOOD.decode() + "\n")
            self.assertEqual(json.loads((root / "assets/card-status.json").read_text())["test.svg"]["source"], SOURCE[0]["url"])

    def test_failed_or_invalid_provider_preserves_existing_image_and_timestamp(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            refresh(root, SOURCE, lambda *a, **k: Response(GOOD), "original")
            before = (root / "assets/card-status.json").read_bytes()
            for broken in [lambda *a, **k: Response(b"<html>Gone</html>", "text/html"), lambda *a, **k: Response(GOOD.replace(b"Followers", b"Error")), lambda *a, **k: (_ for _ in ()).throw(TimeoutError("timeout"))]:
                self.assertEqual(refresh(root, SOURCE, broken), [("test.svg", "kept")])
                self.assertEqual((root / "assets/test.svg").read_text(), GOOD.decode() + "\n")
                self.assertEqual((root / "assets/card-status.json").read_bytes(), before)

    def test_no_snapshot_fails_instead_of_creating_a_broken_image(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(RuntimeError):
                refresh(Path(temporary), SOURCE, lambda *a, **k: Response(b"bad", "text/plain"))

    def test_filename_cannot_escape_the_assets_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(ValueError):
                refresh(Path(temporary), [{**SOURCE[0], "file": "../README.md"}])


if __name__ == "__main__":
    unittest.main()
