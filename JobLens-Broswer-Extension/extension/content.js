// Fake Job Detector: autoencoder verdict (via server) + key-detail highlighting (regex extraction)
(() => {
  const looksLikeJob = /job|career|hiring|vacanc|position|apply now|salary/i
    .test(document.title + " " + location.href + " " + document.body.innerText.slice(0, 3000));
  if (!looksLikeJob) return;

  const esc = s => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const SKILLS = ["python", "java", "javascript", "typescript", "sql", "react", "angular", "node.js",
    "html", "css", "excel", "power bi", "tableau", "aws", "azure", "docker", "git", "linux",
    "machine learning", "data analysis", "communication", "django", "flask", "php", "c#", "figma"];
  const FREE_MAIL = /@(gmail|yahoo|outlook|hotmail|rediffmail)\./i;

  // category -> color, label, regex  (red flags are listed first so they win ties)
  const CATS = {
    redflag: { color: "#ffb3b3", label: "Red flag",
      re: /registration fee|security deposit|processing fee|training fee|refundable|pay (?:a |the )?fee|whatsapp|telegram|no interview|no experience (?:needed|required)|guaranteed (?:job|income|salary)|urgent(?:ly)? hiring|earn (?:up to )?[₹$]?\s?\d[\d,]*\s?(?:per|\/|a) (?:day|week)/gi },
    salary: { color: "#b9f6ca", label: "Salary",
      re: /(?:₹|rs\.?|inr|\$|usd|€|£)\s?\d[\d,]*(?:\.\d+)?\s?(?:k|lpa|lakhs?)?(?:\s?(?:per|\/|a)\s?(?:month|week|day|hour|hr|year|annum))?|\b\d+(?:\.\d+)?\s?(?:lpa|lakhs?)\b/gi },
    email: { color: "#bbdefb", label: "Email",
      re: /[\w.+-]+@[\w-]+\.[\w.-]+/g },
    phone: { color: "#e1bee7", label: "Phone",
      re: /(?:\+\d{1,3}[\s-]?)?\b\d{5}[\s-]?\d{5}\b/g },
    experience: { color: "#ffe082", label: "Experience",
      re: /\b\d+\+?(?:\s?-\s?\d+)?\s?(?:years?|yrs?)(?:\s+of)?(?:\s+experience)?/gi },
    deadline: { color: "#ffccbc", label: "Deadline",
      re: /(?:apply (?:by|before)|last date|deadline)[^.\n]{0,30}/gi },
    skills: { color: "#b2ebf2", label: "Skill",
      re: new RegExp("(?<![\\w])(" + SKILLS.map(esc).join("|") + ")(?![\\w])", "gi") }
  };
  const found = {};
  Object.keys(CATS).forEach(k => (found[k] = new Set()));

  // ---------- highlighting ----------
  function markNode(node) {
    const text = node.nodeValue;
    const hits = [];
    for (const [cat, c] of Object.entries(CATS)) {
      for (const m of text.matchAll(c.re)) {
        hits.push({ start: m.index, end: m.index + m[0].length, cat, txt: m[0] });
      }
    }
    if (!hits.length) return;
    hits.sort((a, b) => a.start - b.start || b.end - a.end);
    const frag = document.createDocumentFragment();
    let pos = 0;
    for (const h of hits) {
      if (h.start < pos) continue;                    // skip overlaps
      frag.append(text.slice(pos, h.start));
      let cat = h.cat;
      if (cat === "email" && FREE_MAIL.test(h.txt)) cat = "redflag"; // personal email = red flag
      found[cat].add(h.txt.trim());
      const mark = document.createElement("mark");
      mark.className = "fjd-mark";
      mark.textContent = h.txt;
      mark.title = cat === "redflag" && h.cat === "email" ? "Red flag: personal email" : CATS[cat].label;
      mark.style.cssText = `background:${CATS[cat].color};color:#000;padding:0 2px;border-radius:3px;`;
      frag.append(mark);
      pos = h.end;
    }
    frag.append(text.slice(pos));
    node.replaceWith(frag);
  }

  function highlightPage() {
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {
      acceptNode(n) {
        const p = n.parentElement;
        if (!p || p.closest("script,style,noscript,textarea,input,#fjd-badge,#fjd-panel,.fjd-mark"))
          return NodeFilter.FILTER_REJECT;
        return n.nodeValue.trim().length > 2 ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT;
      }
    });
    const nodes = [];
    while (walker.nextNode() && nodes.length < 5000) nodes.push(walker.currentNode);
    nodes.forEach(markNode);
  }

  // ---------- UI ----------
  const badge = document.createElement("div");
  badge.id = "fjd-badge";
  badge.style.cssText = "position:fixed;top:12px;right:12px;z-index:2147483647;padding:10px 16px;" +
    "border-radius:8px;font:bold 14px sans-serif;color:#fff;box-shadow:0 2px 8px #0005;cursor:pointer;background:#5f6368";
  badge.textContent = "⏳ Analyzing job listing...";
  document.body.appendChild(badge);

  const panel = document.createElement("div");
  panel.id = "fjd-panel";
  panel.style.cssText = "position:fixed;top:56px;right:12px;z-index:2147483647;width:300px;max-height:70vh;" +
    "overflow:auto;background:#fff;color:#222;border-radius:8px;box-shadow:0 2px 12px #0006;" +
    "font:13px sans-serif;padding:12px;display:none";
  document.body.appendChild(panel);
  badge.onclick = () => (panel.style.display = panel.style.display === "none" ? "block" : "none");

  function buildPanel(res) {
    panel.textContent = "";
    const h = document.createElement("div");
    h.textContent = "Key details (click badge to hide)";
    h.style.cssText = "font-weight:bold;margin-bottom:8px";
    panel.append(h);

    const rows = [["redflag", "Red flags"], ["salary", "Salary"], ["email", "Email"], ["phone", "Phone"],
      ["experience", "Experience"], ["deadline", "Deadline"], ["skills", "Skills"]];
    for (const [key, label] of rows) {
      const row = document.createElement("div");
      row.style.cssText = "margin-bottom:6px";
      const t = document.createElement("span");
      t.textContent = label + ": ";
      t.style.cssText = `font-weight:bold;background:${CATS[key].color};padding:0 4px;border-radius:3px`;
      const v = document.createElement("span");
      const items = [...found[key]].slice(0, 8);
      v.textContent = items.length ? items.join(" | ") : "not found";
      if (!items.length) v.style.color = "#888";
      row.append(t, v);
      panel.append(row);
    }
    const foot = document.createElement("div");
    foot.style.cssText = "margin-top:8px;padding-top:8px;border-top:1px solid #ddd;color:#555";
    foot.textContent = res && !res.failed
      ? `Autoencoder error: ${res.error.toFixed(5)} (threshold ${res.threshold.toFixed(5)})`
      : "Autoencoder server not reachable";
    panel.append(foot);
  }

  // ---------- run ----------
  highlightPage();                                    // works even if the server is off
  chrome.runtime.sendMessage({ html: document.documentElement.outerHTML }, res => {
    const flags = found.redflag.size;
    if (!res || res.failed) {
      badge.textContent = "⚠️ Server offline (highlights only)";
    } else if (res.fraud) {
      badge.textContent = "⚠️ Likely FRAUD job listing";
      badge.style.background = "#d93025";
    } else if (flags >= 2) {
      badge.textContent = `⚠️ Caution: ${flags} red-flag phrases found`;
      badge.style.background = "#f9ab00";
    } else {
      badge.textContent = "✅ Looks genuine";
      badge.style.background = "#188038";
    }
    buildPanel(res);
  });
})();
