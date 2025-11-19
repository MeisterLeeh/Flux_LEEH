from flask import Flask, request, redirect, send_from_directory, jsonify
import requests
import random
import os

app = Flask(__name__, static_folder='static', static_url_path='')

# Cloud-friendly Invidious servers (these work on Render)
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
        except:
            pass
    return INVIDIOUS_INSTANCES[0]  # fallback


@app.route("/")
def home():
    return send_from_directory("static", "index.html")


@app.route("/sw.js")
def service_worker():
    # Required so Render serves service workers correctly
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
            if v.get("videoId"):
                results.append({
                    "id": v["videoId"],
                    "title": v.get("title", "Unknown"),
                    "author": v.get("author", "Unknown"),
                    "duration": v.get("lengthSeconds", 0),
                    "thumbnail": v["videoThumbnails"][-1]["url"]
                })

        return jsonify({"results": results})
    except:
        return jsonify({"results": []})


@app.route("/trending")
def trending():
    instance = pick_invidious()
    try:
        r = requests.get(f"{instance}/api/v1/trending", timeout=10)
        data = r.json()
        results = []

        for v in data[:30]:
            if v.get("videoId"):
                results.append({
                    "id": v["videoId"],
                    "title": v.get("title", "Unknown"),
                    "author": v.get("author", "Unknown"),
                    "duration": v.get("lengthSeconds", 0),
                    "thumbnail": v["videoThumbnails"][-1]["url"]
                })

        return jsonify({"results": results})
    except:
        return jsonify({"results": []})


@app.route("/preview")
def preview():
    vid = request.args.get("id")
    if not vid:
        return "Missing video ID", 400

    instance = pick_invidious()
    return redirect(f"{instance}/latest_version?id={vid}&itag=18")


@app.route("/download")
def download():
    vid = request.args.get("id")
    fmt = request.args.get("format", "mp3")

    if not vid:
        return "Missing video ID", 400

    instance = pick_invidious()

    try:
        info = requests.get(f"{instance}/api/v1/videos/{vid}", timeout=10).json()
        title = "".join(c for c in f"{info.get('author','')} - {info.get('title','Video')}"
                        if c.isalnum() or c in " -_()[]").strip()[:150]

        if fmt == "mp3":
            audio = [s for s in info.get("formatStreams", []) if "audio" in s.get("type", "")]
            stream = max(audio, key=lambda x: x.get("bitrate", 0), default=info["formatStreams"][0])
        else:
            video = [s for s in info.get("formatStreams", []) if "video/mp4" in s.get("type", "")]
            stream = max(video, key=lambda x: int(x["quality"].split("p")[0]) if "p" in x["quality"] else 0,
                         default=info["formatStreams"][0])

        return redirect(f"{stream['url']}&title={title}.{fmt}")

    except:
        return "Error – Try again", 503


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
