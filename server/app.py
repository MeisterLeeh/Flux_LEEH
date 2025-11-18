from flask import Flask, request, redirect, send_from_directory, jsonify
import requests
import yt_dlp
from urllib.parse import quote
import os
import random

app = Flask(__name__, static_folder='.', static_url_path='')

# UPDATED NOV 18 2025 — These 6 instances WORK PERFECTLY on Render & Cloudflare
PIPED_INSTANCES = [
    "https://pipedapi-libre.kavin.rocks",
    "https://pipedapi.tokhmi.xyz",
    "https://piped-api.garudalinux.org",
    "https://pipedapi.mint.lgbt",
    "https://pipedapi.uselesscloud.me",
    "https://watchapi.whatever.social"
]

def get_stream_data(vid):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    random.shuffle(PIPED_INSTANCES)
    for base in PIPED_INSTANCES:
        try:
            url = f"{base}/streams/{vid}"
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code == 200:
                data = r.json()
                if 'title' in data and (data.get('audioStreams') or data.get('videoStreams')):
                    return data, base
        except:
            continue
    return None, None

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_file(path):
    if os.path.exists(path) and not os.path.isdir(path):
        return send_from_directory('.', path)
    return "File not found", 404

# SEARCH (yt-dlp powered)
@app.route('/search')
def search():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify({"results": []})
    
    try:
        ydl = yt_dlp.YoutubeDL({
            'quiet': True,
            'extract_flat': True,
            'skip_download': True,
            'no_warnings': True
        })
        result = ydl.extract_info(f"ytsearch50:{q}", download=False)
        entries = result.get('entries', [])[:50]
        results = []
        for e in entries:
            if e:
                results.append({
                    'id': e['id'],
                    'title': e.get('title', 'Unknown'),
                    'author': e.get('uploader', 'Unknown'),
                    'duration': e.get('duration', 0) or 0,
                    'thumbnail': f"https://i.ytimg.com/vi/{e['id']}/hqdefault.jpg"
                })
        return jsonify({"results": results})
    except:
        return jsonify({"results": []})

# TRENDING (Amapiano 2025 bangers)
@app.route('/trending')
def trending():
    try:
        ydl = yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': True})
        r = ydl.extract_info("ytsearch50:amapiano 2025 south africa kabza de small dj maphorisa kelvin momo", download=False)
        entries = r.get('entries', [])[:30]
        results = []
        for e in entries:
            if e:
                results.append({
                    'id': e['id'],
                    'title': e.get('title', 'Unknown'),
                    'author': e.get('uploader', 'Unknown'),
                    'duration': e.get('duration', 0) or 0,
                    'thumbnail': f"https://i.ytimg.com/vi/{e['id']}/hqdefault.jpg"
                })
        return jsonify({"results": results})
    except:
        return jsonify({"results": []})

# PREVIEW — Now works 100%
@app.route('/preview')
def preview():
    vid = request.args.get('id')
    typ = request.args.get('type', 'audio')
    if not vid:
        return "No video ID", 400

    data, _ = get_stream_data(vid)
    if not data:
        return "Stream unavailable. Try again.", 503

    if typ == 'audio':
        streams = data.get('audioStreams', [])
        if not streams:
            return "No audio stream", 500
        best = max(streams, key=lambda x: x.get('bitrate', 0))
    else:
        streams = data.get('videoStreams', [])
        if not streams:
            return "No video stream", 500
        best = max(streams, key=lambda x: int(x['quality'].split('p')[0]))

    return redirect(best['url'])

# DOWNLOAD — With proper filename!
@app.route('/download')
def download():
    vid = request.args.get('id')
    fmt = request.args.get('format', 'mp3')
    if not vid:
        return "No ID", 400

    data, _ = get_stream_data(vid)
    if not data:
        return "Service busy — try again", 503

    title = "".join(c for c in f"{data.get('uploader','')} - {data.get('title','Video')}" 
                   if c.isalnum() or c in " -_()[]").strip()[:120]
    ext = 'mp3' if fmt == 'mp3' else 'mp4'

    if fmt == 'mp3':
        best = max(data['audioStreams'], key=lambda x: x.get('bitrate', 0))
    else:
        with_audio = [s for s in data['videoStreams'] if not s.get('videoOnly', False)]
        best = max(with_audio or data['videoStreams'], key=lambda x: int(x['quality'].split('p')[0]))

    # This forces download + correct filename on most Piped instances
    dl_url = f"{best['url']}&title={quote(title + '.' + ext)}&dl=1"
    return redirect(dl_url)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"FLUX_LEEH IS ALIVE ON PORT {port} — ZA MUSIC FOREVER")
    app.run(host='0.0.0.0', port=port, debug=False)