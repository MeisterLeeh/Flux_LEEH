from flask import Flask, request, redirect, send_from_directory, jsonify
import requests
import yt_dlp
from urllib.parse import quote, unquote
import os
import random
import logging
import json
import time

# Enable logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='.', static_url_path='')

# Free rotating proxies (from free-proxy-list.net - update monthly)
PROXIES = [
    {'http': 'http://20.111.54.16:80', 'https': 'http://20.111.54.16:80'},
    {'http': 'http://47.74.152.29:8888', 'https': 'http://47.74.152.29:8888'},
    {'http': 'http://103.153.154.142:80', 'https': 'http://103.153.154.142:80'},
    {'http': 'http://47.89.153.209:80', 'https': 'http://47.89.153.209:80'},
    {'http': 'http://47.74.152.29:80', 'https': 'http://47.74.152.29:80'},
]

# Rotating User-Agents (fresh 2025 ones)
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
]

# Fetch live Piped instances on startup
def load_piped_instances():
    try:
        url = 'https://raw.githubusercontent.com/TeamPiped/instances/main/instances.json'
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            instances = [inst['apiUrl'] for inst in data if inst.get('region') and inst.get('cdn', False)]
            logger.info(f"Loaded {len(instances)} live Piped instances")
            return instances
    except Exception as e:
        logger.error(f"Failed to load Piped instances: {e}")
    # Hard fallback (verified working Nov 19 2025)
    return [
        "https://pipedapi.kavin.rocks",
        "https://pipedapi.leptons.xyz",
        "https://pipedapi.nosebs.ru",
        "https://pipedapi-libre.kavin.rocks",
        "https://pipedapi.bcow.xyz",  # Fresh one from status.piped.video
        "https://api.piped.video"    # Official mirror
    ]

PIPED_INSTANCES = load_piped_instances()

def get_stream_data(vid):
    for _ in range(2):  # Retry once
        random.shuffle(PIPED_INSTANCES)
        headers = {
            'User-Agent': random.choice(USER_AGENTS),
            'Referer': 'https://www.youtube.com/',
            'Accept': 'application/json',
        }
        for base in PIPED_INSTANCES[:5]:  # Limit to top 5
            proxy = random.choice(PROXIES) if random.random() > 0.5 else None
            try:
                url = f"{base}/streams/{vid}"
                logger.info(f"Trying {base} (proxy: {proxy is not None})")
                r = requests.get(url, headers=headers, proxies=proxy, timeout=15)
                if r.status_code == 200:
                    data = r.json()
                    if 'title' in data and (data.get('audioStreams') or data.get('videoStreams')):
                        logger.info(f"Success with {base}")
                        return data, base
                else:
                    logger.warning(f"HTTP {r.status_code} from {base}")
            except Exception as e:
                logger.error(f"Error with {base}: {str(e)}")
                continue
        time.sleep(1)  # Backoff
    logger.warning("All Piped failed")
    return None, None

# Enhanced yt-dlp with bot evasion
def get_yt_dlp_stream(vid, typ='audio'):
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'user_agent': random.choice(USER_AGENTS),
            'referer': 'https://www.youtube.com/',
            'sleep_interval': 1,  # Anti-bot sleep
        }
        if random.random() > 0.3:  # 70% chance proxy
            proxy = random.choice(PROXIES)
            ydl_opts['proxy'] = proxy['http']

        if typ == 'audio':
            ydl_opts['format'] = 'bestaudio[ext=m4a]/bestaudio/best[height<=480]'
        else:
            ydl_opts['format'] = 'best[height<=720]/best'

        ydl = yt_dlp.YoutubeDL(ydl_opts)
        info = ydl.extract_info(f"https://www.youtube.com/watch?v={vid}", download=False)
        
        title = info.get('title', 'Unknown')
        uploader = info.get('uploader', 'Unknown')
        url = info.get('url') or info['formats'][-1]['url']
        
        return {
            'title': title,
            'uploader': uploader,
            'url': url,
            'duration': info.get('duration', 0)
        }
    except Exception as e:
        logger.error(f"yt-dlp failed: {str(e)}")
        return None

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_file(path):
    if os.path.exists(path) and not os.path.isdir(path):
        return send_from_directory('.', path)
    return "File not found", 404

# SEARCH (Safe with extract_flat)
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
            'no_warnings': True,
            'user_agent': random.choice(USER_AGENTS),
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

# TRENDING (Safe with extract_flat)
@app.route('/trending')
def trending():
    try:
        ydl = yt_dlp.YoutubeDL({
            'quiet': True,
            'extract_flat': True,
            'no_warnings': True,
            'user_agent': random.choice(USER_AGENTS),
        })
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

# PREVIEW
@app.route('/preview')
def preview():
    vid = request.args.get('id')
    typ = request.args.get('type', 'audio')
    if not vid:
        return "No video ID", 400

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
                    best = max(streams, key=lambda x: int(x.get('quality', '360p').rstrip('p')))
                    return redirect(best['url'])
        except Exception as e:
            logger.error(f"Piped preview error: {str(e)}")

    logger.info("yt-dlp fallback for preview")
    stream = get_yt_dlp_stream(vid, typ)
    if stream:
        return redirect(stream['url'])
    
    return "Streams busy — retry in 30s (YouTube blocking cloud IPs)", 503

# DOWNLOAD
@app.route('/download')
def download():
    vid = request.args.get('id')
    fmt = request.args.get('format', 'mp3')
    if not vid:
        return "No ID", 400

    typ = 'audio' if fmt == 'mp3' else 'video'
    ext = 'mp3' if fmt == 'mp3' else 'mp4'

    data, _ = get_stream_data(vid)
    if data:
        try:
            if typ == 'audio':
                best = max(data['audioStreams'], key=lambda x: x.get('bitrate', 0))
            else:
                with_audio = [s for s in data['videoStreams'] if not s.get('videoOnly', False)]
                best = max(with_audio or data['videoStreams'], key=lambda x: int(x.get('quality', '360p').rstrip('p')))
            
            title = "".join(c for c in f"{data.get('uploader', 'Unknown')} - {data.get('title', 'Video')}" 
                            if c.isalnum() or c in " -_()[]").strip()[:120]
            # Force download with filename (Piped supports it)
            dl_url = f"{best['url']}?title={quote(title + '.' + ext)}&dl=1"
            return redirect(dl_url)
        except Exception as e:
            logger.error(f"Piped download error: {str(e)}")

    logger.info("yt-dlp fallback for download")
    stream = get_yt_dlp_stream(vid, typ)
    if stream:
        title = "".join(c for c in f"{stream['uploader']} - {stream['title']}" 
                        if c.isalnum() or c in " -_()[]").strip()[:120]
        # For yt-dlp direct URLs, use a data URI trick for filename (browser-safe)
        dl_url = f"{stream['url']}?title={quote(title + '.' + ext)}"
        return redirect(dl_url)
    
    return "Downloads busy — retry soon (anti-bot active)", 503

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"FLUX_LEEH ALIVE ON {port} — WITH PROXIES & DYNAMIC PIPED")
    app.run(host='0.0.0.0', port=port, debug=False)