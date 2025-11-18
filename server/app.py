from flask import Flask, request, redirect, send_from_directory, jsonify
import requests
import json
import random
import os          
import logging

app = Flask(__name__, static_folder='.', static_url_path='')


INVIDIOUS = [
    "https://yt.drgnz.club",
    "https://invidious.tiekoetter.com",
    "https://invidious.fdn.fr",
    "https://inv.nadeko.net",
    "https://invidious.privacyredirect.com",
    "https://inv.odyssey346.dev",
    "https://invidious.nerdvpn.de",
    "https://invidious.projectsegfau.lt",
    "https://iv.ggtyler.dev",
    "https://invidious.asir.dev"
]

def get_working_instance():
    random.shuffle(INVIDIOUS)
    for url in INVIDIOUS:
        try:
            r = requests.get(f"{url}/api/v1/stats", timeout=7)
            if r.status_code == 200:
                return url.rstrip("/")
        except:
            pass
    return "https://yt.drgnz.club"  # ultimate fallback

INSTANCE = get_working_instance()
print(f"FLUX_LEEH USING INVIDIOUS: {INSTANCE}")

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    if os.path.isfile(filename):
        return send_from_directory('.', filename)
    return "Not found", 404

@app.route('/search')
def search():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify({"results": []})
    try:
        r = requests.get(f"{INSTANCE}/api/v1/search", params={'q': q}, timeout=15)
        data = r.json()
        results = []
        for v in data[:50]:
            if v.get('videoId'):
                results.append({
                    'id': v['videoId'],
                    'title': v.get('title', 'Unknown'),
                    'author': v.get('author', 'Unknown'),
                    'duration': v.get('lengthSeconds', 0),
                    'thumbnail': v['videoThumbnails'][-1]['url'] if v.get('videoThumbnails') else ''
                })
        return jsonify({"results": results})
    except Exception as e:
        print("Search error:", e)
        return jsonify({"results": []})

@app.route('/trending')
def trending():
    try:
        r = requests.get(f"{INSTANCE}/api/v1/trending", timeout=15)
        data = r.json()[:30]
        results = []
        for v in data:
            if v.get('videoId'):
                results.append({
                    'id': v['videoId'],
                    'title': v.get('title', 'Unknown'),
                    'author': v.get('author', 'Unknown'),
                    'duration': v.get('lengthSeconds', 0),
                    'thumbnail': v['videoThumbnails'][-1]['url'] if v.get('videoThumbnails') else ''
                })
        return jsonify({"results": results})
    except Exception as e:
        print("Trending error:", e)
        return jsonify({"results": []})

@app.route('/preview')
def preview():
    vid = request.args.get('id')
    if not vid:
        return "No ID", 400
    # 360p MP4 — plays instantly, no bot check
    return redirect(f"{INSTANCE}/latest_version?id={vid}&itag=18")

@app.route('/download')
def download():
    vid = request.args.get('id')
    fmt = request.args.get('format', 'mp3')
    if not vid:
        return "No ID", 400
    try:
        info = requests.get(f"{INSTANCE}/api/v1/videos/{vid}", timeout=15).json()
        title = "".join(c for c in f"{info.get('author','')} - {info.get('title','Video')}" 
                       if c.isalnum() or c in " -_()[]").strip()[:150]
        
        if fmt == 'mp3':
            # Best audio
            audio_streams = [s for s in info.get('formatStreams', []) if 'audio' in s.get('type', '')]
            stream = max(audio_streams, key=lambda x: x.get('quality', ''), default=audio_streams[0] if audio_streams else info['formatStreams'][0])
        else:
            # Best video ≤720p
            video_streams = [s for s in info.get('formatStreams', []) if 'video/mp4' in s.get('type', '')]
            stream = max(video_streams, key=lambda x: int(x['quality'].split('p')[0]) if 'p' in x['quality'] else 0)
        
        url = stream['url']
        return redirect(f"{url}&title={title}.{fmt}")
    except Exception as e:
        print("Download error:", e)
        return "Try again", 503

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print("FLUX_LEEH INVIDIOUS EDITION — FULLY WORKING NOV 2025")
    app.run(host='0.0.0.0', port=port)