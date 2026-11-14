"""Refresh public profile cards; a failed provider never replaces a good snapshot."""
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SOURCES = [
    {"file": "trophies.svg", "url": "https://trophy.ryglcloud.net/?username=EricN2907&theme=dracula&no-frame=true&no-bg=true&margin-w=8&column=4", "markers": ["Commits", "Followers"]},
    {"file": "stats.svg", "url": "https://github-readme-stats-fork.vercel.app/api?username=EricN2907&theme=midnight-purple&hide_border=true&include_all_commits=true", "markers": ["Total Commits", "Total PRs"]},
    {"file": "languages.svg", "url": "https://github-readme-stats-fork.vercel.app/api/top-langs/?username=EricN2907&theme=midnight-purple&hide_border=true&layout=compact", "markers": ["Most Used Languages"]},
    {"file": "streak.svg", "url": "https://streak-stats.demolab.com/?user=EricN2907&theme=dracula&hide_border=true", "markers": ["Total Contributions", "Current Streak"]},
    {"file": "activity.svg", "url": "https://github-readme-activity-graph.vercel.app/graph?username=EricN2907&theme=dracula", "markers": ["Contributions"]},
]
MAX_BYTES = 2 * 1024 * 1024


def validate_svg(data, markers):
    if not 100 < len(data) <= MAX_BYTES:
        raise ValueError("SVG size is outside the accepted range")
    text = data.decode("utf-8")
    if re.search(r"<!DOCTYPE|<!ENTITY|@import|url\(\s*['\"]?(?:https?:|//|data:|javascript:)", text, re.I):
        raise ValueError("SVG must not load external content or entities")
    try:
        root = ET.fromstring(text)
    except ET.ParseError as error:
        raise ValueError("Response contains malformed SVG XML") from error
    if root.tag != "{http://www.w3.org/2000/svg}svg":
        raise ValueError("Response is not an SVG image")
    for element in root.iter():
        tag = element.tag.rsplit("}", 1)[-1].lower()
        if tag in {"script", "iframe", "object", "embed"}:
            raise ValueError("Active SVG content is not allowed")
        # The activity graph uses a foreignObject containing one inert XHTML h1.
        if element.tag.startswith("{http://www.w3.org/1999/xhtml}") and tag not in {"h1", "div", "p", "span", "br"}:
            raise ValueError("Only inert XHTML labels are accepted")
        for name, value in element.attrib.items():
            name = name.rsplit("}", 1)[-1].lower()
            if name.startswith("on") or (name == "href" and not value.startswith("#")):
                raise ValueError("SVG must be self-contained and have no event handlers")
    visible_text = " ".join(root.itertext())
    if re.search(r"something went wrong|deployment_(?:disabled|paused|not_found)|rate limit exceeded|could not fetch|error fetching|unable to fetch", visible_text, re.I):
        raise ValueError("Provider returned an error card")
    if not all(marker in visible_text for marker in markers) or not re.search(r"\d", visible_text):
        raise ValueError("Expected profile metrics are missing")
    return re.sub(r"[\t ]+$", "", text, flags=re.M).strip() + "\n"


def atomic_write(path, text):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8", newline="\n")
    temporary.replace(path)


def refresh(root=ROOT, sources=SOURCES, opener=urlopen, timestamp=None):
    assets = Path(root) / "assets"
    assets.mkdir(exist_ok=True)
    status_file = assets / "card-status.json"
    status = json.loads(status_file.read_text(encoding="utf-8")) if status_file.exists() else {}
    timestamp = timestamp or datetime.now(timezone.utc).isoformat(timespec="seconds")
    results = []
    for source in sources:
        if not re.fullmatch(r"[a-z-]+\.svg", source["file"]):
            raise ValueError("Card filename must stay inside assets/")
        destination = assets / source["file"]
        try:
            request = Request(source["url"], headers={"User-Agent": "EricN2907/profile-cards", "Accept": "image/svg+xml"})
            with opener(request, timeout=20) as response:
                if response.headers.get_content_type() != "image/svg+xml":
                    raise ValueError("Provider did not return image/svg+xml")
                text = validate_svg(response.read(MAX_BYTES + 1), source["markers"])
            atomic_write(destination, text)
            status[source["file"]] = {"fetchedAt": timestamp, "source": source["url"]}
            results.append((source["file"], "updated"))
        except Exception as error:
            # Fallback is accepted only when the existing snapshot is still valid.
            if not destination.exists():
                raise RuntimeError(f"No usable snapshot for {source['file']}") from error
            validate_svg(destination.read_bytes(), source["markers"])
            print(f"Warning: keeping {source['file']}: {type(error).__name__}: {error}", file=sys.stderr)
            results.append((source["file"], "kept"))
    if any(result == "updated" for _, result in results):
        atomic_write(status_file, json.dumps(status, ensure_ascii=False, indent=2) + "\n")
    return results


if __name__ == "__main__":
    for filename, result in refresh():
        print(f"{filename}: {result}")
