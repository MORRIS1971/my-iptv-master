#!/usr/bin/env python3
# MY IPTV MASTER PLAYLIST BUILDER v2
# Consolidates public playlists into six categories for OTT Navigator.
# Uses public/authorized sources only. Does not bypass DRM, logins or geo-blocks.

from urllib.request import Request, urlopen
from pathlib import Path
import re
from collections import Counter

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

GROUPS = [
    "01 TV MALAYSIA",
    "02 LEARNING CHANNELS",
    "03 DISCOVERY CHANNELS",
    "04 LIVE CHANNELS",
    "05 SPORTS",
    "06 MOVIES",
]

def fetch(url):
    req = Request(url, headers={"User-Agent": "MY-IPTV-MASTER/2.0"})
    with urlopen(req, timeout=35) as response:
        return response.read().decode("utf-8", "replace")

def parse_m3u(text):
    lines = [line.strip() for line in text.replace("\r", "").split("\n")]
    records, pending = [], None
    for line in lines:
        if not line:
            continue
        if line.startswith("#EXTINF:"):
            pending = line
        elif line.startswith("#"):
            if pending and line.startswith("#EXTVLCOPT"):
                pending += "\n" + line
        elif pending and line.startswith(("http://", "https://")):
            records.append((pending, line))
            pending = None
    return records

def get_attr(line, key):
    match = re.search(r'\b' + re.escape(key) + r'="([^"]*)"', line, re.I)
    return match.group(1).strip() if match else ""

def get_title(extinf):
    return extinf.split(",", 1)[1].strip() if "," in extinf else "Unknown channel"

def normalize(value):
    value = (value or "").lower()
    value = re.sub(r'\[[^]]*\]|\([^)]*\)', ' ', value)
    value = re.sub(r'\b(hd|fhd|uhd|4k|sd|live|backup|alt)\b', ' ', value)
    value = re.sub(r'[^a-z0-9]+', ' ', value)
    return re.sub(r'\s+', ' ', value).strip()

def dedupe_key(extinf):
    # Prefer stable broadcaster EPG ID. Otherwise use normalized channel title.
    tvg_id = get_attr(extinf, "tvg-id").lower()
    if tvg_id:
        return ("id", tvg_id)
    return ("title", normalize(get_title(extinf)))

def set_group(extinf, group):
    if re.search(r'\bgroup-title="[^"]*"', extinf):
        return re.sub(r'\bgroup-title="[^"]*"', f'group-title="{group}"', extinf, count=1)
    head, sep, title = extinf.partition(",")
    return f'{head} group-title="{group}"{sep}{title}'

def main():
    downloaded, failures = {}, []
    for source_name, source_url in SOURCES.items():
        try:
            print(f"Downloading {source_name}...")
            downloaded[source_name] = parse_m3u(fetch(source_url))
        except Exception as error:
            downloaded[source_name] = []
            failures.append(f"{source_name}: {type(error).__name__}: {error}")

    output = []
    seen = set()
    counts = Counter()
    source_counts = Counter()
    duplicates = 0

    def add_records(records, group, source_name):
        nonlocal duplicates
        added = 0
        for extinf, stream_url in records:
            if not stream_url.startswith(("http://", "https://")):
                continue
            if any(bad in stream_url.lower() for bad in ("example.com", "localhost", "127.0.0.1")):
                continue
            key = dedupe_key(extinf)
            if not key[1]:
                key = ("url", stream_url.lower())
            if key in seen:
                duplicates += 1
                continue
            seen.add(key)
            output.append((set_group(extinf, group), stream_url))
            counts[group] += 1
            source_counts[source_name] += 1
            added += 1
        return added

    # Primary categorized sources. The order establishes category priority.
    add_records(downloaded["malaysia"], GROUPS[0], "IPTV-ORG Malaysia")
    add_records(downloaded["education"], GROUPS[1], "IPTV-ORG Education")
    add_records(downloaded["documentary"], GROUPS[2], "IPTV-ORG Documentary")
    add_records(downloaded["science"], GROUPS[2], "IPTV-ORG Science")
    add_records(downloaded["news"], GROUPS[3], "IPTV-ORG News")
    add_records(downloaded["sports"], GROUPS[4], "IPTV-ORG Sports")
    add_records(downloaded["movies"], GROUPS[5], "IPTV-ORG Movies")

    # Supplementary Free-TV entries. Avoid using the broad word "live" as a
    # category trigger; classify by meaningful title/group keywords instead.
    rules = [
        (GROUPS[3], re.compile(r'\b(news|world news|international news|24h news|24 hour news)\b', re.I), "Free-TV News"),
        (GROUPS[4], re.compile(r'\b(sport|sports|football|soccer|tennis|badminton|basketball|cricket|motorsport)\b', re.I), "Free-TV Sports"),
        (GROUPS[5], re.compile(r'\b(movie|movies|cinema|film)\b', re.I), "Free-TV Movies"),
        (GROUPS[1], re.compile(r'\b(education|educational|learning|knowledge|school)\b', re.I), "Free-TV Learning"),
        (GROUPS[2], re.compile(r'\b(documentary|nature|wildlife|discovery|history|animal|science)\b', re.I), "Free-TV Discovery"),
    ]
    for group, pattern, source_label in rules:
        selected = [
            (extinf, url)
            for extinf, url in downloaded["free_tv"]
            if pattern.search(get_title(extinf) + " " + get_attr(extinf, "group-title"))
        ]
        add_records(selected, group, source_label)

    with OUTFILE.open("w", encoding="utf-8", newline="\n") as file:
        file.write("#EXTM3U\n")
        for extinf, stream_url in output:
            file.write(extinf + "\n" + stream_url + "\n")

    report = [
        "MY IPTV MASTER — BUILD REPORT v2",
        "",
        "RINGKASAN KATEGORI (selepas deduplikasi berdasarkan tvg-id atau nama saluran):",
    ]
    for group in GROUPS:
        report.append(f"{group}: {counts[group]} saluran")
    report.extend([
        "",
        f"Jumlah saluran selepas deduplikasi: {len(output)}",
        f"Entri pendua yang ditolak: {duplicates}",
        "",
        "SUMBER DAN JUMLAH TAMBAHAN:",
    ])
    for label, number in source_counts.items():
        report.append(f"{label}: {number}")
    report.extend([
        "",
        "URL SUMBER:",
        *[f"- {name}: {url}" for name, url in SOURCES.items()],
        "",
        "NOTA:",
        "- Deduplikasi v2 mengutamakan tvg-id; jika tiada, nama saluran dinormalisasi.",
        "- Nama sama mungkin merujuk kepada saluran berlainan di sesetengah negara; semak secara manual jika perlu.",
        "- Builder menggabungkan playlist awam dan tidak menjamin semua stream boleh dimainkan dari Malaysia.",
        "- Tiada ujian kebolehcapaian stream, DRM, login atau sekatan geografi dilakukan.",
        "- Saluran sukan tidak menjamin akses kepada EPL atau badminton premium secara langsung.",
        "- Logo dan tvg-id dikekalkan jika disediakan oleh sumber.",
        "- EPG belum digabungkan; perlu sumber XMLTV dan pemadanan tvg-id yang sesuai.",
    ])
    if failures:
        report.extend(["", "SUMBER GAGAL DIMUAT TURUN:"] + failures)

    REPORT.write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report))
    print(f"\nGenerated: {OUTFILE}")

if __name__ == "__main__":
    main()
