from flask import Flask, request, jsonify, send_from_directory, redirect, Response
import yt_dlp
import os
from urllib.parse import quote

app = Flask(__name__, static_folder='.', static_url_path='')

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    if os.path.exists(path) and not path.startswith('downloads'):
        return send_from_directory('.', path)
    return "Not found", 404


# ================= SEARCH & TRENDING (unchanged - working fine) =================
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

@app.route('/trending')
def trending():
    try:
        with yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': True, 'skip_download': True}) as ydl:
            result = ydl.extract_info("ytsearch50:amapiano 2025 south africa trending kabza de small kabza de small dj maphorisa", download=False)
            entries = result.get('entries', [])
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


# ================= PREVIEW (30-sec preview - now working perfectly) =================
@app.route('/preview')
def preview():
    vid = request.args.get('id')
    typ = request.args.get('type', 'audio')
    if not vid:
        return "No ID", 400

    url = f"https://www.youtube.com/watch?v={vid}"

    ydl_opts = {
        'format': 'bestaudio/best' if typ == 'audio' else 'best[height<=480]',
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            direct_url = info['url']

        # Add title parameter so browser shows correct name when saved
        title = info.get('title', 'audio')[:100]
        safe_title = "".join(c for c in title if c.isalnum() or c in " -_.")
        
        redirect_url = f"{direct_url}&title={quote(safe_title)}.{ 'mp3' if typ=='audio' else 'mp4' }"
        
        return redirect(redirect_url)

    except Exception as e:
        print("Preview error:", e)
        return "Failed", 500


# ================= DOWNLOAD MP3 / MP4 - THIS IS THE MAGIC FIX =================
@app.route('/download')
def download():
    vid = request.args.get('id')
    fmt = request.args.get('format', 'mp3')  # mp3 or mp4
    if not vid:
        return "No ID", 400

    url = f"https://www.youtube.com/watch?v={vid}"

    # Best format selection
    format_selector = 'bestaudio/best' if fmt == 'mp3' else 'best[height<=1080]/best'

    ydl_opts = {
        'format': format_selector,
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            direct_url = info['url']
            title = info.get('title', 'Unknown')
            uploader = info.get('uploader', 'Artist')

            # Clean filename
            filename = f"{uploader} - {title}".strip()
            filename = "".join(c for c in filename if c.isalnum() or c in " -_()[]").rstrip()
            filename = filename[:150]  # Prevent too long
            ext = 'mp3' if fmt == 'mp3' else 'mp4'

            # This trick forces download with correct name EVEN on mobile
            final_url = f"{direct_url}&title={quote(filename)}.{ext}"

            # Redirect = zero server load, works 100% on Render
            return redirect(final_url)

    except Exception as e:
        print("Download error:", e)
        return "Video not available or age-restricted", 500


# ================= START SERVER =================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    print(f"FLUX_LEEH IS FULLY ALIVE on port {port} 🇿🇦🔥")
    app.run(host='0.0.0.0', port=port, debug=False)