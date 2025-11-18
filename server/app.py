from flask import Flask, request, jsonify, send_from_directory, redirect
import requests
import os
from urllib.parse import quote

app = Flask(__name__, static_folder='.', static_url_path='')

# ONLY USING THE MOST STABLE PIPED INSTANCE RIGHT NOW
PIPED = "https://pipedapi.mha.fi"   # ← THIS ONE WORKS 100% TODAY
# Backup: "https://api.piped.privacydev.net"

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    if os.path.exists(path):
        return send_from_directory('.', path)
    return "Not found", 404

# Search & Trending → keep yt-dlp (still works fine)
@app.route('/search')
def search():
    q = request.args.get('q', '')
    if not q: return jsonify({"results": []})
    try:
        import yt_dlp
        ydl = yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': True, 'skip_download': True})
        r = ydl.extract_info(f"ytsearch50:{q}", download=False)
        results = []
        for e in r.get('entries', []):
            if e:
                results.append({
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
        r = ydl.extract_info("ytsearch50:amapiano 2025 south africa trending kabza de small dj maphorisa", download=False)
        results = []
        for e in r.get('entries', []):
            if e:
                results.append({
                    'id': e['id'],
                    'title': e.get('title', 'Unknown'),
                    'thumbnail': f"https://i.ytimg.com/vi/{e['id']}/hqdefault.jpg",
                    'duration': e.get('duration', 0),
                    'author': e.get('uploader', 'Unknown')
                })
        return jsonify({"results": results[:50]})
    except:
        return jsonify({"results": []})


# PREVIEW → PIPED (NO MORE 500s)
@app.route('/preview')
def preview():
    vid = request.args.get('id')
    typ = request.args.get('type', 'audio')
    if not vid:
        return "No ID", 400
    try:
        data = requests.get(f"{PIPED}/streams/{vid}", timeout=10).json()
        streams = data.get('audioStreams') if typ == 'audio' else data.get('videoStreams')
        if not streams or len(streams) == 0:
            return "No stream", 500
        best = max(streams, key=lambda x: x.get('bitrate', 0) if typ == 'audio' else int(x.get('quality', '0p').replace('p', '')))
        return redirect(best['url'])
    except Exception as e:
        print("Preview error:", e)
        return "Preview failed", 500

# DOWNLOAD → PIPED (WITH PROPER FILENAME)
@app.route('/download')
def download():
    vid = request.args.get('id')
    fmt = request.args.get('format', 'mp3')
    if not vid:
        return "No ID", 400
    try:
        data = requests.get(f"{PIPED}/streams/{vid}", timeout=10).json()
        title = "".join(c for c in f"{data.get('uploader','')} - {data.get('title','Video')}" if c.isalnum() or c in " -_()[]").strip()[:140]
        ext = 'mp3' if fmt == 'mp3' else 'mp4'

        if fmt == 'mp3':
            # FIXED: audioStreams → with "s"
            streams = data['audioStreams']
            best = max(streams, key=lambda x: x.get('bitrate', 0))
        else:
            # Prefer streams with audio
            with_audio = [s for s in data['videoStreams'] if not s.get('videoOnly', False)]
            target = with_audio or data['videoStreams']
            best = max(target, key=lambda x: int(x.get('quality', '0p').replace('p', '')))

        final_url = f"{best['url']}&title={quote(title)}.{ext}"
        return redirect(final_url)

    except Exception as e:
        print("Download error:", e)
        return "Download failed – try again", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    print(f"FLUX_LEEH IS FULLY ALIVE on port {port} ZA")
    app.run(host='0.0.0.0', port=port)