# ObjectLens
### Smart Object Detection and Retrieval System

A Flask web app that detects objects with your existing YOLOv8 model, using the webcam or an uploaded image. You can save the results you want to keep, and later search those saved results by object name.

| Part | What it does | Where |
|---|---|---|
| **Deep Learning** | Finds objects in a **new** image with YOLOv8 | `detector.py` (same model and calls as `detect.py`) |
| **Information Retrieval** | Searches **records you already saved**; never runs the model | `history.py` (SQLite + keyword search + ranking) |

---

## 1. What changed from the original project

| File | Status |
|---|---|
| `detect.py` | **Unchanged.** Still runs from the command line: `python detect.py --webcam` (press `q` to stop) or `--image photo.jpg`. |
| `yolov8n.pt` | **Unchanged.** The same weights are used by `detect.py` and the web app. |
| `other_models/cnn_digits.py`, `autoencoder.py`, `rnn_lstm.py` | **Unchanged**, moved into a folder. Not part of this app. Run them from the project root if needed. |
| `requirements.txt` | Updated: added `flask`. The original was missing `torch` and `torchvision`. |
| `detector.py` | **New.** Wraps the same `YOLO("yolov8n.pt")` call from `detect.py`, and returns the boxes as data instead of printing them. |
| `history.py`, `app.py`, `templates/`, `static/` | **New.** Detection history, search, and the web interface. |

Why the camera moved to the browser: `detect.py` opens the webcam with OpenCV in a desktop window. A web page cannot show that window. So the browser opens the camera, sends a frame to Flask, and Flask runs the same YOLO model on it.

---

## 2. Folder structure

```
objectlens/
├── app.py               Flask app: pages + JSON API
├── detector.py          YOLOv8 detection (Deep Learning)
├── history.py           SQLite storage, keyword search, ranking (Information Retrieval)
├── detect.py            your original script, unchanged
├── yolov8n.pt           YOLOv8 nano weights
├── requirements.txt
├── run.bat              double-click launcher for Windows
├── templates/           base.html, detect.html, history.html
├── static/css/style.css
├── static/js/           common.js, detect.js, history.js
├── sample_images/       bus.jpg, zidane.jpg (Ultralytics sample images, for testing)
├── other_models/        cnn_digits.py, autoencoder.py, rnn_lstm.py (unchanged)
├── docs/screenshots/    screenshots taken while testing
└── data/                created on first run
    ├── history.db       SQLite database
    ├── saved/           images of saved records (original + with boxes)
    └── temp/            unsaved detections, deleted automatically after 1 hour
```

---

## 3. Run it on Windows

### Option A: double-click `run.bat`
1. Install **Python 3.10, 3.11 or 3.12** from python.org and tick **Add Python to PATH**.
2. Double-click `run.bat`. The first run installs packages, which takes 5–10 minutes and needs internet. Then it opens http://127.0.0.1:5000.
3. Keep the black window open while you use the app, and close it to stop.

### Option B: VS Code
1. **File → Open Folder** → `objectlens`, then **Terminal → New Terminal**.
2. Create and activate a virtual environment:
   ```powershell
   python -m venv venv
   venv\Scripts\activate
   ```
   If PowerShell refuses, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once.
3. Install the packages:
   ```powershell
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
   pip install -r requirements.txt
   ```
4. **Ctrl+Shift+P → Python: Select Interpreter** → pick the one in `venv`.
5. Start the app with `python app.py`, then open **http://127.0.0.1:5000** in Chrome or Edge.
6. Press **Ctrl+C** in the terminal to stop the server.

The browser allows the camera on `http://127.0.0.1` and `http://localhost` only. If you open the app from another device by IP address, the camera will be blocked, but Upload image still works.

---

## 4. How to use it

**Live Detection page**
- **Start camera**: the browser asks for permission once.
- **Live boxes on the video** (optional): sends a small frame about 3–4 times a second and draws the boxes over the video. Live frames are never saved.
- **Capture and detect**: freezes the current frame and runs YOLOv8 on it at full size. The results list shows each object with its confidence.
- **Upload image**: does the same for a JPG, PNG, BMP or WEBP file (up to 8 MB).
- **Save result**: stores the captured or uploaded image, the object names, the confidences and the time. You can add a short note.
- **Back to camera** returns to the live video. **Stop camera** releases the webcam.
- **Confidence threshold**: hides objects the model is unsure about.
- The camera is also released when you leave or close the page.

**Detection History page**
- Search by object name, for example `person`, `bottle`, `chair`, `cell phone` or `person bottle`.
- Plurals and common words work too: `people`, `bottles`, `phone`, `sofa`, `table`.
- Unknown words get a "Did you mean …?" suggestion.
- **Filters**: object type, date from/to, minimum confidence. **Sort**: best match, newest first, oldest first.
- An empty search shows every saved record, newest first.
- Click a card to see the image (with or without boxes), the time, the source, the note and every object.
- **Delete record** removes one record. **Clear history** removes everything. Both ask first.

