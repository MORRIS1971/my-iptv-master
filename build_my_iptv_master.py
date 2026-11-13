#!/usr/bin/env python3
# MY IPTV MASTER PLAYLIST BUILDER
# Fetches public playlists and creates one categorized M3U for OTT Navigator.
# Sources: IPTV-ORG public playlists + Free-TV public playlist.
# It does NOT bypass DRM, login, subscriptions, or geo-restrictions.

from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from urllib.parse import urlparse
from pathlib import Path
import re, sys, time

SOURCES = {
    "malaysia": "https://iptv-org.github.io/iptv/countries/my.m3u",
    "education": "https://iptv-org.github.io/iptv/categories/education.m3u",
    "documentary": "https://iptv-org.github.io/iptv/categories/documentary.m3u",
    "science": "https://iptv-org.github.io/iptv/categories/science.m3u",
    "movies": "https://iptv-org.github.io/iptv/categories/movies.m3u",
    "sports": "https://iptv-org.github.io/iptv/categories/sports.m3u",
    "news": "https://iptv-org.github.io/iptv/categories/news.m3u",
    "free_tv": "https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8",
}

OUTFILE = Path(__file__).with_name("MY-IPTV-MASTER.m3u")
REPORT = Path(__file__).with_name("BUILD-REPORT.txt")

def fetch(url):
    req = Request(url, headers={"User-Agent": "MY-IPTV-MASTER/1.0"})
    with urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")

def parse_m3u(text):
    lines = [x.strip() for x in text.replace("\r", "").split("\n")]
    items, pending = [], None
    for line in lines:
        if not line:
            continue
        if line.startswith("#EXTINF:"):
            pending = line
        elif line.startswith("#"):
            if pending and line.startswith("#EXTVLCOPT"):
                pending += "\n" + line
        elif pending and line.startswith(("http://", "https://")):
            items.append((pending, line))
            pending = None
    return items

def attr(line, key):
    m = re.search(r'\b' + re.escape(key) + r'="([^"]*)"', line, re.I)
    return m.group(1).strip() if m else ""

def clean_title(line):
    return line.split(",", 1)[1].strip() if "," in line else "Unknown channel"

def replace_group(extinf, group):
    if re.search(r'\bgroup-title="[^"]*"', extinf):
        return re.sub(r'\bgroup-title="[^"]*"', f'group-title="{group}"', extinf, count=1)
    head, sep, title = extinf.partition(",")
    return f'{head} group-title="{group}"{sep}{title}'

def dedupe_key(extinf, url):
    return (attr(extinf, "tvg-id").lower(), clean_title(extinf).lower(), url.lower())

def add_group(target, records, group, seen, report):
    count = 0
    for extinf, url in records:
        if not url.startswith(("http://", "https://")):
            continue
        if any(x in url.lower() for x in ("example.com", "localhost", "127.0.0.1")):
            continue
        key = dedupe_key(extinf, url)
        if key in seen:
            continue
        seen.add(key)
        target.append((replace_group(extinf, group), url))
        count += 1
    report.append(f"{group}: {count} saluran unik")
    return count

def main():
    downloaded, failed = {}, []
    for name, url in SOURCES.items():
        try:
            print(f"Memuat turun {name} ...")
            downloaded[name] = parse_m3u(fetch(url))
        except Exception as e:
            failed.append(f"{name}: {type(e).__name__}: {e}")
            downloaded[name] = []

    output, seen, report = [], set(), []
    # Malaysia: playlist negara Malaysia sahaja.
    add_group(output, downloaded["malaysia"], "01 TV MALAYSIA", seen, report)
    # Education channels.
    add_group(output, downloaded["education"], "02 LEARNING CHANNELS", seen, report)
    # Documentary + science merged as Discovery.
    add_group(output, downloaded["documentary"], "03 DISCOVERY CHANNELS", seen, report)
    add_group(output, downloaded["science"], "03 DISCOVERY CHANNELS", seen, report)

    # News sources are a conservative basis for live/current-affairs channels.
    add_group(output, downloaded["news"], "04 LIVE CHANNELS", seen, report)

    # Sports category includes available sports channels, not guaranteed live EPL/BWF events.
    add_group(output, downloaded["sports"], "05 SPORTS", seen, report)

    # Movie category.
    add_group(output, downloaded["movies"], "06 MOVIES", seen, report)

    # Free-TV supplements relevant live/news and sports/movies/education channels
    # only when title or category metadata indicates a relevant type.
    supplemental = downloaded["free_tv"]
    rules = [
        ("04 LIVE CHANNELS", re.compile(r"\b(news|live|world|24h|24/7)\b", re.I)),
        ("05 SPORTS", re.compile(r"\b(sport|sports|football|soccer|tennis|badminton|racing)\b", re.I)),
        ("06 MOVIES", re.compile(r"\b(movie|movies|cinema|film)\b", re.I)),
        ("02 LEARNING CHANNELS", re.compile(r"\b(education|learning|science|knowledge)\b", re.I)),
        ("03 DISCOVERY CHANNELS", re.compile(r"\b(documentary|nature|wildlife|discovery|history|animal|planet)\b", re.I)),
    ]
    for group, pattern in rules:
        chosen = [(e,u) for e,u in supplemental if pattern.search(clean_title(e) + " " + attr(e, "group-title"))]
        add_group(output, chosen, group, seen, report)

    header = '#EXTM3U\n'
    body = "\n".join(f"{e}\n{u}" for e,u in output)
    OUTFILE.write_text(header + body + ("\n" if body else ""), encoding="utf-8", newline="\n")

    report.extend([
        "",
        f"Jumlah keseluruhan: {len(output)} saluran unik",
        "Sumber:",
        *[f"- {k}: {v}" for k,v in SOURCES.items()],
        "",
        "PENTING:",
        "- Builder ini menggabungkan senarai awam; ia tidak menjamin setiap stream boleh dimainkan dari Malaysia.",
        "- Tiada ujian HTTP/geo-block dibuat secara automatik kerana sesetengah server menolak HEAD/automated checks.",
        "- Saluran sukan tidak menjamin akses kepada siaran EPL atau badminton premium secara langsung.",
        "- Playlist tidak membuka DRM, akaun berbayar atau sekatan geografi.",
        "- EPG tidak ditambah secara automatik; tvg-id/logo asal dikekalkan jika disediakan oleh sumber."
    ])
    if failed:
        report.extend(["", "Sumber gagal dimuat turun:"] + failed)
    REPORT.write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report))
    print(f"\nFail dijana: {OUTFILE}")

if __name__ == "__main__":
    main()
