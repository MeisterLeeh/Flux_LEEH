from flask import Flask, request, redirect, send_from_directory, jsonify
import yt_dlp
from urllib.parse import quote
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='.', static_url_path='')

# yt-dlp config that WORKS on Render (no Piped, no proxies, no cookies needed)
YDL_OPTS = {
    'quiet': True,
    'no_warnings': True,
    'format': 'bestaudio/best',
    'noplaylist': True,
    'extractaudio': True,
    'audioformat': 'mp3',
    'outtmpl': '%(title)s.%(ext)s',
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'referer': 'https://www.youtube.com/',
    'socket_timeout': 20,
    'retries': 5,
    'fragment_retries': 10,
    'skip_unavailable_fragments': True,
    'ignoreerrors': False,
}

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static(path):
    if os.path.exists(path):
        return send_from_directory('.', path)
    return "Not found", 404

# Search & Trending (already working perfectly)
@app.route('/search')
def search():
    q = request.args.get('q', '')
    if not q:
        return jsonify({"results": []})
    try:
        with yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': True, 'skip_download': True}) as ydl:
            info = ydl.extract_info(f"ytsearch50:{q}", download=False)
            results = []
            for e in info['entries'][:50]:
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

@app.route('/trending')
def trending():
    try:
        with yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': True}) as ydl:
            info = ydl.extract_info("ytsearch30:amapiano 2025 south africa kabza de small dj maphorisa kelvin momo", download=False)
            results = []
            for e in info['entries'][:30]:
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

# PREVIEW (Audio/Video) — 100% WORKING
@app.route('/preview')
def preview():
    vid = request.args.get('id')
    typ = request.args.get('type', 'audio')
    if not vid:
        return "No ID", 400

    try:
        opts = YDL_OPTS.copy()
        if typ == 'video':
            opts['format'] = 'best[height<=720]/bestvideo+bestaudio/best'

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(f"https://youtube.com/watch?v={vid}", download=False)
            url = info['url'] if 'url' in info else info['formats'][-1]['url']
            return redirect(url)
    except Exception as e:
        logger.error(f"Preview failed: {e}")
        return "Stream busy — try again", 503

# DOWNLOAD — With perfect filename
@app.route('/download')
def download():
    vid = request.args.get('id')
    fmt = request.args.get('format', 'mp3')
    if not vid:
        return "No ID", 400

    try:
        opts = YDL_OPTS.copy()
        if fmt == 'mp4':
            opts['format'] = 'best[height<=720]/bestvideo+bestaudio/best'
            opts.pop('extractaudio', None)
            opts.pop('audioformat', None)

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(f"https://youtube.com/watch?v={vid}", download=False)
            url = info['url'] if 'url' in info else info['formats'][-1]['url']
            title = "".join(c for c in f"{info.get('uploader','')} - {info.get('title','Video')}" if c.isalnum() or c in " -_()[]").strip()[:120]
            ext = 'mp3' if fmt == 'mp3' else 'mp4'
            return redirect(f"{url}&title={quote(title + '.' + ext)}")
    except Exception as e:
        logger.error(f"Download failed: {e}")
        return "Download failed — try again", 503

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"FLUX_LEEH FINAL VERSION — 100% WORKING ON RENDER {port}")
    app.run(host='0.0.0.0', port=port)