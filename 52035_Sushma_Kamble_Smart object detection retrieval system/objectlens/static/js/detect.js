/* Live Detection page: camera, upload, YOLOv8 results, save. */

const video = $("#video"), still = $("#still"), overlay = $("#overlay");
const startBtn = $("#startBtn"), stopBtn = $("#stopBtn"), captureBtn = $("#captureBtn");
const saveBtn = $("#saveBtn"), liveToggle = $("#liveToggle"), backBtn = $("#backBtn");
const state = { stream: null, view: "empty", last: null, token: null, liveBusy: false, liveTimer: null, objectUrl: null };

/* ------------------------------------------------------------ drawing */
function drawBoxes(result) {
  const ctx = overlay.getContext("2d");
  const dpr = window.devicePixelRatio || 1;
  const cw = overlay.clientWidth, ch = overlay.clientHeight;
  overlay.width = cw * dpr; overlay.height = ch * dpr;
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, cw, ch);
  if (!result) return;
  // the media uses object-fit: contain, so work out where the picture sits
  const s = Math.min(cw / result.width, ch / result.height);
  const ox = (cw - result.width * s) / 2, oy = (ch - result.height * s) / 2;
  ctx.font = "600 13px Segoe UI, system-ui, sans-serif";
  ctx.lineWidth = 2;
  for (const d of result.detections) {
    const [x1, y1, x2, y2] = d.box;
    const x = ox + x1 * s, y = oy + y1 * s, w = (x2 - x1) * s, h = (y2 - y1) * s;
    const col = colorFor(d.label);
    ctx.strokeStyle = col;
    ctx.strokeRect(x, y, w, h);
    const text = `${d.label} ${pct(d.confidence)}`;
    const tw = ctx.measureText(text).width + 10;
    const ty = y > 20 ? y - 20 : y;
    ctx.fillStyle = col;
    ctx.fillRect(x - 1, ty, tw, 20);
    ctx.fillStyle = "#fff";
    ctx.fillText(text, x + 4, ty + 14);
  }
}
new ResizeObserver(() => drawBoxes(state.view === "empty" ? null : state.last)).observe(overlay);

function setView(view) {
  state.view = view;
  video.classList.toggle("hidden", view !== "video");
  still.classList.toggle("hidden", view !== "still");
  $("#stageEmpty").classList.toggle("hidden", view !== "empty");
  backBtn.classList.toggle("hidden", !(view === "still" && state.stream));
  const badge = $("#stageBadge");
  if (view === "still") { badge.textContent = state.lastSource === "camera" ? "Captured frame" : "Uploaded image"; badge.classList.remove("hidden"); }
  else if (view === "video" && liveToggle.checked) { badge.textContent = "Live"; badge.classList.remove("hidden"); }
  else badge.classList.add("hidden");
  if (view !== "still") drawBoxes(view === "video" && liveToggle.checked ? state.last : null);
}

/* ------------------------------------------------------------ results panel */
function renderResults(r, live = false) {
  const body = $("#detBody");
  $("#detMeta").textContent = `${r.inference_ms} ms${live ? ", live" : ""}`;
  if (!r.detections.length) {
    body.innerHTML = `<p class="empty">No objects found above confidence ${r.conf.toFixed(2)}. Try a closer shot, better light, or a lower threshold.</p>`;
    return;
  }
  const counts = Object.entries(r.counts).sort((a, b) => b[1] - a[1]);
  body.innerHTML = `
    <div class="summary">${counts.map(([l, n]) => `<span class="chip"><i style="background:${colorFor(l)}"></i>${esc(l)} × ${n}</span>`).join("")}</div>
    <div class="det-list">${r.detections.map(d => `
      <div class="det"><span>${esc(d.label)}</span><span class="bar"><i style="width:${(100 * d.confidence).toFixed(1)}%;background:${colorFor(d.label)}"></i></span><span>${pct(d.confidence)}</span></div>`).join("")}
    </div>`;
}

function setSaveState() {
  const ok = state.token && state.view === "still" && state.last && state.last.detections.length;
  saveBtn.disabled = !ok;
  $("#saveHint").textContent = ok ? "Saves the image, the object names and their confidence scores."
    : state.token && state.last && !state.last.detections.length ? "Nothing was detected, so there is nothing to save."
    : "Capture a frame or upload an image first. Live boxes are not saved.";
}

/* ------------------------------------------------------------ camera */
function camState(on) {
  $("#camState").classList.toggle("on", on);
  $("#camState").lastChild.textContent = on ? "Camera on" : "Camera off";
  startBtn.disabled = on; stopBtn.disabled = !on; captureBtn.disabled = !on; liveToggle.disabled = !on;
}

async function startCamera() {
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    toast("This browser cannot open the camera here. Use Chrome or Edge and open the app at http://127.0.0.1:5000.", true, 7000);
    return;
  }
  busy(startBtn, true, "Starting");
  try {
    state.stream = await navigator.mediaDevices.getUserMedia({ video: { width: { ideal: 1280 }, height: { ideal: 720 } }, audio: false });
    video.srcObject = state.stream;
    await video.play();
    busy(startBtn, false);
    camState(true);
    state.last = null;
    setView("video");
    if (liveToggle.checked) startLive();
  } catch (e) {
    busy(startBtn, false);
    camState(false);
    const msg = {
      NotAllowedError: "Camera permission was blocked. Click the camera icon in the address bar, allow access, then try again.",
      NotFoundError: "No camera was found. Connect a webcam, or use Upload image instead.",
      NotReadableError: "The camera is busy in another app (Zoom, Teams, Camera). Close it and try again.",
      OverconstrainedError: "The camera does not support the requested size.",
    }[e.name] || `Could not start the camera: ${e.message}`;
    toast(esc(msg), true, 7000);
  }
}