---

## 5. How the search works

1. **Saving.** Each saved detection becomes one row in `records` (time, image files, source, note) plus one row per object in `objects` (label, confidence, box).
2. **Index.** `objects.label` has a database index. Looking up "which records contain a bottle" uses that index instead of reading every record. This label → records lookup is the inverted index of this app.
3. **Query.** The text is cleaned up and turned into YOLO class names: `People and bottles` becomes `person`, `bottle`. Multi-word names like `cell phone` are recognised.
4. **Matching.** A record matches if it contains at least one searched object (above the minimum confidence) and passes the filters.
5. **Ranking:**
   1. records containing **more of the searched objects** come first (both `person` and `bottle` beats only one);
   2. then records with **more matching objects** (3 people beats 1);
   3. then a **higher average confidence** of those objects;
   4. ties go to the **newest** record.
6. **Display.** Matching labels are highlighted on each card, and the page states how many records matched and how they were ranked.

Nothing is detected during a search. Searching only reads the database, which is why it takes about 1–5 ms.

**What this is not:** there is no PageRank, web crawling, recommendation, or learned ranking model. It is keyword retrieval with a simple, explainable ranking.

---

## 6. API (used by the pages)

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/detect` | Multipart `image` (+ `conf`, `source`, `live=1`). Returns detections; non-live results get a `token` for saving |
| POST | `/api/records` | `{"token": "...", "note": "..."}`: saves that detection |
| GET | `/api/records?q=&label=&from=&to=&min_conf=&sort=` | Searches saved records |
| GET | `/api/records/<id>` | One record with all its objects |
| DELETE | `/api/records/<id>` | Deletes one record and its images |
| DELETE | `/api/records` | `{"confirm": true}`: clears all history |
| GET | `/api/labels` | Object types in the history, all 80 model classes, record count |
| GET | `/media/saved/<id>[?annotated=1]` | Saved image, looked up by record ID only |

Example search response (from a test run, trimmed):
```json
{ "terms": ["person"], "unknown": [], "total": 2, "sort": "relevance",
  "items": [ { "id": 3, "created_at": "2026-10-13 15:07:35", "source": "upload", "note": null,
               "matched_terms": 1, "matched_objects": 4, "match_conf": 0.7012,
               "objects": [ {"label": "bus", "confidence": 0.8734}, {"label": "person", "confidence": 0.8657}, "..." ] } ] }
```

---

## 7. Demonstration (about 5 minutes)

1. Run `run.bat` (or `python app.py`) and open http://127.0.0.1:5000.
2. Click **Start camera** and allow access.
3. Point it at everyday objects (a bottle, a cup, a phone, yourself). Tick **Live boxes** to show real-time detection.
4. Click **Capture and detect**. Show the labels and confidence scores. Type a note such as "desk", then **Save result**.
5. Click **Back to camera**, point it at a different scene (a chair or a laptop), capture and save again.
6. Open **Detection History**. Search `person` or `bottle`.
7. Show the matching images and timestamps. Explain the ranking line above the results.
8. Change **Sort** to Newest first, filter by an object type or today's date, and open a record.
9. Go back to Live Detection and click **Stop camera**.

**What to say:** "YOLOv8 is the deep-learning part: it looks at a new image and finds objects. The history page is the information-retrieval part: it never runs the model. It searches what we already saved, using an index on object labels, and ranks records by how well they match."

If the classroom PC has no webcam, use **Upload image** with `sample_images/bus.jpg` and `sample_images/zidane.jpg`.

---

## 8. Troubleshooting

| Problem | Fix |
|---|---|
| "Camera permission was blocked" | Click the camera icon in the address bar → Allow, then Start camera again. In Windows Settings → Privacy → Camera, allow desktop apps and browsers. |
| "No camera was found" | Plug in a webcam, or use Upload image. |
| "The camera is busy" | Close Zoom, Teams, the Camera app, or `detect.py --webcam`. Only one app can use it at a time. |
| Camera button does nothing on another device | Browsers block cameras on plain `http://` except `localhost`. Use the PC running the app. |
| `python` not recognised | Reinstall Python with **Add Python to PATH**, or use `py`. |
| `No matching distribution found for torch` | Use 64-bit Python 3.10–3.12. |
| First detection is slow | The model loads and warms up at start-up. Wait for "Running at" in the terminal. |
| Live boxes lag | Normal on a slow CPU. Turn Live boxes off and use Capture and detect. |
| Nothing detected | Better light, a closer shot, or a lower confidence threshold. YOLOv8n knows 80 COCO classes (person, bottle, cup, chair, laptop, cell phone, book, …). |
| "Nothing was detected… nothing to save" | Records without objects cannot be found by an object search, so they are not saved. |
| "This detection has expired" | Unsaved captures are kept for 1 hour. Capture again, then save. |
| Port 5000 in use | Close the other app, or change `port=5000` at the end of `app.py`. |
| Start fresh | Stop the app and delete the `data` folder. |
