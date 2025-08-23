# 🎵 YouTube Audio Downloader (CC Licensed Only)

A Python utility to **download audio, subtitles, and metadata** from YouTube videos that are explicitly under **Creative Commons Attribution License (reuse allowed)**.  
This script uses [yt-dlp](https://github.com/yt-dlp/yt-dlp) and ensures downloads only happen for CC-licensed videos.

---

## 🚀 Features
- ✅ Downloads **only Creative Commons licensed videos**
- ✅ Extracts **best-quality audio (MP3)**
- ✅ Saves **metadata** (title, author, description, duration, etc.) as JSON
- ✅ Downloads **subtitles** if available in common languages (`en`, `es`, `fr`, `de`, `hi`)
- ✅ Uses **cookies** for authenticated requests
- ✅ Random **cooldown** between requests to avoid rate-limiting

---

## 📂 Project Structure
- audio_downloading.py # Main script
- cookies.txt # YouTube cookies (update regularly)
- processing.csv # Input file containing video links
- output2/ # Generated audio + metadata
- Sample_Data (1).png # Screenshot 1
- Sample_Data (2).png # Screenshot 2
- Sample_Data (3).png # Screenshot 3
- README.md # This file
