from flask import Flask, request, jsonify, send_file, Response
import yt_dlp
import requests
from urllib.parse import quote
import os

app = Flask(__name__, static_folder='../public', static_url_path='')

# Serve the main page
@app.route('/')
def index():
    return app.send_static_file('index.html')

# ================= SEARCH =================
@app.route('/search')
def search():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify({"results": []})

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
        'skip_download': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(f"ytsearch50:{q}", download=False)
            entries = result.get('entries', []) if result else []
            results = []
            for e in entries:
                if e:
                    results.append({
                        'id': e['id'],
                        'title': e.get('title', 'No Title'),
                        'thumbnail': f"https://i.ytimg.com/vi/{e['id']}/hqdefault.jpg",
                        'duration': e.get('duration', 0) or 0,
                        'author': e.get('uploader', 'Unknown')
                    })
            return jsonify({"results": results[:50]})
    except:
        return jsonify({"results": []})

# ================= TRENDING (SOUTH AFRICA AMAPIANO) =================
@app.route('/trending')
def trending():
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
        'skip_download': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info("ytsearch50:amapiano 2025 south africa trending kabza de small dj maphorisa", download=False)
            entries = result.get('entries', []) if result else []
            results = []
            for e in entries:
                if e:
                    results.append({
                        'id': e['id'],
                        'title': e.get('title', 'No Title'),
                        'thumbnail': f"https://i.ytimg.com/vi/{e['id']}/hqdefault.jpg",
                        'duration': e.get('duration', 0) or 0,
                        'author': e.get('uploader', 'Unknown')
                    })
            return jsonify({"results": results[:50]})
    except:
        return jsonify({"results": []})

# ================= PREVIEW (first ~30 seconds) =================
@app.route('/preview')
def preview():
    vid = request.args.get('id')
    typ = request.args.get('type', 'audio')
    if not vid:
        return "No video ID", 400

    url = f"https://www.youtube.com/watch?v={vid}"
    format_selector = 'bestaudio' if typ == 'audio' else 'best[height<=480]'

    ydl_opts = {
        'format': format_selector,
        'quiet': True,
        'no_warnings': True,
    }

    def stream():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            direct_url = info['url']
            r = requests.get(direct_url, stream=True)
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    yield chunk

    mimetype = 'audio/mpeg' if typ == 'audio' else 'video/mp4'
    return Response(stream(), mimetype=mimetype)

# ================= DOWNLOAD (MP3 or MP4) =================
@app.route('/download')
def download():
    vid = request.args.get('id')
    fmt = request.args.get('format', 'mp3')
    if not vid:
        return "No video ID", 400

    url = f"https://www.youtube.com/watch?v={vid}"
    is_mp3 = fmt == 'mp3'

    ydl_opts = {
        'format': 'bestaudio' if is_mp3 else 'best',
        'quiet': True,
        'no_warnings': True,
    }

    def stream():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = f"{info.get('uploader', 'Artist')} - {info.get('title', 'Song')}.{fmt}"
            title = "".join(c for c in title if c.isalnum() or c in " -_.").rstrip()
            yield f"attachment; filename=\"{title}\"\n".encode()

            direct_url = info['url']
            r = requests.get(direct_url, stream=True)
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    yield chunk

    # Get proper filename for header
    with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
        info = ydl.extract_info(url, download=False)
        safe_name = f"{info.get('uploader', 'Artist')} - {info.get('title', 'Song')}.{fmt}"
        safe_name = "".join(c for c in safe_name if c.isalnum() or c in " -_.").rstrip()

    response = Response(stream(), mimetype='audio/mpeg' if is_mp3 else 'video/mp4')
    response.headers['Content-Disposition'] = f'attachment; filename="{safe_name}"'
    return response

# ================= START SERVER =================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    print(f"FLUX_LEEH IS FULLY ALIVE on port {port} 🇿🇦🔥")
    app.run(host='0.0.0.0', port=port, debug=False)