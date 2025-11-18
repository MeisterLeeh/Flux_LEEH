from flask import Flask, request, redirect, send_from_directory, jsonify
import requests
import yt_dlp
from urllib.parse import quote
import os
import random
import logging

# Enable logging to see what's failing on Render
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='.', static_url_path='')

# FRESH WORKING INSTANCES (VERIFIED NOV 18 2025 VIA OFFICIAL PIPED DOCS)
PIPED_INSTANCES = [
    "https://pipedapi.kavin.rocks",           # Official, CDN-backed, most reliable
    "https://pipedapi-libre.kavin.rocks",     # Official libre, no CDN but stable
    "https://pipedapi.leptons.xyz",           # Austria-based, low latency
    "https://pipedapi.nosebs.ru",             # Finland, good for EU/ZA
    "https://pipedapi.mha.fi",                # Fresh, API-focused
    "https://api.piped.privacydev.net"        # Privacy-focused, works on clouds
]

def get_stream_data(vid):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    random.shuffle(PIPED_INSTANCES)  # Rotate for fairness
    for base in PIPED_INSTANCES:
        try:
            url = f"{base}/streams/{vid}"
            logger.info(f"Trying Piped instance: {base} for vid {vid}")
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code == 200:
                data = r.json()
                if 'title' in data and (data.get('audioStreams') or data.get('videoStreams')):
                    logger.info(f"Success with {base}")
                    return data, base
                else:
                    logger.warning(f"Empty data from {base}")
            else:
                logger.warning(f"HTTP {r.status_code} from {base}")
        except Exception as e:
            logger.error(f"Error with {base}: {str(e)}")
            continue
    logger.warning("All Piped instances failed")
    return None, None

# YT-DLP FALLBACK HELPER (Direct stream extraction)
def get_yt_dlp_stream(vid, typ='audio'):
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,  # Full extract for URLs
        }
        if typ == 'audio':
            ydl_opts['format'] = 'bestaudio[ext=m4a]/bestaudio/best'
        else:
            ydl_opts['format'] = 'best[height<=720]/best'
        
        ydl = yt_dlp.YoutubeDL(ydl_opts)
        info = ydl.extract_info(f"https://www.youtube.com/watch?v={vid}", download=False)
        
        # Get title for filename
        title = info.get('title', 'Unknown')
        uploader = info.get('uploader', 'Unknown')
        
        # Get direct URL
        if typ == 'audio':
            url = info['url'] if 'url' in info else info['formats'][-1]['url']
        else:
            url = info['url'] if 'url' in info else info['formats'][-1]['url']
        
        return {
            'title': title,
            'uploader': uploader,
            'url': url,
            'duration': info.get('duration', 0)
        }
    except Exception as e:
        logger.error(f"yt-dlp fallback failed: {str(e)}")
        return None

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_file(path):
    if os.path.exists(path) and not os.path.isdir(path):
        return send_from_directory('.', path)
    return "File not found", 404

# SEARCH (Unchanged, works fine)
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
    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        return jsonify({"results": []})

# TRENDING (Unchanged)
@app.route('/trending')
def trending():
    try:
        ydl = yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': True, 'no_warnings': True})
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
    except Exception as e:
        logger.error(f"Trending failed: {str(e)}")
        return jsonify({"results": []})

# PREVIEW — Piped + yt-dlp fallback
@app.route('/preview')
def preview():
    vid = request.args.get('id')
    typ = request.args.get('type', 'audio')
    if not vid:
        return "No video ID", 400

    # Try Piped first
    data, _ = get_stream_data(vid)
    if data:
        try:
            if typ == 'audio':
                streams = data.get('audioStreams', [])
                if streams:
                    best = max(streams, key=lambda x: x.get('bitrate', 0))
                    return redirect(best['url'])
            else:
                streams = data.get('videoStreams', [])
                if streams:
                    best = max(streams, key=lambda x: int(x['quality'].split('p')[0]) if 'p' in x['quality'] else 0)
                    return redirect(best['url'])
        except Exception as e:
            logger.error(f"Piped preview error: {str(e)}")

    # Fallback to yt-dlp
    logger.info("Falling back to yt-dlp for preview")
    stream = get_yt_dlp_stream(vid, typ)
    if stream:
        return redirect(stream['url'])
    
    return "Stream unavailable — all services busy. Try again in 1 min.", 503

# DOWNLOAD — Piped + yt-dlp fallback with filename
@app.route('/download')
def download():
    vid = request.args.get('id')
    fmt = request.args.get('format', 'mp3')
    if not vid:
        return "No ID", 400

    typ = 'audio' if fmt == 'mp3' else 'video'
    ext = 'mp3' if fmt == 'mp3' else 'mp4'

    # Try Piped first
    data, _ = get_stream_data(vid)
    if data:
        try:
            if typ == 'audio':
                best = max(data['audioStreams'], key=lambda x: x.get('bitrate', 0))
            else:
                with_audio = [s for s in data['videoStreams'] if not s.get('videoOnly', False)]
                best = max(with_audio or data['videoStreams'], key=lambda x: int(x['quality'].split('p')[0]) if 'p' in x['quality'] else 0)
            
            title = "".join(c for c in f"{data.get('uploader','Unknown')} - {data.get('title','Video')}" 
                           if c.isalnum() or c in " -_()[]").strip()[:120]
            dl_url = f"{best['url']}#dl&title={quote(title + '.' + ext)}"
            return redirect(dl_url)
        except Exception as e:
            logger.error(f"Piped download error: {str(e)}")

    # Fallback to yt-dlp
    logger.info("Falling back to yt-dlp for download")
    stream = get_yt_dlp_stream(vid, typ)
    if stream:
        title = "".join(c for c in f"{stream['uploader']} - {stream['title']}" 
                       if c.isalnum() or c in " -_()[]").strip()[:120]
        # yt-dlp URLs are direct; browser handles download
        return redirect(f"{stream['url']}#dl&title={quote(title + '.' + ext)}")
    
    return "Download unavailable — try again.", 503

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)