"""ObjectLens: Smart Object Detection and Retrieval System (Flask backend).

Pages
  /          Live Detection    camera or upload -> YOLOv8 -> boxes -> save
  /history   Detection History search saved records by object name

Deep Learning = detector.py (runs YOLOv8 on a new image).
Information Retrieval = history.py (searches records that were already saved;
it never runs the model).
"""
import json
import os
import re
import time
import uuid

import cv2
import numpy as np
from flask import Flask, abort, jsonify, render_template, request, send_from_directory

import history
from detector import Detector

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024        # 8 MB per image
app.json.sort_keys = False

TEMP_DIR = os.path.join("data", "temp")       # unsaved detections, auto-deleted after 1 hour
SAVED_DIR = os.path.join("data", "saved")     # images of saved records
ALLOWED_EXT = {"jpg", "jpeg", "png", "bmp", "webp"}
TOKEN_RE = re.compile(r"^[0-9a-f]{32}$")
MAX_SIDE = 1280

for d in (TEMP_DIR, SAVED_DIR):
    os.makedirs(d, exist_ok=True)
history.init_db()
print("Loading YOLOv8 model...")
DETECTOR = Detector()
CLASS_NAMES = list(DETECTOR.names.values())


class ApiError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.message, self.status = message, status


@app.errorhandler(ApiError)
def _api_error(e):
    return jsonify({"error": e.message}), e.status


@app.errorhandler(413)
def _too_large(e):
    return jsonify({"error": "That image is larger than 8 MB."}), 413


@app.errorhandler(404)
def _not_found(e):
    if request.path.startswith(("/api/", "/media/")):
        return jsonify({"error": "Not found."}), 404
    return e


@app.errorhandler(500)
def _server_error(e):
    return jsonify({"error": "Something went wrong on the server. Check the terminal."}), 500


def _cleanup_temp(max_age_s=3600):
    now = time.time()
    for f in os.listdir(TEMP_DIR):
        p = os.path.join(TEMP_DIR, f)
        if now - os.path.getmtime(p) > max_age_s:
            os.remove(p)


