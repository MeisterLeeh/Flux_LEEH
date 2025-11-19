from flask import Flask, request, jsonify, send_file
import requests
import tempfile
import os

app = Flask(__name__)

PIPED_API = "https://pipedapi.kavin.rocks"


# -----------------------------------------------------
# SEARCH (returns 20 results)
# -----------------------------------------------------
@app.route("/search")
def search():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"results": []})

    try:
        r = requests.get(
            f"{PIPED_API}/search",
            params={"q": q},
            timeout=10
        )
        data = r.json()

        results = []
        for v in data[:20]:  # LIMIT TO 20 RESULTS
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

    except Exception as e:
        print("SEARCH ERROR:", e)
        return jsonify({"results": []})


# -----------------------------------------------------
# TRENDING (TOP 10)
# -----------------------------------------------------
@app.route("/trending")
def trending():
    try:
        r = requests.get(f"{PIPED_API}/trending", timeout=10)
        data = r.json()

        results = []
        for v in data[:10]:  # LIMIT TO TOP 10
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

    except Exception as e:
        print("TRENDING ERROR:", e)
        return jsonify({"results": []})


# -----------------------------------------------------
# VIDEO INFO (preview page)
# -----------------------------------------------------
@app.route("/info")
def info():
    video_id = request.args.get("id", "")
    if not video_id:
        return jsonify({"error": "missing video id"})

    try:
        r = requests.get(f"{PIPED_API}/streams/{video_id}", timeout=10)
        data = r.json()
        return jsonify(data)

    except Exception as e:
        print("INFO ERROR:", e)
        return jsonify({"error": "failed to get info"})


# -----------------------------------------------------
# DOWNLOAD MP3
# -----------------------------------------------------
@app.route("/download/mp3")
def download_mp3():
    video_id = request.args.get("id", "")
    if not video_id:
        return jsonify({"error": "missing video id"})

    try:
        data = requests.get(f"{PIPED_API}/streams/{video_id}", timeout=10).json()

        # Find best audio stream
        audio = None
        for a in data.get("audioStreams", []):
            if "mp4" in a.get("mimeType", "") or "webm" in a.get("mimeType", ""):
                audio = a
                break

        if not audio:
            return jsonify({"error": "no audio stream found"})

        # Download audio to temp file
        temp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        content = requests.get(audio["url"], stream=True).content
        temp.write(content)
        temp.close()

        return send_file(temp.name, as_attachment=True, download_name="audio.mp3")

    except Exception as e:
        print("MP3 DOWNLOAD ERROR:", e)
        return jsonify({"error": "mp3 download failed"})


# -----------------------------------------------------
# DOWNLOAD MP4
# -----------------------------------------------------
@app.route("/download/mp4")
def download_mp4():
    video_id = request.args.get("id", "")
    if not video_id:
        return jsonify({"error": "missing video id"})

    try:
        data = requests.get(f"{PIPED_API}/streams/{video_id}", timeout=10).json()

        # Pick best quality (highest resolution)
        video = None
        streams = sorted(data.get("videoStreams", []), key=lambda x: x.get("quality", ""), reverse=True)

        if streams:
            video = streams[0]

        if not video:
            return jsonify({"error": "no video stream found"})

        # Download to temp file
        temp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        content = requests.get(video["url"], stream=True).content
        temp.write(content)
        temp.close()

        return send_file(temp.name, as_attachment=True, download_name="video.mp4")

    except Exception as e:
        print("MP4 DOWNLOAD ERROR:", e)
        return jsonify({"error": "mp4 download failed"})


if __name__ == "__main__":
    app.run(debug=True)
