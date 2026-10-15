'use strict';
const $ = id => document.getElementById(id);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let user = null, projects = [];

async function api(url, body, method) {
  const opt = body === undefined ? {} : {method: method || 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)};
  let r; try { r = await fetch(url, opt); } catch { throw Error('Network error. Is the server running?'); }
  if (r.status === 401) { location.href = '/'; throw Error('Please log in.'); }
  let d = {}; try { d = await r.json(); } catch {}
  if (!r.ok) throw Error(d.error || 'Request failed (' + r.status + ')');
  return d;
}
// Run an action: loading spinner, error box.
async function run(outId, btnId, fn) {
  const out = $(outId), btn = btnId && $(btnId);
  out.innerHTML = '<span class="spin"></span>Working…'; if (btn) btn.disabled = true;
  try { out.innerHTML = await fn() || ''; } catch (e) { out.innerHTML = '<div class="err">' + esc(e.message) + '</div>'; }
  if (btn) btn.disabled = false;
}
const empty = m => '<div class="empty">' + esc(m) + '</div>';
const table = (heads, rows) => rows.length ? '<div class="table-responsive"><table><thead><tr>' + heads.map(h => '<th>' + h + '</th>').join('') +
  '</tr></thead><tbody>' + rows.map(r => '<tr>' + r.map(c => '<td>' + c + '</td>').join('') + '</tr>').join('') + '</tbody></table></div>' : '';
const need = (id, label) => { const v = $(id).value.trim(); if (!v) throw Error(label + ' is required.'); return v; };
const chips = a => a.map(x => '<span class="chip">' + esc(x) + '</span>').join('') || '<span class="muted">none</span>';

const rankTable = (res, extra) => res && res.length ? table(['Rank', 'Title', 'Score'], res.map(r => [r.position, esc(r.title || r.passage), r.score])) : empty('No matching results.');
const NAMES = {tfidf: 'TF-IDF + cosine similarity (higher is better)'};

const tabs = [['search','Search & Ranking'],['passage','Passage Retrieval'],['rec','Content-Based Recommendation'],['pr','PageRank']];
function show(id) {
  document.querySelectorAll('.panel').forEach(p => p.classList.toggle('active', p.id === 'p-' + id));
  document.querySelectorAll('#side button').forEach(b => b.classList.toggle('active', b.dataset.t === id));
  history.replaceState(null, '', '#' + id);
}
async function logout() { await fetch('/api/auth/logout', {method: 'POST'}); location.href = '/'; }

// ---- Search
$('s-go').onclick = () => run('s-out', 's-go', async () => {
  const q = need('s-q', 'Query'), m = $('s-m').value;
  const d = await api('/api/ir/search', {query: q, method: m});
  if (d.message) return empty(d.message);
  return '<p class="muted">' + NAMES[m] + '</p>' + rankTable(d.results);
});
// ---- Passages
$('ps-go').onclick = () => run('ps-out', 'ps-go', async () => {
  const d = await api('/api/ir/passages', {query: need('ps-q', 'Query'), text: need('ps-t', 'Text'), method: $('ps-m').value});
  return rankTable(d.results);
});

// ---- Recommenders
$('r-go').onclick = () => run('r-out', 'r-go', async () => {
  const d = await api('/api/ir/recommendations', {query: need('r-q', 'Query')});
  return d.recommendations && d.recommendations.length ? table(['#', 'Title', 'Similarity'], d.recommendations.map((r, i) => [i + 1, esc(r.title), (r.similarity_percent !== undefined ? r.similarity_percent : r.score) + '%'])) : empty('No similar projects found.');
});
// ---- PageRank
$('pr-go').onclick = () => run('pr-out', 'pr-go', async () => {
  const d = await api('/api/ir/pagerank', {threshold: parseFloat($('pr-t').value)});
  if (!d.nodes) return empty('No projects in the database yet.');
  return '<div class="info">' + d.nodes + ' nodes, ' + d.edges + ' edges' + (d.edges ? '' : ' — no pairs reach the threshold, so all scores are equal.') + '</div>' +
    table(['Rank', 'Title', 'PageRank', 'Links'], d.results.map(r => [r.position, esc(r.title), r.pagerank, r.links]));
});

(async function init() {
  try { user = (await api('/api/auth/me')).user; } catch { return; }
  $('who').textContent = user.name + ' (' + user.role + ')';
  $('back').href = user.role === 'faculty' ? '/faculty' : '/student';
  $('side').innerHTML = tabs.map(t => '<button data-t="' + t[0] + '">' + t[1] + '</button>').join('');
  document.querySelectorAll('#side button').forEach(b => b.onclick = () => show(b.dataset.t));
  try { projects = (await api('/api/ir/projects')).projects; } catch {}
  show(tabs.some(t => '#' + t[0] === location.hash) ? location.hash.slice(1) : 'search');
})();
