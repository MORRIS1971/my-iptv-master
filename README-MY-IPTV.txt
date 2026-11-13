# MY IPTV MASTER PLAYLIST — Builder Pack

## Kandungan
- `build_my_iptv_master.py` — memuat turun playlist awam dan menggabungkan saluran mengikut enam kategori.
- `BUILD-MY-IPTV.bat` — pelancar Windows satu klik.
- Output selepas dijalankan:
  - `MY-IPTV-MASTER.m3u`
  - `BUILD-REPORT.txt`

## Cara guna (Windows)
1. Pasang Python 3 jika belum ada.
2. Ekstrak folder ini.
3. Pastikan komputer mempunyai sambungan Internet.
4. Klik dua kali `BUILD-MY-IPTV.bat`.
5. Selepas selesai, buka OTT Navigator > Playlist > Add provider/playlist.
6. Pilih fail `MY-IPTV-MASTER.m3u` daripada storan peranti, atau salin fail itu ke peranti TV.

## Enam kategori
1. TV MALAYSIA
2. LEARNING CHANNELS
3. DISCOVERY CHANNELS
4. LIVE CHANNELS
5. SPORTS
6. MOVIES

## Sumber
- IPTV-ORG public country/category playlists
- Free-TV public playlist

## Had yang perlu difahami
- Builder ini memerlukan Internet ketika dijalankan untuk mendapatkan versi sumber terkini.
- Ia menghasilkan fail M3U tempatan, bukan URL hosting kekal.
- Ia mengekalkan metadata `tvg-id` dan `tvg-logo` yang wujud dalam sumber.
- EPG tidak digabungkan secara automatik; perlu ditambah melalui sumber EPG yang sepadan dengan `tvg-id`.
- Senarai sukan tidak menjamin siaran EPL atau badminton premium. Hak siaran berbayar tidak dibuka.
- Tiada DRM, login, paywall atau geo-block yang dipintas.
- Pembinaan ini belum diuji pada OTT Navigator sebenar atau diuji dari rangkaian Malaysia.