function stopCamera() {
  stopLive();
  if (state.stream) state.stream.getTracks().forEach(t => t.stop());
  state.stream = null;
  video.srcObject = null;
  camState(false);
  if (state.view === "video") { state.last = null; setView("empty"); }
  else setView(state.view);   // keep a captured or uploaded result on screen
}

function frameBlob(maxW) {
  const w = video.videoWidth, h = video.videoHeight;
  if (!w || !h) return Promise.resolve(null);
  const s = maxW && w > maxW ? maxW / w : 1;
  const c = document.createElement("canvas");
  c.width = Math.round(w * s); c.height = Math.round(h * s);
  c.getContext("2d").drawImage(video, 0, 0, c.width, c.height);
  return new Promise(res => c.toBlob(b => res(b), "image/jpeg", 0.9));
}

async function sendForDetection(blob, filename, source, live) {
  const fd = new FormData();
  fd.append("image", blob, filename);
  fd.append("source", source);
  fd.append("conf", $("#conf").value);
  if (live) fd.append("live", "1");
  return api("/api/detect", { method: "POST", body: fd });
}

async function captureAndDetect() {
  const blob = await frameBlob();
  if (!blob) { toast("The camera has not delivered a frame yet. Wait a second and try again.", true); return; }
  stopLive();
  busy(captureBtn, true, "Detecting");
  $("#stageBusy").classList.remove("hidden");
  try {
    const r = await sendForDetection(blob, "frame.jpg", "camera", false);
    showStill(URL.createObjectURL(blob), r, "camera");
  } catch (e) { toast(esc(e.message), true); }
  finally { busy(captureBtn, false); $("#stageBusy").classList.add("hidden"); if (!state.stream) captureBtn.disabled = true; }
}

function showStill(url, r, source) {
  if (state.objectUrl) URL.revokeObjectURL(state.objectUrl);
  state.objectUrl = url;
  state.last = r; state.token = r.token; state.lastSource = source;
  still.onload = () => drawBoxes(r);
  still.src = url;
  setView("still");
  renderResults(r);
  setSaveState();
}

/* ------------------------------------------------------------ live boxes */
async function liveStep() {
  if (!state.stream || !liveToggle.checked || state.view !== "video") return;
  if (!state.liveBusy) {
    state.liveBusy = true;
    try {
      const blob = await frameBlob(640);
      if (blob) {
        const r = await sendForDetection(blob, "live.jpg", "camera", true);
        if (state.view === "video" && liveToggle.checked) { state.last = r; drawBoxes(r); renderResults(r, true); }
      }
    } catch (e) { toast(esc(e.message), true); liveToggle.checked = false; stopLive(); }
    state.liveBusy = false;
  }
  state.liveTimer = setTimeout(liveStep, 250);
}
function startLive() { clearTimeout(state.liveTimer); setView(state.view); liveStep(); }
function stopLive() { clearTimeout(state.liveTimer); state.liveTimer = null; if (state.view === "video") drawBoxes(null); $("#stageBadge").classList.add("hidden"); }

/* ------------------------------------------------------------ upload */
$("#fileInput").addEventListener("change", async e => {
  const f = e.target.files[0];
  e.target.value = "";
  if (!f) return;
  if (!/\.(jpe?g|png|bmp|webp)$/i.test(f.name)) { toast("Use a JPG, PNG, BMP or WEBP image.", true); return; }
  if (f.size > 8 * 1024 * 1024) { toast("That image is larger than 8 MB.", true); return; }
  stopLive();
  $("#stageBusy").classList.remove("hidden");
  try {
    const r = await sendForDetection(f, f.name, "upload", false);
    showStill(URL.createObjectURL(f), r, "upload");
  } catch (err) { toast(esc(err.message), true); }
  finally { $("#stageBusy").classList.add("hidden"); }
});

/* ------------------------------------------------------------ save */
saveBtn.addEventListener("click", async () => {
  busy(saveBtn, true, "Saving");
  try {
    const { record } = await api("/api/records", { json: { token: state.token, note: $("#note").value } });
    const top = [...new Set(record.objects.map(o => o.label))].slice(0, 2).join(" ");
    toast(`Saved as record #${record.id}. <a href="/history?q=${encodeURIComponent(top)}">Find it in history</a>`, false, 6000);
    state.token = null;
    $("#note").value = "";
    busy(saveBtn, false);
    saveBtn.disabled = true;
    $("#saveHint").textContent = `Saved as record #${record.id}. Capture another frame to save more.`;
  } catch (e) { busy(saveBtn, false); toast(esc(e.message), true); setSaveState(); }
});

/* ------------------------------------------------------------ wiring */
startBtn.addEventListener("click", startCamera);
stopBtn.addEventListener("click", stopCamera);
captureBtn.addEventListener("click", captureAndDetect);
backBtn.addEventListener("click", () => { state.last = null; setView("video"); $("#detBody").innerHTML = `<p class="empty">Back to the camera. Capture a frame to detect objects.</p>`; $("#detMeta").textContent = ""; setSaveState(); if (liveToggle.checked) startLive(); });
liveToggle.addEventListener("change", () => {
  if (liveToggle.checked) { if (state.view === "still" && state.stream) { state.last = null; setView("video"); } startLive(); }
  else { stopLive(); setView(state.view); }
});
$("#conf").addEventListener("input", e => { $("#confVal").textContent = Number(e.target.value).toFixed(2); });
// always release the camera when leaving or closing the page
window.addEventListener("pagehide", () => { if (state.stream) state.stream.getTracks().forEach(t => t.stop()); });
window.addEventListener("beforeunload", () => { if (state.stream) state.stream.getTracks().forEach(t => t.stop()); });
setSaveState();
