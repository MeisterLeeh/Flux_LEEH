# app.py
from flask import Flask, request, jsonify, send_from_directory, send_file, redirect
import requests
import tempfile
import os
import shutil
import time
from yt_dlp import YoutubeDL

app = Flask(__name__, static_folder="static", static_url_path="")

# Piped API for search/trending (keeps that responsive)
PIPED_API = "https://pipedapi.kavin.rocks"

# yt-dlp options template (we will override per-format)
YTDL_OPTS_BASE = {
    "format": "bestaudio/best",
    "noprogress": True,
    "quiet": True,
    "no_warnings": True,
    # Prevent writing cache files into current dir
    "cachedir": False,
}

# -----------------------------------------------------
# HOME + STATIC
# -----------------------------------------------------
@app.route("/")
def home():
    return send_from_directory("static", "index.html")


@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory("static", filename)


# -----------------------------------------------------
# SEARCH (20 results)
# -----------------------------------------------------
@app.route("/search")
def search():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"results": []})

    try:
        r = requests.get(f"{PIPED_API}/search", params={"q": q}, timeout=12)
        r.raise_for_status()
        data = r.json()

        results = []
        for v in data[:20]:
            if v.get("type") != "stream":
                continue
            vid = v.get("url", "").replace("/watch?v=", "")
            results.append({
                "id": vid,
                "title": v.get("title", "Unknown"),
                "author": v.get("uploader", "Unknown"),
                "duration": v.get("duration", 0),
                "thumbnail": v.get("thumbnail") or "/logo.jpg",
            })
        return jsonify({"results": results})
    except Exception as e:
        print("SEARCH ERROR:", e)
        return jsonify({"results": []})


# -----------------------------------------------------
# TRENDING (top 10)
# -----------------------------------------------------
@app.route("/trending")
def trending():
    try:
        r = requests.get(f"{PIPED_API}/trending", timeout=12)
        r.raise_for_status()
        data = r.json()

        results = []
        for v in data[:10]:
            vid = v.get("url", "").replace("/watch?v=", "")
            results.append({
                "id": vid,
                "title": v.get("title", "Unknown"),
                "author": v.get("uploader", "Unknown"),
                "duration": v.get("duration", 0),
                "thumbnail": v.get("thumbnail") or "/logo.jpg",
            })
        return jsonify({"results": results})
    except Exception as e:
        print("TRENDING ERROR:", e)
        return jsonify({"results": []})


# -----------------------------------------------------
# PREVIEW - redirect to youtube watch page
# -----------------------------------------------------
@app.route("/preview")
def preview():
    vid = request.args.get("id")
    if not vid:
        return "missing id", 400
    return redirect(f"https://www.youtube.com/watch?v={vid}")


# -----------------------------------------------------
# Helper: run yt-dlp and return path to created file
# -----------------------------------------------------
def ytdl_download(video_url, outdir, filename, extra_opts=None):
    opts = YTDL_OPTS_BASE.copy()
    opts.update({
        "outtmpl": os.path.join(outdir, filename),
    })
    if extra_opts:
        opts.update(extra_opts)

    with YoutubeDL(opts) as ydl:
        ydl.download([video_url])
    # return the absolute path of the created file pattern (yt-dlp writes extension)
    # find matching file in outdir starting with filename (without extension)
    base = os.path.join(outdir, filename)
    for f in os.listdir(outdir):
        if f.startswith(os.path.basename(filename)):
            return os.path.join(outdir, f)
    return None


# -----------------------------------------------------
# DOWNLOAD - unified endpoint: /download?id=VID&format=mp3|mp4
# -----------------------------------------------------
@app.route("/download")
def download():
    vid = request.args.get("id", "")
    fmt = request.args.get("format", "mp3").lower()
    if not vid:
        return jsonify({"error": "missing video id"}), 400

    video_url = f"https://www.youtube.com/watch?v={vid}"

    # create temporary working dir for this request
    workdir = tempfile.mkdtemp(prefix="flux_")
    try:
        if fmt == "mp3":
            # export to mp3 via postprocessor
            filename = f"{vid}.%(ext)s"  # yt-dlp will replace ext with .mp3 after postprocessor
            ytdl_opts = {
                **YTDL_OPTS_BASE,
                "format": "bestaudio/best",
                "outtmpl": os.path.join(workdir, filename),
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
                # ensure ffmpeg is used if available
            }
            # Run download
            with YoutubeDL(ytdl_opts) as ydl:
                ydl.download([video_url])

            # find mp3 file in workdir
            files = [f for f in os.listdir(workdir) if f.endswith(".mp3")]
            if not files:
                return jsonify({"error": "failed to produce mp3"}), 503
            path = os.path.join(workdir, files[0])
            # send file, then cleanup
            return send_file(path, as_attachment=True, download_name=f"{files[0]}")
        else:
            # mp4: merge video+audio into mp4
            filename = f"{vid}.%(ext)s"
            ytdl_opts = {
                **YTDL_OPTS_BASE,
                "format": "bestvideo+bestaudio/best",
                "outtmpl": os.path.join(workdir, filename),
                "merge_output_format": "mp4"
            }
            with YoutubeDL(ytdl_opts) as ydl:
                ydl.download([video_url])

            files = [f for f in os.listdir(workdir) if f.endswith(".mp4")]
            if not files:
                return jsonify({"error": "failed to produce mp4"}), 503
            path = os.path.join(workdir, files[0])
            return send_file(path, as_attachment=True, download_name=f"{files[0]}")
    except Exception as e:
        print("DOWNLOAD ERROR:", e)
        return jsonify({"error": "download failed"}), 503
    finally:
        # schedule cleanup after short delay to ensure send_file has finished reading the file.
        # send_file will keep file open for WSGI worker until response finishes; to avoid deleting too early,
        # spawn a short waiter process via background thread/process or just rely on periodic cleanup.
        # Here we attempt a best-effort cleanup after small sleep in a child process.
        try:
            pid = os.fork()
            if pid == 0:
                # child
                time.sleep(10)
                try:
                    shutil.rmtree(workdir, ignore_errors=True)
                finally:
                    os._exit(0)
        except Exception:
            # if fork not available (Windows/Render), try to remove immediately (may fail)
            try:
                shutil.rmtree(workdir, ignore_errors=True)
            except Exception:
                pass


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
