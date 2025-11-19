from flask import Flask, request, jsonify, send_from_directory, send_file, redirect
import requests
import tempfile
import os

app = Flask(__name__, static_folder="static", static_url_path="")

PIPED_API = "https://pipedapi.kavin.rocks"


# -----------------------------------------------------
# HOME PAGE
# -----------------------------------------------------
@app.route("/")
def home():
    return send_from_directory("static", "index.html")


# -----------------------------------------------------
# STATIC FILES (style.css, scripts.js, images)
# -----------------------------------------------------
@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory("static", filename)


# -----------------------------------------------------
# SEARCH
# -----------------------------------------------------
@app.route("/search")
def search():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"results": []})

    try:
        r = requests.get(f"{PIPED_API}/search", params={"q": q}, timeout=10)
        data = r.json()

        results = []
        for v in data[:20]:
            if v.get("type") != "stream":
                continue

            vid = v.get("url", "").replace("/watch?v=", "")
            thumb = v.get("thumbnail")

            results.append({
                "id": vid,
                "title": v.get("title", "Unknown"),
                "author": v.get("uploader", "Unknown"),
                "duration": v.get("duration", 0),
                "thumbnail": thumb or "logo.jpg",
            })

        return jsonify({"results": results})

    except:
        return jsonify({"results": []})


# -----------------------------------------------------
# TRENDING
# -----------------------------------------------------
@app.route("/trending")
def trending():
    try:
        r = requests.get(f"{PIPED_API}/trending", timeout=10)
        data = r.json()

        results = []
        for v in data[:10]:
            vid = v.get("url", "").replace("/watch?v=", "")
            thumb = v.get("thumbnail")

            results.append({
                "id": vid,
                "title": v.get("title", "Unknown"),
                "author": v.get("uploader", "Unknown"),
                "duration": v.get("duration", 0),
                "thumbnail": thumb or "logo.jpg",
            })

        return jsonify({"results": results})

    except:
        return jsonify({"results": []})


# -----------------------------------------------------
# PREVIEW (Open YouTube or Piped)
# -----------------------------------------------------
@app.route("/preview")
def preview():
    video_id = request.args.get("id")
    if not video_id:
        return "missing id", 400
    return redirect(f"https://www.youtube.com/watch?v={video_id}")


# -----------------------------------------------------
# DOWNLOAD MP3
# -----------------------------------------------------
@app.route("/download/mp3")
def download_mp3():
    vid = request.args.get("id", "")
    if not vid:
        return jsonify({"error": "missing video id"})

    try:
        data = requests.get(f"{PIPED_API}/streams/{vid}", timeout=10).json()

        audio = None
        for a in data.get("audioStreams", []):
            if "mp4" in a.get("mimeType", "") or "webm" in a.get("mimeType", ""):
                audio = a
                break

        if not audio:
            return jsonify({"error": "no audio stream found"})

        temp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        content = requests.get(audio["url"], stream=True).content
        temp.write(content)
        temp.close()

        return send_file(temp.name, as_attachment=True, download_name="audio.mp3")

    except:
        return jsonify({"error": "mp3 failed"})


# -----------------------------------------------------
# DOWNLOAD MP4
# -----------------------------------------------------
@app.route("/download/mp4")
def download_mp4():
    vid = request.args.get("id", "")
    if not vid:
        return jsonify({"error": "missing video id"})

    try:
        data = requests.get(f"{PIPED_API}/streams/{vid}", timeout=10).json()

        streams = sorted(
            data.get("videoStreams", []),
            key=lambda x: x.get("quality", ""),
            reverse=True
        )

        if not streams:
            return jsonify({"error": "no video stream"})

        best = streams[0]

        temp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        content = requests.get(best["url"], stream=True).content
        temp.write(content)
        temp.close()

        return send_file(temp.name, as_attachment=True, download_name="video.mp4")

    except:
        return jsonify({"error": "mp4 failed"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
