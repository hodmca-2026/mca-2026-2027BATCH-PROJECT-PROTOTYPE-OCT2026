/* Detection History page: search saved records (no detection runs here). */

const q = $("#q"), results = $("#results"), info = $("#resultInfo");
let lastTerms = [];

function params() {
  const p = new URLSearchParams();
  if (q.value.trim()) p.set("q", q.value.trim());
  if ($("#fLabel").value) p.set("label", $("#fLabel").value);
  if ($("#fFrom").value) p.set("from", $("#fFrom").value);
  if ($("#fTo").value) p.set("to", $("#fTo").value);
  if (Number($("#fConf").value) > 0) p.set("min_conf", $("#fConf").value);
  p.set("sort", $("#fSort").value);
  return p;
}

async function loadLabels() {
  try {
    const d = await api("/api/labels");
    const sel = $("#fLabel"), cur = sel.value;
    sel.innerHTML = `<option value="">Any object</option>` +
      d.in_history.map(l => `<option value="${esc(l.label)}">${esc(l.label)} (${l.records})</option>`).join("");
    sel.value = d.in_history.some(l => l.label === cur) ? cur : "";
    $("#labelList").innerHTML = d.all.map(l => `<option value="${esc(l)}">`).join("");
    return d.stats;
  } catch (e) { toast(esc(e.message), true); return null; }
}

function card(r) {
  const counts = {};
  r.objects.forEach(o => { counts[o.label] = (counts[o.label] || 0) + 1; });
  const labels = Object.entries(counts).sort((a, b) => b[1] - a[1]).map(([l, n]) =>
    `<span class="chip ${lastTerms.includes(l) ? "" : "plain"}">${esc(l)}${n > 1 ? ` × ${n}` : ""}</span>`).join("");
  const best = Math.max(...r.objects.map(o => o.confidence));
  const match = r.matched_objects
    ? `${r.matched_objects} matching object${r.matched_objects > 1 ? "s" : ""}, average confidence ${pct(r.match_conf)}`
    : `${r.objects.length} object${r.objects.length > 1 ? "s" : ""}, best confidence ${pct(best)}`;
  return `<button class="rec" data-id="${r.id}">
      <img src="/media/saved/${r.id}?annotated=1" alt="Record ${r.id}" loading="lazy">
      <span class="info">
        <span class="top"><b>Record #${r.id}</b><span>${formatTime(r.created_at)}</span></span>
        <span class="labels">${labels}</span>
        <span class="match">${match}</span>${r.note ? `<span class="match">Note: ${esc(r.note)}</span>` : ""}
      </span></button>`;
}

async function search() {
  const p = params();
  history.replaceState(null, "", "/history" + (p.toString() ? "?" + p : ""));
  results.innerHTML = `<div class="skeleton"></div><div class="skeleton"></div><div class="skeleton"></div>`;
  info.textContent = "";
  const btn = $("#searchBtn");
  busy(btn, true, "Searching");
  try {
    const res = await api("/api/records?" + p);
    lastTerms = res.terms;
    const stats = await loadLabels();
    let line = "";
    if (res.terms.length) {
      line = `<b>${res.total}</b> saved record${res.total === 1 ? " contains" : "s contain"} ${res.terms.map(t => `<b>${esc(t)}</b>`).join(" or ")}. `;
      line += res.sort === "relevance"
        ? "Ranked by how many of your search words appear, then the number of matching objects, then their confidence. Newest first when tied."
        : res.sort === "newest" ? "Sorted newest first." : "Sorted oldest first.";
    } else if (!res.unknown.length) {
      line = `Showing <b>${res.total}</b> saved record${res.total === 1 ? "" : "s"}, ${res.sort === "oldest" ? "oldest" : "newest"} first.`;
    }
    if (res.unknown.length) {
      line += `<div class="suggest">${res.unknown.map(w => {
        const s = res.suggestions[w] || [];
        return `"${esc(w)}" is not an object the detector knows.` +
          (s.length ? ` Did you mean ${s.map(x => `<button type="button" data-s="${esc(x)}">${esc(x)}</button>`).join(" or ")}?` : "");
      }).join(" ")}</div>`;
    }
    info.innerHTML = line + `<span class="small"> (${res.search_ms} ms)</span>`;
    $$(".suggest button", info).forEach(b => b.addEventListener("click", () => {
      q.value = q.value.toLowerCase().replace(/[^a-z ]/g, " ").split(/\s+/).map(w => res.unknown.includes(w) ? b.dataset.s : w).join(" ").trim();
      search();
    }));
    if (!res.items.length) {
      results.innerHTML = stats && stats.records === 0
        ? `<div class="state"><b>No saved detections yet</b>Go to <a href="/">Live Detection</a>, capture or upload an image, and click Save result.</div>`
        : `<div class="state"><b>No saved record matches this search</b>Try another object name, or clear the filters. Only objects you saved earlier can be found here.</div>`;
      return;
    }
    results.innerHTML = res.items.map(card).join("");
    $$(".rec", results).forEach(c => c.addEventListener("click", () => openRecord(Number(c.dataset.id))));
  } catch (e) {
    results.innerHTML = `<div class="state error"><b>Search failed</b>${esc(e.message)}</div>`;
  } finally { busy(btn, false); }
}

