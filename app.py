from flask import Flask, request, redirect, send_from_directory, jsonify
import requests
import random
import os

app = Flask(__name__, static_folder='static', static_url_path='')

# Cloud-friendly Invidious servers (these work on Render) — kept as fallback for API calls
INVIDIOUS_INSTANCES = [
    "https://invidious.nerdvpn.de",
    "https://yt.drgnz.club",
    "https://invidious.tiekoetter.com",
    "https://invidious.fdn.fr",
    "https://inv.nadeko.net",
    "https://invidious.asir.dev",
    "https://iv.ggtyler.dev",
    "https://invidious.privacyredirect.com"
]


def pick_invidious():
    """Pick a working Invidious server – safe for Render deployment."""
    random.shuffle(INVIDIOUS_INSTANCES)
    for url in INVIDIOUS_INSTANCES:
        try:
            r = requests.get(url + "/api/v1/stats", timeout=4)
            if r.status_code == 200:
                return url
        except Exception:
            pass
    return INVIDIOUS_INSTANCES[0]  # fallback


@app.route("/")
def home():
    return send_from_directory("static", "index.html")


@app.route("/sw.js")
def service_worker():
    # Serve the service worker so browsers accept it
    return send_from_directory("static", "sw.js", mimetype="application/javascript")


@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory("static", filename)


@app.route("/search")
def search():
    instance = pick_invidious()
    q = request.args.get("q", "").strip()

    if not q:
        return jsonify({"results": []})

    try:
        r = requests.get(f"{instance}/api/v1/search", params={"q": q}, timeout=10)
        data = r.json()
        results = []

        for v in data[:40]:
            # Some Invidious instances return different shapes; guard defensively
            video_id = v.get("videoId") or v.get("id")
            if video_id:
                thumb = None
                if v.get("videoThumbnails"):
                    thumb = v["videoThumbnails"][-1].get("url")
                results.append({
                    "id": video_id,
                    "title": v.get("title") or v.get("videoTitle") or "Unknown",
                    "author": v.get("author") or v.get("uploader") or "Unknown",
                    "duration": int(v.get("lengthSeconds") or v.get("duration") or 0),
                    "thumbnail": thumb or "logo.jpg"
                })

        return jsonify({"results": results})
    except Exception:
        return jsonify({"results": []})


@app.route("/trending")
def trending():
    instance = pick_invidious()
    try:
        # request region-specific trending if the instance supports it
        r = requests.get(f"{instance}/api/v1/trending", timeout=10)
        data = r.json()
        results = []

        for v in data[:30]:
            video_id = v.get("videoId") or v.get("id")
            if video_id:
                thumb = None
                if v.get("videoThumbnails"):
                    thumb = v["videoThumbnails"][-1].get("url")
                results.append({
                    "id": video_id,
                    "title": v.get("title") or v.get("videoTitle") or "Unknown",
                    "author": v.get("author") or v.get("uploader") or "Unknown",
                    "duration": int(v.get("lengthSeconds") or v.get("duration") or 0),
                    "thumbnail": thumb or "logo.jpg"
                })

        return jsonify({"results": results})
    except Exception:
        return jsonify({"results": []})


@app.route("/preview")
def preview():
    # In many hosts invidious direct video proxying is blocked.
    # Redirect users to the official YouTube watch page instead
    vid = request.args.get("id")
    if not vid:
        return "Missing video ID", 400

    return redirect(f"https://www.youtube.com/watch?v={vid}")


@app.route("/download")
def download():
    vid = request.args.get("id")
    fmt = request.args.get("format", "mp3")

    if not vid:
        return "Missing video ID", 400

    instance = pick_invidious()

    try:
        info = requests.get(f"{instance}/api/v1/videos/{vid}", timeout=10)
        info = info.json()

        # Build safe filename
        title = "".join(c for c in f"{info.get('author','')} - {info.get('title','Video')}"
                        if c.isalnum() or c in " -_()[]").strip()[:150]

        # Select stream
        streams = info.get("formatStreams", [])
        if not streams:
            return "No streams available", 503

        if fmt == "mp3":
            audio = [s for s in streams if "audio" in s.get("type", "")]
            stream = max(audio, key=lambda x: int(x.get("bitrate", 0)), default=streams[0])
        else:
            video = [s for s in streams if "video" in s.get("type", "") or "video/mp4" in s.get("type", "")]
            def qkey(x):
                q = x.get("quality", "")
                if isinstance(q, str) and "p" in q:
                    try:
                        return int(q.split("p")[0])
                    except Exception:
                        return 0
                return 0
            stream = max(video, key=qkey, default=streams[0])

        # Redirect the client to the stream URL. Many browsers block cross-site downloads with filename headers.
        return redirect(stream.get('url'))

    except Exception:
        return "Error – Try again", 503


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
