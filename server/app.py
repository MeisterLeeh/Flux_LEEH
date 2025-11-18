from flask import Flask, request, jsonify, send_from_directory, redirect
import requests
import os
from urllib.parse import quote

app = Flask(__name__, static_folder='.', static_url_path='')

# Working Piped instances (November 2025)
PIPED_INSTANCES = [
    "https://pipedapi.kavin.rocks",
    "https://pipedapi.mha.fi",
    "https://api.piped.privacydev.net",
]

def get_working_piped():
    for url in PIPED_INSTANCES:
        try:
            test = requests.get(f"{url}/trending?region=ZA", timeout=5)
            if test.status_code == 200:
                return url
        except:
            continue
    return PIPED_INSTANCES[0]  # fallback

PIPED = get_working_piped()

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    if os.path.exists(path):
        return send_from_directory('.', path)
    return "Not found", 404

# Search & Trending still use yt-dlp (lightweight, rarely blocked)
@app.route('/search')
def search():
    q = request.args.get('q', '')
    if not q: return jsonify({"results": []})
    try:
        import yt_dlp
        ydl = yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': True, 'skip_download': True})
        r = ydl.extract_info(f"ytsearch50:{q}", download=False)
        entries = r.get('entries', [])
        results = []
        for e in entries:
            if e: results.append({
                'id': e['id'],
                'title': e.get('title', 'Unknown'),
                'thumbnail': f"https://i.ytimg.com/vi/{e['id']}/hqdefault.jpg",
                'duration': e.get('duration', 0),
                'author': e.get('uploader', 'Unknown')
            })
        return jsonify({"results": results[:50]})
    except:
        return jsonify({"results": []})

@app.route('/trending')
def trending():
    try:
        import yt_dlp
        ydl = yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': True, 'skip_download': True})
        r = ydl.extract_info("ytsearch50:amapiano 2025 south africa trending", download=False)
        entries = r.get('entries', [])
        results = []
        for e in entries:
            if e: results.append({
                'id': e['id'],
                'title': e.get('title', 'Unknown'),
                'thumbnail': f"https://i.ytimg.com/vi/{e['id']}/hqdefault.jpg",
                'duration': e.get('duration', 0),
                'author': e.get('uploader', 'Unknown')
            })
        return jsonify({"results": results[:50]})
    except:
        return jsonify({"results": []})

# PREVIEW & DOWNLOAD → 100% via Piped = ZERO BOT ERRORS
@app.route('/preview')
def preview():
    vid = request.args.get('id')
    typ = request.args.get('type', 'audio')
    if not vid: return "No ID", 400
    try:
        data = requests.get(f"{PIPED}/streams/{vid}").json()
        streams = data.get('audioStreams') if typ == 'audio' else data.get('videoStreams')
        best = max(streams, key=lambda x: x.get('quality', '0p') if typ != 'audio' else x.get('bitrate', 0))
        return redirect(best['url'])
    except:
        return "Preview failed", 500

@app.route('/download')
def download():
    vid = request.args.get('id')
    fmt = request.args.get('format', 'mp3')
    if not vid: return "No ID", 400
    try:
        data = requests.get(f"{PIPED}/streams/{vid}").json()
        title = "".join(c for c in f"{data.get('uploader','')} - {data.get('title','Video')}" if c.isalnum() or c in " -_()").strip()[:150]

        if fmt == 'mp3':
            best = max(data.get('audioStreams', []), key=lambda x: x.get('bitrate', 0))
        else:
            best = max([s for s in data.get('videoStreams', []) if s.get('videoOnly') == False], key=lambda x: x.get('quality', ''))
            if not best: best = data['videoStreams'][0]

        url = best['url']
        ext = 'mp3' if fmt == 'mp3' else 'mp4'
        return redirect(f"{url}&title={quote(title)}.{ext}")
    except Exception as e:
        print(e)
        return "Download failed — try again", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    print(f"FLUX_LEEH IS FULLY ALIVE on port {port} 🇿🇦")
    app.run(host='0.0.0.0', port=port)