import yt_dlp
import os
import re
import subprocess

print("This app made by Suraj Gehlot")
print("Enter URLs one by one. Type 'exit' to stop.")

download_path = os.path.join(os.environ.get('EXTERNAL_STORAGE', '/sdcard'), 'Download')

if not os.path.exists(download_path):
    os.makedirs(download_path)

def download_and_scan(url):
    ydl_opts = {
        'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
        'noplaylist': True,
    }

    def is_youtube_url(url):
        return re.search(r'(youtube\.com|youtu\.be)', url) is not None

    if is_youtube_url(url):
        print("YouTube link detected. Fetching common qualities (1080p, 720p, 480p, 360p)...")
        ydl = yt_dlp.YoutubeDL({'quiet': True})
        info = ydl.extract_info(url, download=False)
        formats = info.get('formats', [])

        # Common resolutions we want: 1080, 720, 480, 360 (and audio only if needed)
        target_heights = [1080, 720, 480, 360]
        quality_options = {}
        option_num = 1

        for height in target_heights:
            best_for_height = None
            best_size = 0
            for f in formats:
                if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                    if f.get('height') == height:
                        size = f.get('filesize_approx', 0) or f.get('filesize', 0)
                        if size > best_size:
                            best_size = size
                            best_for_height = f
            if best_for_height:
                size_mb = best_size / (1024 * 1024) if best_size else 'Unknown'
                print(f"{option_num}: {height}p mp4 (\~{size_mb:.2f} MB)")
                quality_options[option_num] = best_for_height['format_id']
                option_num += 1

        if not quality_options:
            print("No common resolutions found. Using best available.")
            ydl_opts['format'] = 'bestvideo+bestaudio/best'
        else:
            print(f"{option_num}: Best available (highest quality)")
            quality_options[option_num] = 'bestvideo+bestaudio/best'

            choice = int(input("Enter quality number: "))
            if choice in quality_options:
                ydl_opts['format'] = quality_options[choice]
            else:
                ydl_opts['format'] = 'bestvideo+bestaudio/best'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            filename = ydl.prepare_filename(info)
            full_path = os.path.join(download_path, filename)
            ydl.download([url])

        # Fast scan
        try:
            subprocess.run(['termux-media-scan', full_path], check=True, timeout=5)
            print("Fast media scan done.")
        except:
            subprocess.run(['am', 'broadcast', '-a', 'android.intent.action.MEDIA_SCANNER_SCAN_FILE', '-d', f'file://{full_path}'])
            print("Fallback broadcast sent.")

        print(f"Download complete: {full_path}")
        print("Video should appear in gallery. Swipe down in Gallery to refresh instantly (no restart needed).")
    except Exception as e:
        print(f"Error: {e}. Moving to next URL...")

while True:
    url = input("Enter URL (or 'exit'): ")
    if url.lower() == 'exit':
        break
    if url.strip():
        download_and_scan(url)