def _read_image():
    f = request.files.get("image")
    if f is None or not f.filename:
        raise ApiError("No image received.")
    ext = f.filename.rsplit(".", 1)[-1].lower() if "." in f.filename else ""
    if ext not in ALLOWED_EXT:
        raise ApiError("Unsupported file type. Use JPG, PNG, BMP or WEBP.")
    img = cv2.imdecode(np.frombuffer(f.read(), np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise ApiError("Could not read that image.")
    h, w = img.shape[:2]
    if max(h, w) > MAX_SIDE:
        s = MAX_SIDE / max(h, w)
        img = cv2.resize(img, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
    return img


# ------------------------------------------------------------------ pages
@app.route("/")
def page_detect():
    return render_template("detect.html", active="detect")


@app.route("/history")
def page_history():
    return render_template("history.html", active="history")


@app.route("/media/temp/<token>")
def media_temp(token):
    if not TOKEN_RE.match(token):
        abort(404)
    kind = "_annotated" if request.args.get("annotated") else ""
    name = f"{token}{kind}.jpg"
    if not os.path.exists(os.path.join(TEMP_DIR, name)):
        abort(404)
    return send_from_directory(os.path.abspath(TEMP_DIR), name)


@app.route("/media/saved/<int:rid>")
def media_saved(rid):
    rec = history.get_record(rid)
    if rec is None:
        abort(404)
    name = rec["annotated_file"] if request.args.get("annotated") else rec["image_file"]
    if not os.path.exists(os.path.join(SAVED_DIR, name)):
        abort(404)
    return send_from_directory(os.path.abspath(SAVED_DIR), name, max_age=3600)


# ------------------------------------------------------------------ detection (Deep Learning)
@app.route("/api/detect", methods=["POST"])
def api_detect():
    img = _read_image()
    try:
        conf = min(0.9, max(0.05, float(request.form.get("conf", 0.25))))
    except ValueError:
        conf = 0.25
    live = request.form.get("live") == "1"
    source = request.form.get("source", "upload")
    source = source if source in ("camera", "upload") else "upload"
    t0 = time.perf_counter()
    detections, annotated = DETECTOR.detect(img, conf)
    ms = round(1000 * (time.perf_counter() - t0), 1)
    h, w = img.shape[:2]
    out = {"detections": detections, "width": w, "height": h, "inference_ms": ms, "conf": conf}
    counts = {}
    for d in detections:
        counts[d["label"]] = counts.get(d["label"], 0) + 1
    out["counts"] = counts
    if not live:
        # keep this frame for up to an hour so the user can choose to save it
        _cleanup_temp()
        token = uuid.uuid4().hex
        cv2.imwrite(os.path.join(TEMP_DIR, f"{token}.jpg"), img, [cv2.IMWRITE_JPEG_QUALITY, 90])
        cv2.imwrite(os.path.join(TEMP_DIR, f"{token}_annotated.jpg"), annotated, [cv2.IMWRITE_JPEG_QUALITY, 90])
        with open(os.path.join(TEMP_DIR, f"{token}.json"), "w") as fh:
            json.dump({"source": source, "detections": detections, "width": w, "height": h}, fh)
        out["token"] = token
    return jsonify(out)


# ------------------------------------------------------------------ history (Information Retrieval)
@app.route("/api/records", methods=["POST"])
def api_save():
    p = request.get_json(silent=True) or {}
    token = str(p.get("token", ""))
    if not TOKEN_RE.match(token):
        raise ApiError("Run a detection first, then save it.")
    meta_path = os.path.join(TEMP_DIR, f"{token}.json")
    if not os.path.exists(meta_path):
        raise ApiError("This detection has expired. Capture it again, then save.", 410)
    with open(meta_path) as fh:
        meta = json.load(fh)
    if not meta["detections"]:
        raise ApiError("Nothing was detected in this image, so there is nothing to search for later.", 422)
    note = str(p.get("note", "")).strip()[:120] or None
    image_file, annotated_file = f"{token}.jpg", f"{token}_annotated.jpg"
    os.replace(os.path.join(TEMP_DIR, image_file), os.path.join(SAVED_DIR, image_file))
    os.replace(os.path.join(TEMP_DIR, annotated_file), os.path.join(SAVED_DIR, annotated_file))
    os.remove(meta_path)
    rid = history.save_record(meta["source"], image_file, annotated_file, meta["width"], meta["height"],
                              meta["detections"], note)
    return jsonify({"record": history.get_record(rid)}), 201


@app.route("/api/records", methods=["GET"])
def api_search():
    a = request.args
    q = a.get("q", "")[:100]
    label = a.get("label") or None
    if label and label not in CLASS_NAMES:
        raise ApiError("Unknown object type.")
    date_re = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    date_from = a.get("from") or None
    date_to = a.get("to") or None
    for d in (date_from, date_to):
        if d and not date_re.match(d):
            raise ApiError("Dates must look like 2026-10-13.")
    try:
        min_conf = min(1.0, max(0.0, float(a.get("min_conf", 0))))
    except ValueError:
        min_conf = 0.0
    sort = a.get("sort", "relevance")
    sort = sort if sort in ("relevance", "newest", "oldest") else "relevance"
    t0 = time.perf_counter()
    res = history.search(q, label, date_from, date_to, min_conf, sort, class_names=CLASS_NAMES)
    res["search_ms"] = round(1000 * (time.perf_counter() - t0), 2)
    res["sort"] = sort if res["terms"] else ("oldest" if sort == "oldest" else "newest")
    return jsonify(res)


@app.route("/api/records", methods=["DELETE"])
def api_clear():
    p = request.get_json(silent=True) or {}
    if p.get("confirm") is not True:
        raise ApiError("Send {\"confirm\": true} to clear the history.")
    files = history.clear_all()
    for f in files:
        for name in f.values():
            path = os.path.join(SAVED_DIR, name)
            if os.path.exists(path):
                os.remove(path)
    return jsonify({"deleted": len(files)})


@app.route("/api/records/<int:rid>", methods=["GET"])
def api_record(rid):
    rec = history.get_record(rid)
    if rec is None:
        raise ApiError("Record not found.", 404)
    return jsonify(rec)


@app.route("/api/records/<int:rid>", methods=["DELETE"])
def api_delete(rid):
    files = history.delete_record(rid)
    if files is None:
        raise ApiError("Record not found.", 404)
    for name in files.values():
        path = os.path.join(SAVED_DIR, name)
        if os.path.exists(path):
            os.remove(path)
    return jsonify({"deleted": rid})


@app.route("/api/labels")
def api_labels():
    return jsonify({"in_history": history.label_counts(), "all": sorted(CLASS_NAMES), "stats": history.stats()})


if __name__ == "__main__":
    print("\n  ObjectLens running at  http://127.0.0.1:5000\n")
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
