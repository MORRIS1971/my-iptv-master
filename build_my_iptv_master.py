#!/usr/bin/env python3
# MY IPTV MASTER PLAYLIST BUILDER v3.2 — HYBRID MALAYSIA
# Public/authorized M3U sources only. Official platform links remain separate.

from urllib.request import Request, urlopen
from urllib.parse import urlsplit
from pathlib import Path
from collections import Counter
import re

VERSION = "3.2"
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
        "note": "Gunakan aplikasi atau laman web rasmi. URL M3U terbuka RTM belum disahkan oleh builder."
    },
    {
        "name": "Tonton",
        "channels": "TV3, TV9, 8TV, DidikTV dan kandungan Media Prima",
        "website": "https://www.tonton.com.my/",
        "live": "https://browse.tonton.com.my/live",
        "note": "Sesetengah siaran mungkin memerlukan aplikasi, akaun atau langganan."
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
    "04 NEWS",
    "05 LIVE & GENERAL",
    "06 SPORTS",
    "07 MOVIES",
]

BASE = Path(__file__).resolve().parent
OUTFILE = BASE / "MY-IPTV-MASTER.m3u"
REPORT = BASE / "BUILD-REPORT.txt"
HYBRID_GUIDE = BASE / "MALAYSIA-OFFICIAL-STREAMING.md"

def fetch(url):
    request = Request(url, headers={"User-Agent": f"MY-IPTV-MASTER/{VERSION}"})
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

def is_malaysian_channel(extinf):
    """Conservative country check; do not infer country from stream URL or language."""
    country = get_attr(extinf, "tvg-country").lower()
    tvg_id = get_attr(extinf, "tvg-id").lower()
    country_values = {part.strip() for part in re.split(r'[;,|]', country) if part.strip()}
    country_match = bool(country_values.intersection({"my", "mys", "malaysia"}))
    id_match = bool(re.search(r'\.my(?:@|$)', tvg_id))
    return country_match or id_match

def dedupe_key(extinf, stream_url):
    tvg_id = get_attr(extinf, "tvg-id").lower()
    if tvg_id:
        return ("id", tvg_id)
    # Without a stable channel ID, require the same title AND exact stream URL.
    title = normalize(get_title(extinf))
    return ("title-url", title, stream_url.strip().lower())

def valid_stream_url(stream_url):
    try:
        parsed = urlsplit(stream_url.strip())
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            return False
        host = parsed.hostname.lower()
        if host in {"localhost", "127.0.0.1", "::1"}:
            return False
        if host.endswith(".example.com") or host == "example.com":
            return False
        return True
    except ValueError:
        return False

def set_group(extinf, group):
    if re.search(r'\bgroup-title="[^"]*"', extinf):
        return re.sub(r'\bgroup-title="[^"]*"', lambda _: f'group-title="{group}"', extinf, count=1)
    head, separator, title = extinf.partition(",")
    return f'{head} group-title="{group}"{separator}{title}'

def build_hybrid_guide():
    lines = [
        f"# MY IPTV MASTER V{VERSION} — Platform Penstriman Rasmi Malaysia",
        "",
        "Playlist M3U utama mengandungi stream awam/yang dibenarkan sahaja.",
        "Pautan dalam panduan ini membuka laman atau aplikasi rasmi; ia BUKAN stream M3U.",
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
        "- OTT Navigator membaca stream M3U; ia tidak menukar pautan laman web atau aplikasi menjadi stream.",
        "- Ketersediaan kandungan, akaun, langganan dan sekatan lokasi ditentukan oleh penyiar.",
        "- Tiada URL dalaman aplikasi, DRM atau sekatan lokasi yang dipintas.",
        "- Kategori LIVE & GENERAL menempatkan entri Free-TV yang tidak dikenal pasti dalam kategori khusus.",
        "- Ketersediaan dan playback setiap stream perlu diuji dalam aplikasi.",
        "- EPG XMLTV belum disepadukan.",
    ])
    HYBRID_GUIDE.write_text("\n".join(lines) + "\n", encoding="utf-8")

def run_self_tests():
    sample_my = '#EXTINF:-1 tvg-id="TV1.my@SD" group-title="News",TV1'
    sample_nl = '#EXTINF:-1 tvg-id="BTLTV.nl@SD",BTL TV'
    sample_tw = '#EXTINF:-1 tvg-id="FTV.tw@SD",FTV'
    sample_country = '#EXTINF:-1 tvg-country="MY",Local Channel'
    assert is_malaysian_channel(sample_my)
    assert not is_malaysian_channel(sample_nl)
    assert not is_malaysian_channel(sample_tw)
    assert is_malaysian_channel(sample_country)
    assert get_attr(set_group(sample_my, "04 NEWS"), "group-title") == "04 NEWS"
    assert valid_stream_url("https://cdn.example.org/live.m3u8")
    assert not valid_stream_url("file:///tmp/channel.m3u8")
    assert not valid_stream_url("http://localhost/channel")
    print("Self-test: PASS (country filter, group assignment, URL validation)")