/* ------------------------------------------------------------ detail */
async function openRecord(id) {
  const m = $("#detailModal");
  m.classList.remove("hidden");
  $("#detailTitle").textContent = `Record #${id}`;
  $("#detailBody").innerHTML = `<div class="skeleton"></div>`;
  try {
    const r = await api(`/api/records/${id}`);
    $("#detailBody").innerHTML = `
      <div class="detail">
        <div>
          <div class="seg"><button class="on" data-v="1">With boxes</button><button data-v="0">Original</button></div>
          <img id="detailImg" src="/media/saved/${r.id}?annotated=1" alt="Saved image for record ${r.id}">
        </div>
        <div>
          <dl class="facts">
            <dt>Record ID</dt><dd>#${r.id}</dd>
            <dt>Saved</dt><dd>${formatTime(r.created_at)}</dd>
            <dt>Source</dt><dd>${r.source === "camera" ? "Camera capture" : "Uploaded image"}</dd>
            <dt>Image size</dt><dd>${r.width} × ${r.height}</dd>
            ${r.note ? `<dt>Note</dt><dd>${esc(r.note)}</dd>` : ""}
            <dt>Objects</dt><dd>${r.objects.length}</dd>
          </dl>
          <table class="objs"><thead><tr><th>Object</th><th>Confidence</th></tr></thead>
            <tbody>${r.objects.map(o => `<tr class="${lastTerms.includes(o.label) ? "hit" : ""}"><td>${esc(o.label)}</td><td>${pct(o.confidence)}</td></tr>`).join("")}</tbody></table>
          <div class="modal-actions"><button class="btn danger" id="deleteOne">Delete record</button></div>
        </div>
      </div>`;
    $$(".seg button").forEach(b => b.addEventListener("click", () => {
      $$(".seg button").forEach(x => x.classList.toggle("on", x === b));
      $("#detailImg").src = `/media/saved/${r.id}${b.dataset.v === "1" ? "?annotated=1" : ""}`;
    }));
    $("#deleteOne").addEventListener("click", async () => {
      if (!await confirmBox(`Delete record #${r.id}?`, "The saved image and its objects will be removed. This cannot be undone.")) return;
      try { await api(`/api/records/${r.id}`, { method: "DELETE" }); closeDetail(); toast(`Record #${r.id} deleted.`); search(); }
      catch (e) { toast(esc(e.message), true); }
    });
  } catch (e) { $("#detailBody").innerHTML = `<div class="state error"><b>Could not open this record</b>${esc(e.message)}</div>`; }
}
function closeDetail() { $("#detailModal").classList.add("hidden"); }
$("#closeDetail").addEventListener("click", closeDetail);
$("#detailModal").addEventListener("click", e => { if (e.target.id === "detailModal") closeDetail(); });
document.addEventListener("keydown", e => { if (e.key === "Escape") closeDetail(); });

/* ------------------------------------------------------------ wiring */
$("#searchForm").addEventListener("submit", e => { e.preventDefault(); search(); });
q.addEventListener("search", () => { if (!q.value) search(); });     // the x in the search box
["fLabel", "fFrom", "fTo", "fSort"].forEach(id => $("#" + id).addEventListener("change", search));
$("#fConf").addEventListener("input", e => { $("#fConfVal").textContent = Number(e.target.value).toFixed(2); });
$("#fConf").addEventListener("change", search);
$("#resetBtn").addEventListener("click", () => {
  $("#fLabel").value = ""; $("#fFrom").value = ""; $("#fTo").value = ""; $("#fConf").value = 0; $("#fConfVal").textContent = "0.00"; $("#fSort").value = "relevance";
  search();
});
$("#clearAllBtn").addEventListener("click", async () => {
  if (!await confirmBox("Clear the whole history?", "Every saved record and image will be deleted. This cannot be undone.", "Clear history")) return;
  try { const r = await api("/api/records", { method: "DELETE", json: { confirm: true } }); toast(`Deleted ${r.deleted} record${r.deleted === 1 ? "" : "s"}.`); search(); }
  catch (e) { toast(esc(e.message), true); }
});

(function init() {
  const p = new URLSearchParams(location.search);
  q.value = p.get("q") || "";
  if (p.get("from")) $("#fFrom").value = p.get("from");
  if (p.get("to")) $("#fTo").value = p.get("to");
  if (p.get("sort")) $("#fSort").value = p.get("sort");
  loadLabels().then(() => { if (p.get("label")) $("#fLabel").value = p.get("label"); search(); });
})();
