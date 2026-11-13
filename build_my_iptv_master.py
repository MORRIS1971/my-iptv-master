#!/usr/bin/env python3
# MY IPTV MASTER PLAYLIST BUILDER v3.1 — HYBRID MALAYSIA
# M3U contains only public/authorized stream URLs.
# Official broadcaster platforms are documented separately, never faked as M3U streams.

from urllib.request import Request, urlopen
from pathlib import Path
from collections import Counter
import re

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
        "website": "https://rtmklik.rtm.gov.my/",
        "android": "https://play.google.com/store/apps/details?id=my.gov.rtm.mobile",
        "android_tv": "https://play.google.com/store/apps/details?id=my.gov.rtm.tv",
        "note": "Gunakan aplikasi atau laman web rasmi. Builder ini tidak mempunyai URL M3U terbuka RTM yang disahkan."
    },
    {
        "name": "Tonton",
        "channels": "TV3, TV9, 8TV, DidikTV dan kandungan Media Prima",
        "website": "https://www.tonton.com.my/",
        "live": "https://browse.tonton.com.my/live",
        "note": "Sesetengah siaran mungkin memerlukan aplikasi, akaun atau langganan Tonton."
    },
    {
        "name": "Awesome TV",
        "channels": "Awesome TV",
        "website": "https://awesometv.my/",
        "live": "https://awesometv.my/livetv/details/awesome-tv/28",
        "note": "Gunakan halaman Live rasmi. Pautan laman web bukan URL M3U."
    },
]

GROUPS = [
    "01 TV MALAYSIA",
    "02 LEARNING CHANNELS",
    "03 DISCOVERY CHANNELS",
    "04 LIVE CHANNELS",
    "05 SPORTS",
    "06 MOVIES",
]

BASE = Path(__file__).resolve().parent
OUTFILE = BASE / "MY-IPTV-MASTER.m3u"
REPORT = BASE / "BUILD-REPORT.txt"
HYBRID_GUIDE = BASE / "MALAYSIA-OFFICIAL-STREAMING.md"

def fetch(url):
    request = Request(url, headers={"User-Agent": "MY-IPTV-MASTER/3.1"})
    with urlopen(request, timeout=40) as response:
        return response.read().decode("utf-8", "replace")

def parse_m3u(text):
    records = []
    pending = None
    for raw in text.replace("\r", "").split("\n"):
        line = raw.strip()
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

def get_attr(extinf, key):
    match = re.search(r'\b' + re.escape(key) + r'="([^"]*)"', extinf, re.I)
    return match.group(1).strip() if match else ""

def get_title(extinf):
    return extinf.split(",", 1)[1].strip() if "," in extinf else "Unknown channel"

def normalize(value):
    value = (value or "").lower()
    value = re.sub(r'\[[^]]*\]|\([^)]*\)', " ", value)
    value = re.sub(r'\b(hd|fhd|uhd|4k|sd|live|backup|alt)\b', " ", value)
    value = re.sub(r'[^a-z0-9]+', " ", value)
    return re.sub(r'\s+', " ", value).strip()

def dedupe_key(extinf, stream_url):
    tvg_id = get_attr(extinf, "tvg-id").lower()
    if tvg_id:
        return ("id", tvg_id)
    title = normalize(get_title(extinf))
    return ("title", title) if title else ("url", stream_url.lower())

def set_group(extinf, group):
    if re.search(r'\bgroup-title="[^"]*"', extinf):
        return re.sub(r'\bgroup-title="[^"]*"', f'group-title="{group}"', extinf, count=1)
    head, separator, title = extinf.partition(",")
    return f'{head} group-title="{group}"{separator}{title}'

def build_hybrid_guide():
    lines = [
        "# MY IPTV MASTER V3 — Platform Penstriman Rasmi Malaysia",
        "",
        "Playlist M3U utama mengandungi stream awam/yang dibenarkan sahaja.",
        "Pautan dalam panduan ini membuka laman atau aplikasi rasmi; ia BUKAN stream M3U dan tidak akan muncul sebagai saluran boleh main dalam OTT Navigator.",
        "",
        "## Platform rasmi Malaysia",
        "",
    ]
    for item in OFFICIAL_MALAYSIA:
        lines.extend([
            f"### {item['name']}",
            f"- Saluran/kandungan: {item['channels']}",
            f"- Laman rasmi: {item['website']}",
        ])
        if item.get("live"):
            lines.append(f"- Halaman Live: {item['live']}")
        if item.get("android"):
            lines.append(f"- Aplikasi Android: {item['android']}")
        if item.get("android_tv"):
            lines.append(f"- Aplikasi Android TV: {item['android_tv']}")
        lines.extend([f"- Nota: {item['note']}", ""])
    lines.extend([
        "## Cara menggunakan sistem Hybrid",
        "1. Tambah MY-IPTV-MASTER.m3u sebagai playlist utama dalam OTT Navigator.",
        "2. Untuk saluran yang tiada stream M3U sah, buka laman/aplikasi rasmi melalui pautan dalam dokumen ini.",
        "3. Pada telefon atau Android TV, pasang aplikasi rasmi yang berkaitan.",
        "4. Pada laptop, gunakan laman web rasmi melalui browser jika penyiar menyokong tontonan web.",
        "",
        "## Batasan",
        "- OTT Navigator membaca stream M3U; ia tidak boleh menukar pautan laman web atau pautan aplikasi menjadi stream.",
        "- Ketersediaan kandungan, akaun, langganan dan sekatan lokasi ditentukan oleh penyiar.",
        "- Jangan ekstrak atau mengedar URL dalaman aplikasi yang tidak diterbitkan sebagai stream awam.",
        "- Tiada akses kepada kandungan premium/DRM yang dipintas.",
    ])
    HYBRID_GUIDE.write_text("\n".join(lines) + "\n", encoding="utf-8")

