#!/usr/bin/env python3
# MY IPTV MASTER PLAYLIST BUILDER v3 — HYBRID MALAYSIA
# M3U streams remain limited to public/authorized sources.
# Official broadcaster apps/websites are listed separately; they are not converted
# into stream URLs and are not falsely represented as playable M3U entries.

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

OFFICIAL_MALAYSIA = [
    {
        "name": "RTMKlik",
        "channels": "TV1, TV2, TV Okey, Berita RTM, Sukan TV, TV6 dan Parlimen RTM",
        "url": "https://rtmklik.rtm.gov.my/",
        "app": "https://play.google.com/store/apps/details?id=my.gov.rtm.mobile",
        "note": "Platform rasmi RTM. Gunakan aplikasi atau laman web RTMKlik; tiada URL M3U rasmi terbuka disahkan dalam builder ini."
    },
    {
        "name": "Tonton",
        "channels": "TV3, TV9, 8TV, DidikTV dan kandungan Media Prima",
        "url": "https://www.tonton.com.my/",
        "live": "https://browse.tonton.com.my/live",
        "note": "Platform rasmi Media Prima. Sesetengah tontonan langsung mungkin memerlukan aplikasi Tonton atau akaun."
    },
    {
        "name": "Awesome TV",
        "channels": "Awesome TV Live",
        "url": "https://awesometv.my/",
        "live": "https://awesometv.my/livetv",
        "note": "Laman rasmi menyediakan halaman Live TV. Pautan ini dibuka sebagai laman web, bukan stream M3U."
    },
]

OUTFILE = Path(__file__).with_name("MY-IPTV-MASTER.m3u")
REPORT = Path(__file__).with_name("BUILD-REPORT.txt")
HYBRID_GUIDE = Path(__file__).with_name("MALAYSIA-OFFICIAL-STREAMING.md")

GROUPS = [
    "01 TV MALAYSIA",
    "02 LEARNING CHANNELS",
    "03 DISCOVERY CHANNELS",
    "04 LIVE CHANNELS",
    "05 SPORTS",
    "06 MOVIES",
]

def fetch(url):
    req = Request(url, headers={"User-Agent": "MY-IPTV-MASTER/3.0"})
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
    match = re.search(r'\\b' + re.escape(key) + r'="([^"]*)"', line, re.I)
    return match.group(1).strip() if match else ""

def get_title(extinf):
    return extinf.split(",", 1)[1].strip() if "," in extinf else "Unknown channel"

def normalize(value):
    value = (value or "").lower()
    value = re.sub(r'\\[[^]]*\\]|\\([^)]*\\)', ' ', value)
    value = re.sub(r'\\b(hd|fhd|uhd|4k|sd|live|backup|alt)\\b', ' ', value)
    value = re.sub(r'[^a-z0-9]+', ' ', value)
    return re.sub(r'\\s+', ' ', value).strip()

def dedupe_key(extinf):
    tvg_id = get_attr(extinf, "tvg-id").lower()
    if tvg_id:
        return ("id", tvg_id)
    return ("title", normalize(get_title(extinf)))

def set_group(extinf, group):
    if re.search(r'\\bgroup-title="[^"]*"', extinf):
        return re.sub(r'\\bgroup-title="[^"]*"', f'group-title="{group}"', extinf, count=1)
    head, sep, title = extinf.partition(",")
    return f'{head} group-title="{group}"{sep}{title}'

def build_hybrid_guide():
    lines = [
        "# MY IPTV MASTER V3 — Pautan Penstriman Rasmi Malaysia",
        "",
        "Dokumen ini melengkapkan playlist M3U dengan pautan ke platform rasmi penyiar Malaysia.",
        "Pautan di bawah ialah laman web/aplikasi rasmi, BUKAN URL M3U. Ia tidak akan muncul sebagai saluran boleh main dalam OTT Navigator.",
        "",
        "## Platform rasmi",
        "",
    ]
    for item in OFFICIAL_MALAYSIA:
        lines.extend([
            f"### {item['name']}",
            f"- Saluran/kandungan: {item['channels']}",
            f"- Laman rasmi: {item['url']}",
        ])
        if item.get("live"):
            lines.append(f"- Halaman Live: {item['live']}")
        if item.get("app"):
            lines.append(f"- Aplikasi Android: {item['app']}")
        lines.extend([f"- Nota: {item['note']}", ""])
    lines.extend([
        "## Cara penggunaan",
        "1. Gunakan MY-IPTV-MASTER.m3u sebagai playlist utama dalam OTT Navigator.",
        "2. Untuk saluran yang tidak tersedia sebagai M3U, buka platform rasmi di atas menggunakan aplikasi atau browser yang disokong.",
        "3. Jangan salin atau ekstrak URL dalaman aplikasi/laman web jika penyiar tidak menyediakan pautan M3U secara rasmi.",
        "",
        "## Batasan",
        "- Ketersediaan kandungan, akaun dan sekatan lokasi ditentukan oleh setiap penyiar.",
        "- Pautan rasmi boleh berubah; semak laman penyiar jika pautan tidak lagi berfungsi.",
        "- Dokumen ini tidak menyediakan akses kepada saluran berbayar atau kandungan yang memerlukan langganan.",
    ])
    HYBRID_GUIDE.write_text("\n".join(lines) + "\n", encoding="utf-8")

