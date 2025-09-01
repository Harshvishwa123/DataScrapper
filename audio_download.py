import os
import csv
import json
import time
import random
from yt_dlp import YoutubeDL

# ================== CONFIG ==================
CSV_PATH = "/Users/yamansmac/Downloads/Audino Bugs - Sheet10.csv"
OUTPUT_DIR = "/Users/yamansmac/Downloads/New_data"
COOKIE_FILE = "/Users/yamansmac/Downloads/Audino_data_scraping/www.youtube.com_cookies (7).txt"
COOLDOWN_RANGE = (15, 30)  # seconds between downloads

# Only download manual subtitles in these languages:
COMMON_LANGS = ["en", "es", "fr", "de", "hi", "it", "ja", "zh-Hans", "zh-Hant", "pt", "ar", "ru"]
CSV_LINK_COLUMN = "link"
# ============================================

os.makedirs(OUTPUT_DIR, exist_ok=True)

def _vtt_to_text(vtt_str: str) -> str:
    """Very simple VTT → text: drop headers, cue numbers, timestamps."""
    lines = []
    for line in vtt_str.splitlines():
        s = line.strip("\ufeff").strip()
        if not s:
            continue
        if s.upper().startswith("WEBVTT"):
            continue
        if "-->" in s:   # timestamp line
            continue
        if s.isdigit():  # cue number
            continue
        lines.append(s)
    return " ".join(lines)

def _srt_to_text(srt_str: str) -> str:
    """Very simple SRT → text."""
    lines = []
    for line in srt_str.splitlines():
        s = line.strip("\ufeff").strip()
        if not s:
            continue
        if "-->" in s:
            continue
        if s.isdigit():
            continue
        lines.append(s)
    return " ".join(lines)

def _json3_to_text(json_str: str) -> str:
    """YouTube JSON3 → text (concatenate seg utf8)."""
    try:
        obj = json.loads(json_str)
    except Exception:
        return ""
    parts = []
    for ev in obj.get("events", []):
        for seg in ev.get("segs", []) or []:
            t = seg.get("utf8", "")
            if t:
                parts.append(t)
    return " ".join(parts).strip()

def read_csv_urls(csv_path: str, col: str):
    urls = []
    # utf-8-sig handles BOM from Excel
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if col not in (reader.fieldnames or []):
            raise ValueError(f"CSV must contain a '{col}' column. Found: {reader.fieldnames}")
        for row in reader:
            url = (row.get(col) or "").strip()
            if url:
                urls.append(url)
    return list(set(urls))  # Deduplicate

def download_one(url: str):
    """
    Downloads MP3 and manual subtitles (COMMON_LANGS only).
    Saves metadata + plain-text transcripts (per language) to <id>.json
    """
    vid = None
    try:
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": os.path.join(OUTPUT_DIR, "%(id)s.%(ext)s"),
            "noplaylist": True,
            "cookiefile": COOKIE_FILE,
            "writesubtitles": True,           # manual subs only
            "writeautomaticsub": False,       # NO auto subs
            "subtitleslangs": COMMON_LANGS,   # respect common languages list
            "subtitlesformat": "vtt",
            "retries": 3,
            "fragment_retries": 3,
            "skip_unavailable_fragments": True,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
            "quiet": True,
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

            vid = info.get("id")
            base = os.path.join(OUTPUT_DIR, vid)

            # Skip if already downloaded
            if os.path.exists(f"{base}.mp3") and os.path.exists(f"{base}.json"):
                print(f"⏩ Skipping {vid} (already downloaded)")
                return

            # Build metadata
            meta = {
                "id": vid,
                "title": info.get("title"),
                "uploader": info.get("uploader"),
                "channel_id": info.get("channel_id"),
                "upload_date": info.get("upload_date"),
                "duration": info.get("duration"),
                "view_count": info.get("view_count"),
                "like_count": info.get("like_count"),
                "source_url": url,                 # original video URL
                "mp3_file": f"{vid}.mp3",          # local audio filename
                "transcriptions": {},              # {lang: text}
            }

            # Figure out what subs were actually requested & saved
            requested = info.get("requested_subtitles") or {}
            manual = info.get("subtitles") or {}

            for lang, subinfo in requested.items():
                if lang not in manual:
                    continue

                ext = (subinfo.get("ext") or "").lower()
                text = ""

                candidate_paths = [
                    f"{base}.{lang}.{ext}",
                    f"{base}.{lang}.vtt",
                    f"{base}.{lang}.json3",
                    f"{base}.{lang}.srt",
                ]
                file_path = next((p for p in candidate_paths if os.path.exists(p)), None)

                if file_path:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as sf:
                        raw = sf.read()
                    if file_path.endswith(".vtt"):
                        text = _vtt_to_text(raw)
                    elif file_path.endswith(".srt"):
                        text = _srt_to_text(raw)
                    elif file_path.endswith(".json3"):
                        text = _json3_to_text(raw)
                    else:
                        text = raw.strip()
                else:
                    sub_url = subinfo.get("url")
                    if sub_url:
                        raw = ydl.urlopen(sub_url).read().decode("utf-8", errors="ignore")
                        if ext == "vtt":
                            text = _vtt_to_text(raw)
                        elif ext == "srt":
                            text = _srt_to_text(raw)
                        elif ext == "json3":
                            text = _json3_to_text(raw)
                        else:
                            text = raw.strip()

                if text:
                    meta["transcriptions"][lang] = text

            # Save JSON
            json_path = f"{base}.json"
            try:
                with open(json_path, "w", encoding="utf-8") as jf:
                    json.dump(meta, jf, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"❌ Failed to write JSON for {vid}: {e}")
                return

            print(f"✅ {vid}: saved MP3 + JSON with transcripts ({', '.join(meta['transcriptions'].keys()) or 'none'})")

    except Exception as e:
        print(f"❌ Error processing {url} (video ID: {vid}): {e}")

def main():
    try:
        urls = read_csv_urls(CSV_PATH, CSV_LINK_COLUMN)
    except Exception as e:
        print(f"❌ Failed to read CSV: {e}")
        return

    print(f"Found {len(urls)} unique URLs.")
    for i, url in enumerate(urls, 1):
        if "youtube.com/" not in url and "youtu.be/" not in url:
            print(f"❌ Skipping non-YouTube URL: {url}")
            continue

        print(f"[{i}/{len(urls)}] {url}")
        download_one(url)

        if i < len(urls):
            pause = random.randint(*COOLDOWN_RANGE)
            print(f"⏳ Cooldown {pause}s...\n")
            time.sleep(pause)

if __name__ == "__main__":
    main()