def main():
    downloaded = {}
    failures = []
    for name, url in SOURCES.items():
        try:
            print(f"Downloading {name}...")
            downloaded[name] = parse_m3u(fetch(url))
        except Exception as error:
            downloaded[name] = []
            failures.append(f"{name}: {type(error).__name__}: {error}")

    output = []
    seen = set()
    counts = Counter()
    source_counts = Counter()
    duplicates = 0
    malaysia_titles = []

    def add_records(records, group, source_label):
        nonlocal duplicates
        added = 0
        for extinf, stream_url in records:
            if not stream_url.startswith(("http://", "https://")):
                continue
            if any(token in stream_url.lower() for token in ("example.com", "localhost", "127.0.0.1")):
                continue
            key = dedupe_key(extinf, stream_url)
            if key in seen:
                duplicates += 1
                continue
            seen.add(key)
            output.append((set_group(extinf, group), stream_url))
            counts[group] += 1
            source_counts[source_label] += 1
            added += 1
            if group == GROUPS[0]:
                malaysia_titles.append((get_title(extinf), get_attr(extinf, "tvg-id")))
        return added

    add_records(downloaded["malaysia"], GROUPS[0], "IPTV-ORG Malaysia")
    add_records(downloaded["education"], GROUPS[1], "IPTV-ORG Education")
    add_records(downloaded["documentary"], GROUPS[2], "IPTV-ORG Documentary")
    add_records(downloaded["science"], GROUPS[2], "IPTV-ORG Science")
    add_records(downloaded["news"], GROUPS[3], "IPTV-ORG News")
    add_records(downloaded["sports"], GROUPS[4], "IPTV-ORG Sports")
    add_records(downloaded["movies"], GROUPS[5], "IPTV-ORG Movies")

    free_tv_rules = [
        (GROUPS[3], re.compile(r'\b(news|world news|international news|24h news|24 hour news)\b', re.I), "Free-TV News"),
        (GROUPS[4], re.compile(r'\b(sport|sports|football|soccer|tennis|badminton|basketball|cricket|motorsport)\b', re.I), "Free-TV Sports"),
        (GROUPS[5], re.compile(r'\b(movie|movies|cinema|film)\b', re.I), "Free-TV Movies"),
        (GROUPS[1], re.compile(r'\b(education|educational|learning|knowledge|school)\b', re.I), "Free-TV Learning"),
        (GROUPS[2], re.compile(r'\b(documentary|nature|wildlife|discovery|history|animal|science)\b', re.I), "Free-TV Discovery"),
    ]
    for group, pattern, source_label in free_tv_rules:
        matches = [
            (extinf, stream_url)
            for extinf, stream_url in downloaded["free_tv"]
            if pattern.search(get_title(extinf) + " " + get_attr(extinf, "group-title"))
        ]
        add_records(matches, group, source_label)

    with OUTFILE.open("w", encoding="utf-8", newline="\n") as playlist:
        playlist.write("#EXTM3U\n")
        for extinf, stream_url in output:
            playlist.write(extinf + "\n" + stream_url + "\n")

    build_hybrid_guide()

    report = [
        "MY IPTV MASTER — BUILD REPORT v3.1 HYBRID",
        "",
        "RINGKASAN KATEGORI M3U:",
    ]
    for group in GROUPS:
        report.append(f"{group}: {counts[group]} saluran")
    report.extend([
        "",
        f"Jumlah saluran M3U: {len(output)}",
        f"Entri pendua ditolak: {duplicates}",
        "",
        "SENARAI TV MALAYSIA DALAM M3U:",
    ])
    report.extend([f"- {name} | tvg-id={tvg_id or 'tiada'}" for name, tvg_id in malaysia_titles] or ["- Tiada entri Malaysia dalam sumber M3U."])
    report.extend(["", "SUMBER DAN JUMLAH:"])
    report.extend([f"{label}: {number}" for label, number in source_counts.items()])
    report.extend([
        "",
        "PLATFORM RASMI MALAYSIA (PAUTAN WEB/APLIKASI, BUKAN M3U):",
    ])
    report.extend([f"- {item['name']}: {item['website']}" for item in OFFICIAL_MALAYSIA])
    report.extend([
        "",
        "SUMBER M3U:",
    ])
    report.extend([f"- {name}: {url}" for name, url in SOURCES.items()])
    report.extend([
        "",
        "NOTA:",
        "- V3.1 ialah sistem Hybrid: satu playlist M3U ditambah panduan platform rasmi Malaysia.",
        "- Pautan RTMKlik, Tonton dan Awesome TV bukan stream M3U dan tidak dipaparkan sebagai saluran boleh main dalam OTT Navigator.",
        "- Stream M3U bersumberkan playlist awam; kebolehcapaian dari Malaysia belum dijamin.",
        "- Tiada ujian playback, DRM, login atau geo-block dibuat.",
        "- Saluran sukan tidak menjamin akses EPL atau badminton premium.",
        "- Metadata tvg-id/tvg-logo dikekalkan jika tersedia.",
        "- EPG XMLTV belum disepadukan.",
    ])
    if failures:
        report.extend(["", "SUMBER GAGAL DIMUAT TURUN:"] + failures)

    REPORT.write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report))
    print(f"Generated: {OUTFILE}")
    print(f"Generated: {HYBRID_GUIDE}")

if __name__ == "__main__":
    main()