def main():
    downloaded, failures = {}, []
    for source_name, source_url in SOURCES.items():
        try:
            print(f"Downloading {source_name}...")
            downloaded[source_name] = parse_m3u(fetch(source_url))
        except Exception as error:
            downloaded[source_name] = []
            failures.append(f"{source_name}: {type(error).__name__}: {error}")

    output, seen = [], set()
    counts, source_counts = Counter(), Counter()
    duplicates = 0
    malaysia_entries = []

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
            if group == GROUPS[0]:
                malaysia_entries.append((get_title(extinf), get_attr(extinf, "tvg-id"), stream_url))
        return added

    # Six M3U categories: retain public playlist feeds and metadata.
    add_records(downloaded["malaysia"], GROUPS[0], "IPTV-ORG Malaysia")
    add_records(downloaded["education"], GROUPS[1], "IPTV-ORG Education")
    add_records(downloaded["documentary"], GROUPS[2], "IPTV-ORG Documentary")
    add_records(downloaded["science"], GROUPS[2], "IPTV-ORG Science")
    add_records(downloaded["news"], GROUPS[3], "IPTV-ORG News")
    add_records(downloaded["sports"], GROUPS[4], "IPTV-ORG Sports")
    add_records(downloaded["movies"], GROUPS[5], "IPTV-ORG Movies")

    # Free-TV supplements use specific topical terms; no broad "live" match.
    rules = [
        (GROUPS[3], re.compile(r'\\b(news|world news|international news|24h news|24 hour news)\\b', re.I), "Free-TV News"),
        (GROUPS[4], re.compile(r'\\b(sport|sports|football|soccer|tennis|badminton|basketball|cricket|motorsport)\\b', re.I), "Free-TV Sports"),
        (GROUPS[5], re.compile(r'\\b(movie|movies|cinema|film)\\b', re.I), "Free-TV Movies"),
        (GROUPS[1], re.compile(r'\\b(education|educational|learning|knowledge|school)\\b', re.I), "Free-TV Learning"),
        (GROUPS[2], re.compile(r'\\b(documentary|nature|wildlife|discovery|history|animal|science)\\b', re.I), "Free-TV Discovery"),
    ]
    for group, pattern, source_label in rules:
        selected = [
            (extinf, stream_url)
            for extinf, stream_url in downloaded["free_tv"]
            if pattern.search(get_title(extinf) + " " + get_attr(extinf, "group-title"))
        ]
        add_records(selected, group, source_label)

    with OUTFILE.open("w", encoding="utf-8", newline="\n") as file:
        file.write("#EXTM3U\n")
        for extinf, stream_url in output:
            file.write(extinf + "\n" + stream_url + "\n")

    build_hybrid_guide()

    report = [
        "MY IPTV MASTER — BUILD REPORT v3 HYBRID",
        "",
        "RINGKASAN KATEGORI M3U (selepas deduplikasi):",
    ]
    for group in GROUPS:
        report.append(f"{group}: {counts[group]} saluran")
    report.extend([
        "",
        f"Jumlah saluran M3U: {len(output)}",
        f"Entri pendua ditolak: {duplicates}",
        "",
        "TV MALAYSIA — SENARAI UNTUK AUDIT:",
    ])
    if malaysia_entries:
        for title, tvg_id, _ in malaysia_entries:
            report.append(f"- {title} | tvg-id={tvg_id or 'tiada'}")
    else:
        report.append("- Tiada entri Malaysia berjaya dimuat turun.")
    report.extend([
        "",
        "SUMBER M3U DAN JUMLAH:",
    ])
    for label, number in source_counts.items():
        report.append(f"{label}: {number}")
    report.extend([
        "",
        "PLATFORM RASMI MALAYSIA (pautan aplikasi/web, bukan stream M3U):",
        *[f"- {item['name']}: {item['url']}" for item in OFFICIAL_MALAYSIA],
        "",
        "URL SUMBER M3U:",
        *[f"- {name}: {url}" for name, url in SOURCES.items()],
        "",
        "NOTA:",
        "- V3 Hybrid mengekalkan satu playlist M3U dan menghasilkan panduan pautan rasmi Malaysia secara berasingan.",
        "- Pautan RTMKlik, Tonton dan Awesome TV ialah laman/aplikasi rasmi; tidak disamarkan sebagai saluran M3U.",
        "- M3U menggabungkan sumber awam; tidak menjamin semua stream boleh dimainkan dari Malaysia.",
        "- Tiada ujian playback, DRM, login atau sekatan geografi dilakukan.",
        "- Saluran sukan tidak menjamin akses kepada EPL atau badminton premium.",
        "- tvg-id dan tvg-logo dikekalkan jika tersedia daripada sumber.",
        "- EPG belum digabungkan; perlu sumber XMLTV yang sah dan padanan tvg-id.",
        "- TV Malaysia masih bergantung pada feed M3U awam IPTV-ORG; panduan rasmi melengkapkan saluran yang tiada dalam M3U.",
    ])
    if failures:
        report.extend(["", "SUMBER GAGAL DIMUAT TURUN:"] + failures)

    REPORT.write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report))
    print(f"Generated: {OUTFILE}")
    print(f"Generated: {HYBRID_GUIDE}")

if __name__ == "__main__":
    main()
