#!/usr/bin/env python3

from pathlib import Path
import re

ROOT = Path(".")
HOST_RE = r"https?://2010\.stateofthemap\.org"

stats = {
    "files_changed": 0,
    "attribute_urls": 0,
    "rss_links": 0,
    "sitemap_lines_removed": 0,
}


# href/src/etc beginning with the old absolute hostname.
ATTR_RE = re.compile(
    rf'''(?P<prefix>\b(?:href|src|poster|action|xml:base)=
        (?P<quote>["']))
        {HOST_RE}
        (?P<path>/[^"'<>]*)
        (?P=quote)
    ''',
    re.IGNORECASE | re.VERBOSE,
)


# RSS-style:
#
#   <link>/foo/</link>
#
# Atom <link href="..."> is handled by ATTR_RE.
RSS_LINK_RE = re.compile(
    rf"(<link>\s*){HOST_RE}(/[^<]*)(\s*</link>)",
    re.IGNORECASE,
)


def replace_attr(match):
    stats["attribute_urls"] += 1

    path = match.group("path")

    # Broken WPML-generated favicon URLs:
    # /es//wp-content/... -> /wp-content/...
    if path.startswith("/es//wp-content/"):
        path = path[len("/es/"):]

    return (
        match.group("prefix")
        + path
        + match.group("quote")
    )


def replace_rss_link(match):
    stats["rss_links"] += 1

    return (
        match.group(1)
        + match.group(2)
        + match.group(3)
    )


for path in ROOT.rglob("*"):
    if not path.is_file():
        continue

    if ".git" in path.parts:
        continue

    try:
        text = path.read_text(
            encoding="utf-8",
            errors="strict",
        )
    except (UnicodeDecodeError, OSError):
        continue

    original = text

    #
    # Convert normal href/src/xml:base/etc.
    #
    text = ATTR_RE.sub(
        replace_attr,
        text,
    )

    #
    # Convert RSS <link>...</link>.
    #
    text = RSS_LINK_RE.sub(
        replace_rss_link,
        text,
    )

    #
    # The WordPress sitemap no longer exists in the static site.
    #
    if path.name == "robots.txt":
        lines = []

        for line in text.splitlines(keepends=True):
            if re.match(
                rf"\s*Sitemap:\s*{HOST_RE}/wp-sitemap\.xml\s*$",
                line,
                re.IGNORECASE,
            ):
                print(
                    "REMOVE obsolete sitemap: robots.txt"
                )
                stats["sitemap_lines_removed"] += 1
                continue

            lines.append(line)

        text = "".join(lines)

    if text != original:
        path.write_text(
            text,
            encoding="utf-8",
        )

        stats["files_changed"] += 1
        print(f"UPDATED: {path}")


print("\nSummary:")

for name, value in stats.items():
    print(f"  {name:28} {value}")
