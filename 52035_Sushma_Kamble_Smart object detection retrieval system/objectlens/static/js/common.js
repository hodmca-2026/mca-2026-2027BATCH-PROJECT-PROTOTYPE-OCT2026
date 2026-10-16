/* Shared helpers for both pages. */

async function api(path, options = {}) {
  const opts = Object.assign({}, options);
  if (opts.json !== undefined) {
    opts.headers = Object.assign({ "Content-Type": "application/json" }, opts.headers || {});
    opts.body = JSON.stringify(opts.json);
    opts.method = opts.method || "POST";
    delete opts.json;
  }
  let res;
  try { res = await fetch(path, opts); }
  catch (e) { throw new Error("Cannot reach the server. Is  python app.py  still running?"); }
  let data = null;
  try { data = await res.json(); } catch (e) { /* not JSON */ }
  if (!res.ok) throw new Error((data && data.error) || `Request failed (${res.status}).`);
  return data;
}

const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
const esc = v => String(v ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const pct = v => (100 * v).toFixed(0) + "%";

let toastTimer;
function toast(html, isError = false, ms = 4000) {
  const t = $("#toast");
  t.innerHTML = html;
  t.classList.toggle("error", isError);
  t.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.remove("show"), ms);
}

function busy(btn, on, label) {
  if (on) {
    if (!btn.dataset.busy) btn.dataset.html = btn.innerHTML;    // keep the original label only once
    btn.dataset.busy = "1";
    btn.innerHTML = `<span class="spin"></span>${esc(label)}`;
    btn.disabled = true;
  } else {
    if (btn.dataset.busy) btn.innerHTML = btn.dataset.html;
    delete btn.dataset.busy;
    btn.disabled = false;
  }
}

/* one colour per object class, stable between frames */
const PALETTE = ["#2563A6", "#D9822B", "#1F9D6B", "#C2417A", "#6B4FC4", "#B8901A", "#2A8FB0", "#B3383A"];
function colorFor(label) {
  let h = 0;
  for (const c of label) h = (h * 31 + c.charCodeAt(0)) >>> 0;
  return PALETTE[h % PALETTE.length];
}

/* in-page confirmation instead of window.confirm */
function confirmBox(title, text, okLabel = "Delete") {
  return new Promise(resolve => {
    const m = $("#confirmModal");
    $("#confirmTitle").textContent = title;
    $("#confirmText").textContent = text;
    $("#confirmOk").textContent = okLabel;
    m.classList.remove("hidden");
    $("#confirmOk").focus();
    const done = v => { m.classList.add("hidden"); ok.removeEventListener("click", yes); cancel.removeEventListener("click", no); resolve(v); };
    const ok = $("#confirmOk"), cancel = $("#confirmCancel");
    const yes = () => done(true), no = () => done(false);
    ok.addEventListener("click", yes);
    cancel.addEventListener("click", no);
  });
}

function formatTime(s) {
  // 'YYYY-MM-DD HH:MM:SS' (local time saved by the server) -> '13 Oct 2026, 20:41'
  const [d, t] = s.split(" ");
  const [y, m, day] = d.split("-").map(Number);
  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  return `${day} ${months[m - 1]} ${y}, ${t.slice(0, 5)}`;
}