def main():
    run_self_tests()
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
    rejected_invalid = 0
    rejected_non_malaysia = []
    malaysia_titles = []
    free_tv_assigned = set()

    def add_records(records, group, source_label):
        nonlocal duplicates, rejected_invalid
        added = 0
        for extinf, stream_url in records:
            if not valid_stream_url(stream_url):
                rejected_invalid += 1
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
                malaysia_titles.append((get_title(extinf), get_attr(extinf, "tvg-id"), get_attr(extinf, "tvg-country")))
        return added

    malaysia_records = downloaded["malaysia"]
    verified_malaysia = []
    for extinf, stream_url in malaysia_records:
        if is_malaysian_channel(extinf):
            verified_malaysia.append((extinf, stream_url))
        else:
            rejected_non_malaysia.append(
                f"{get_title(extinf)} | tvg-id={get_attr(extinf, 'tvg-id') or 'tiada'} | tvg-country={get_attr(extinf, 'tvg-country') or 'tiada'}"
            )
    add_records(verified_malaysia, GROUPS[0], "IPTV-ORG Malaysia (verified)")

    add_records(downloaded["education"], GROUPS[1], "IPTV-ORG Education")
    add_records(downloaded["documentary"], GROUPS[2], "IPTV-ORG Documentary")
    add_records(downloaded["science"], GROUPS[2], "IPTV-ORG Science")
    add_records(downloaded["news"], GROUPS[3], "IPTV-ORG News")
    add_records(downloaded["sports"], GROUPS[5], "IPTV-ORG Sports")
    add_records(downloaded["movies"], GROUPS[6], "IPTV-ORG Movies")

    free_tv_rules = [
        (GROUPS[3], re.compile(r'\b(news|world news|international news|24h news|24 hour news)\b', re.I), "Free-TV News"),
        (GROUPS[5], re.compile(r'\b(sport|sports|football|soccer|tennis|badminton|basketball|cricket|motorsport)\b', re.I), "Free-TV Sports"),
        (GROUPS[6], re.compile(r'\b(movie|movies|cinema|film)\b', re.I), "Free-TV Movies"),
        (GROUPS[1], re.compile(r'\b(education|educational|learning|knowledge|school)\b', re.I), "Free-TV Learning"),
        (GROUPS[2], re.compile(r'\b(documentary|nature|wildlife|discovery|history|animal|science)\b', re.I), "Free-TV Discovery"),
    ]
    free_tv_records = downloaded["free_tv"]
    for group, pattern, source_label in free_tv_rules:
        matches = []
        for index, record in enumerate(free_tv_records):
            extinf, _ = record
            if index not in free_tv_assigned and pattern.search(get_title(extinf) + " " + get_attr(extinf, "group-title")):
                matches.append(record)
                free_tv_assigned.add(index)
        add_records(matches, group, source_label)

    # Keep remaining Free-TV entries available, but label them honestly as general live channels.
    remaining = [record for index, record in enumerate(free_tv_records) if index not in free_tv_assigned]
    add_records(remaining, GROUPS[4], "Free-TV General/Unclassified")

    with OUTFILE.open("w", encoding="utf-8", newline="\n") as playlist:
        playlist.write("#EXTM3U\n")
        for extinf, stream_url in output:
            playlist.write(extinf + "\n" + stream_url + "\n")

    build_hybrid_guide()

    report = [
        f"MY IPTV MASTER — BUILD REPORT v{VERSION} HYBRID",
        "",
        "RINGKASAN KATEGORI M3U:",
    ]
    for group in GROUPS:
        report.append(f"{group}: {counts[group]} saluran")
    report.extend([
        "",
        f"Jumlah saluran M3U: {len(output)}",
        f"Entri pendua ditolak: {duplicates}",
        f"URL tidak sah/ditolak: {rejected_invalid}",
        f"Entri bukan Malaysia ditolak daripada kategori TV Malaysia: {len(rejected_non_malaysia)}",
        "",
        "SENARAI TV MALAYSIA YANG DISAHKAN:",
    ])
    report.extend([
        f"- {name} | tvg-id={tvg_id or 'tiada'} | tvg-country={country or 'tiada'}"
        for name, tvg_id, country in malaysia_titles
    ] or ["- Tiada entri Malaysia yang melepasi penapis negara."])
    report.extend(["", "ENTRI DITOLAK DARIPADA KATEGORI TV MALAYSIA:"])
    report.extend([f"- {item}" for item in rejected_non_malaysia] or ["- Tiada."])
    report.extend(["", "SUMBER DAN JUMLAH:"])
    report.extend([f"{label}: {number}" for label, number in source_counts.items()])
    report.extend(["", "PLATFORM RASMI MALAYSIA (PAUTAN WEB/APLIKASI, BUKAN M3U):"])
    report.extend([f"- {item['name']}: {item['website']}" for item in OFFICIAL_MALAYSIA])
    report.extend(["", "SUMBER M3U:"])
    report.extend([f"- {name}: {url}" for name, url in SOURCES.items()])
    report.extend([
        "",
        "NOTA:",
        "- V3.2 mengasingkan NEWS daripada LIVE & GENERAL.",
        "- TV Malaysia ditapis menggunakan tvg-country (MY/MYS/Malaysia) atau tvg-id berakhiran .my.",
        "- Rekod yang tidak mempunyai bukti negara Malaysia tidak dimasukkan ke kategori TV Malaysia.",
        "- Free-TV yang tidak sepadan dengan kategori khusus diletakkan dalam LIVE & GENERAL.",
        "- Pendua tanpa tvg-id hanya ditolak jika nama dan URL stream sama.",
        "- Stream awam tidak semestinya boleh dimainkan dari Malaysia; playback belum diuji.",
        "- Tiada URL dalaman aplikasi, DRM atau sekatan lokasi yang dipintas.",
        "- EPG XMLTV belum disepadukan.",
    ])
    if failures:
        report.extend(["", "SUMBER GAGAL DIMUAT TURUN:"] + failures)

    REPORT.write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report))
    print(f"Generated: {OUTFILE}")
    print(f"Generated: {HYBRID_GUIDE}")
    print(f"Generated: {REPORT}")

if __name__ == "__main__":
    main()
