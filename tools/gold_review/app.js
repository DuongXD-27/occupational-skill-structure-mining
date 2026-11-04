(function () {
"use strict";
const D = JSON.parse(document.getElementById("gold-data").textContent);
const JOBS = D.jobs;
const BYID = Object.fromEntries(JOBS.map(j => [j.id, j]));
const TAX = D.tax.map(([id, n, al]) => ({ id, n, keys: [n, ...al].map(s => s.toLowerCase()) }));
const TAXBYID = Object.fromEntries(TAX.map(t => [t.id, t]));

const S = {
  cur: JOBS[0].id, filter: "all",
  uid: null, myName: "", db: null, canWrite: true,
  mine: {},            // jobId -> doc
  others: {},          // uid -> {jobId -> doc}
  names: {},           // uid -> display name
  reviewers: new Set(),
  sel: null,           // {s,e,text} chọn từ văn bản
  q: "", saving: 0, failed: false, registered: false,
};
try { const h = location.hash.slice(1); if (BYID[h]) S.cur = h; } catch (e) {}

const $ = id => document.getElementById(id);
const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const blank = () => ({ v: 1, rej: {}, res: {}, added: [], ind: [], indDone: false, note: "", done: false });
const docOf = id => S.mine[id] || (S.mine[id] = blank());

// ---------- quy tắc chốt nhãn ----------
function choicesFor(sg) {
  if (sg.k === "missing") return [["add", "Thêm " + sg.n], ["skip", "Bỏ qua"]];
  if (sg.a === "thay") return [["keep", "Giữ " + sg.n], ["replace", "Thay bằng " + sg.rn], ["reject", "Bỏ nhãn"]];
  if (sg.a === "sửa bằng chứng") return [["fix", "Dùng bằng chứng gợi ý"], ["keep", "Giữ bằng chứng cũ"], ["reject", "Bỏ nhãn"]];
  return [["keep", "Giữ nhãn"], ["reject", "Bỏ nhãn"]];
}
function sugForLabel(j, li) { return j.S.findIndex(s => s.k === "label" && s.li === li); }
function unresolved(j, d) { return j.S.filter((s, i) => !d.res[i]).length; }
function needsInd(j, d) { return j.kp && !d.indDone; }

function finalAnnotations(j, d) {
  const out = [];
  j.L.forEach((l, li) => {
    const si = sugForLabel(j, li);
    if (si >= 0) {
      const sg = j.S[si], ch = d.res[si];
      if (!ch || ch === "reject") return;
      if (ch === "keep") out.push({ ...l });
      if (ch === "fix") out.push({ ...l, s: sg.s, e: sg.e });
      if (ch === "replace") out.push({ n: sg.rn, id: sg.rid, s: sg.s, e: sg.e });
    } else if (!d.rej[li]) out.push({ ...l });
  });
  j.S.forEach((sg, si) => { if (sg.k === "missing" && d.res[si] === "add") out.push({ n: sg.n, id: sg.id, s: sg.s, e: sg.e }); });
  d.added.forEach(a => out.push({ ...a }));
  const seen = new Set();
  return out.filter(a => { const k = a.id + ":" + a.s; if (seen.has(k)) return false; seen.add(k); return true; });
}
function status(j) {
  const d = S.mine[j.id];
  if (d && d.done) return "done";
  if (d && (d.indDone || d.ind.length || Object.keys(d.res).length || Object.keys(d.rej).length || d.added.length)) return "part";
  return "todo";
}

// ---------- lưu ----------
const timers = {}, inflight = {}, again = {};
function touch(id) {
  const d = docOf(id); d.updatedAt = new Date().toISOString();
  clearTimeout(timers.all); timers.all = setTimeout(save, 400);
  render();
}
const KEY = "gold-review-v1";
function save() {
  timers.all = null;
  try {
    localStorage.setItem(KEY, JSON.stringify({ reviewer: S.myName, jobs: S.mine }));
    S.failed = false;
  } catch (e) { S.failed = true; }
  setSync();
}
function setSync() {
  $("sync").textContent = S.failed ? "Chưa lưu được trong trình duyệt – hãy bấm Xuất file" : "Đã lưu trong trình duyệt này";
}
function banner(msg) { const b = $("banner"); b.textContent = msg; b.hidden = !msg; }

// ---------- danh sách ----------
function renderList() {
  const items = $("items"), sel = $("jobsel");
  const show = JOBS.filter(j => S.filter === "all" || (S.filter === "todo" && status(j) !== "done") || (S.filter === "kp" && j.kp) || (S.filter === "holdout" && j.sp === "holdout"));
  items.innerHTML = show.map((j, i) => `<button class="item" type="button" data-id="${j.id}" aria-current="${j.id === S.cur}">
    <span class="dot ${status(j)}" aria-label="${{ done: "đã duyệt", part: "đang duyệt", todo: "chưa duyệt" }[status(j)]}"></span>
    <span style="min-width:0"><span class="t" style="display:block">${esc(j.t)}</span>
    <span class="m">${j.L.length} nhãn · ${j.S.length} góp ý${j.kp ? " · kappa" : ""}${j.sp === "holdout" ? " · holdout" : ""}</span></span></button>`).join("") || `<div class="empty" style="padding:10px">Không còn tin nào trong bộ lọc này.</div>`;
  sel.innerHTML = JOBS.map((j, i) => `<option value="${j.id}" ${j.id === S.cur ? "selected" : ""}>${i + 1}. ${{ done: "✓ ", part: "… ", todo: "" }[status(j)]}${esc(j.t)}</option>`).join("");
  const done = JOBS.filter(j => status(j) === "done").length;
  $("prog").style.width = (done / JOBS.length * 100) + "%";
  $("progtxt").textContent = done + "/" + JOBS.length;
}

// ---------- tô văn bản ----------
function marks(j, d) {
  const m = [];
  if (needsInd(j, d)) { d.ind.forEach((a, i) => m.push({ s: a.s, e: a.e, c: "mine", k: "ind" + i, p: 4 })); return m; }
  j.L.forEach((l, li) => {
    const si = sugForLabel(j, li);
    let c = d.rej[li] ? "drop" : "keep", s = l.s, e = l.e;
    if (si >= 0) {
      const ch = d.res[si];
      c = !ch ? "sug" : ch === "reject" ? "drop" : "keep";
      if (ch === "fix" || ch === "replace") { s = j.S[si].s; e = j.S[si].e; }
    }
    m.push({ s, e, c, k: "L" + li, p: c === "sug" ? 3 : c === "drop" ? 1 : 2 });
  });
  j.S.forEach((sg, si) => { if (sg.k === "missing" && d.res[si] !== "skip") m.push({ s: sg.s, e: sg.e, c: d.res[si] === "add" ? "keep" : "sug", k: "S" + si, p: 3 }); });
  d.added.forEach((a, i) => m.push({ s: a.s, e: a.e, c: "mine", k: "A" + i, p: 4 }));
  return m;
}
function renderText(j, d) {
  const x = j.x, m = marks(j, d), pts = new Set([0, x.length]);
  m.forEach(a => { pts.add(a.s); pts.add(a.e); });
  const P = [...pts].sort((a, b) => a - b);
  let h = "";
  for (let i = 0; i < P.length - 1; i++) {
    const a = P[i], b = P[i + 1], seg = esc(x.slice(a, b));
    const cov = m.filter(t => t.s <= a && t.e >= b).sort((p, q) => q.p - p.p);
    h += cov.length ? `<mark class="${cov[0].c}" data-k="${cov[0].k}">${seg}</mark>` : seg;
  }
  return h;
}

// ---------- trang một tin ----------
function hitList() {
  const q = S.q.trim().toLowerCase();
  if (!q) return [];
  const exact = [], pre = [], inc = [];
  TAX.forEach(t => {
    if (t.keys.some(k => k === q)) exact.push(t);
    else if (t.keys.some(k => k.startsWith(q))) pre.push(t);
    else if (t.keys.some(k => k.includes(q))) inc.push(t);
  });
  return [...exact, ...pre, ...inc].slice(0, 8);
}
function addBox(j, d) {
  const hits = hitList();
  const target = needsInd(j, d) ? "danh sách gán độc lập" : "gold";
  return `<div class="add">
    <h3>Thêm kỹ năng</h3>
    ${S.sel ? `<div>Đoạn đã chọn: <span class="mono">«${esc(S.sel.text)}»</span> <span class="muted mono">[${S.sel.s}–${S.sel.e}]</span></div>`
            : `<div class="muted" style="font-size:12.5px">Bôi đen đoạn bằng chứng trong văn bản, rồi chọn kỹ năng trong taxonomy. Nhãn sẽ được thêm vào ${target}.</div>`}
    <input id="q" type="search" placeholder="Tìm trong 246 kỹ năng của taxonomy (tên hoặc alias)" value="${esc(S.q)}" autocomplete="off">
    <div class="hits">${hits.map(t => `<button type="button" data-add="${t.id}" ${S.sel ? "" : "disabled"}>${esc(t.n)} <span class="muted mono">${t.id}</span></button>`).join("") || (S.q ? `<span class="empty">Không có kỹ năng nào khớp. Kỹ năng ngoài taxonomy ghi vào ô ghi chú.</span>` : "")}</div>
  </div>`;
}
function rowLabel(j, d, li) {
  const l = j.L[li], si = sugForLabel(j, li), ev = j.x.slice(l.s, l.e);
  if (si >= 0) {
    const sg = j.S[si], ch = d.res[si];
    return `<div class="row flag" data-row="L${li}"><div><span class="nm">${esc(l.n)}</span> <span class="ev">«${esc(ev)}»</span></div><span class="mono muted">${l.id}</span>
      <div class="why">${esc(sg.why)}${sg.s != null && sg.a !== "xem" ? ` Gợi ý: <span class="mono">«${esc(j.x.slice(sg.s, sg.e))}»</span>` : ""}</div>
      <div class="choices">${choicesFor(sg).map(([v, t]) => `<button type="button" data-res="${si}" data-v="${v}" aria-pressed="${ch === v}">${esc(t)}</button>`).join("")}</div></div>`;
  }
  return `<div class="row" data-row="L${li}"><div><span class="nm">${esc(l.n)}</span> <span class="ev">«${esc(ev)}»</span></div>
    <button type="button" class="tog ${d.rej[li] ? "off" : ""}" data-rej="${li}" aria-pressed="${!d.rej[li]}">${d.rej[li] ? "Đã bỏ" : "Giữ"}</button></div>`;
}
function rowMissing(j, d, si) {
  const sg = j.S[si], ch = d.res[si];
  return `<div class="row flag" data-row="S${si}"><div><span class="nm">Thiếu: ${esc(sg.n)}</span> <span class="ev">«${esc(j.x.slice(sg.s, sg.e))}»</span></div><span class="mono muted">${sg.lv === "cao" ? "ưu tiên cao" : "xem xét"}</span>
    <div class="why">${esc(sg.why)}</div>
    <div class="choices">${choicesFor(sg).map(([v, t]) => `<button type="button" data-res="${si}" data-v="${v}" aria-pressed="${ch === v}">${esc(t)}</button>`).join("")}</div></div>`;
}
function rowAdded(j, list, i, kind) {
  const a = list[i];
  return `<div class="row" data-row="${kind}${i}"><div><span class="nm">${esc(a.n)}</span> <span class="ev">«${esc(j.x.slice(a.s, a.e))}»</span></div>
    <button type="button" class="x" data-del="${kind}" data-i="${i}" aria-label="Xoá ${esc(a.n)}">×</button></div>`;
}

function renderJob() {
  const j = BYID[S.cur], d = docOf(j.id), idx = JOBS.indexOf(j);
  const ind = needsInd(j, d), open = unresolved(j, d);
  const flagged = j.L.map((_, li) => li).filter(li => sugForLabel(j, li) >= 0);
  const plain = j.L.map((_, li) => li).filter(li => sugForLabel(j, li) < 0);
  const miss = j.S.map((s, i) => i).filter(i => j.S[i].k === "missing");
  const fin = ind ? [] : finalAnnotations(j, d);
  let side;
  if (ind) {
    side = `<div class="card sec"><h3>Kỹ năng bạn gán (${d.ind.length})</h3>
      ${d.ind.map((_, i) => rowAdded(j, d.ind, i, "ind")).join("") || `<div class="empty">Chưa có nhãn nào. Bôi đen từng kỹ năng trong văn bản để gán.</div>`}</div>
      ${addBox(j, d)}
      <div class="foot"><button class="btn pri" type="button" id="indDone">Xong gán độc lập, mở bản nháp</button>
      <span class="muted" style="font-size:12.5px">Sau bước này mới thấy nhãn nháp và góp ý.</span></div>`;
  } else {
    side = `${flagged.length || miss.length ? `<div class="card sec"><h3>Cần quyết định (${open} còn lại)</h3>
        ${flagged.map(li => rowLabel(j, d, li)).join("")}${miss.map(si => rowMissing(j, d, si)).join("")}</div>` : ""}
      <div class="card sec"><h3>Nhãn nháp không bị góp ý (${plain.length})</h3>
        ${plain.map(li => rowLabel(j, d, li)).join("") || `<div class="empty">Không có.</div>`}</div>
      ${d.added.length ? `<div class="card sec"><h3>Bạn thêm (${d.added.length})</h3>${d.added.map((_, i) => rowAdded(j, d.added, i, "A")).join("")}</div>` : ""}
      ${addBox(j, d)}
      <div class="sec"><label for="note"><h3>Ghi chú cho tin này</h3></label>
        <textarea id="note" placeholder="Ví dụ: kỹ năng ngoài taxonomy, câu không rõ nghĩa">${esc(d.note)}</textarea></div>
      <div class="foot">
        <button class="btn ${d.done ? "" : "pri"}" type="button" id="done" ${open && !d.done ? "disabled" : ""}>${d.done ? "Mở lại để sửa" : "Đánh dấu đã duyệt"}</button>
        <span class="muted" style="font-size:12.5px">${open && !d.done ? `Còn ${open} mục cần quyết định.` : `Gold sau duyệt: ${fin.length} nhãn.`}</span>
        <span class="grow"></span>
        <button class="btn" type="button" data-go="${idx + 1}" ${idx + 1 >= JOBS.length ? "disabled" : ""}>Tin sau →</button>
      </div>`;
  }
  $("job").innerHTML = `
    <div class="jhead"><div class="grow"><h2>${esc(j.t)}</h2>
      <div class="muted" style="font-size:12.5px"><span class="mono">${j.id}</span> · ${esc(j.src)} · <a href="${esc(j.url)}" target="_blank" rel="noopener">Xem tin gốc</a></div></div>
      <span class="chip ${j.sp === "holdout" ? "ho" : ""}" title="Nửa holdout chỉ dùng báo cáo P/R/F1 chính thức">${j.sp}</span>
      ${j.kp ? `<span class="chip kp" title="Một trong 18 tin hai người gán độc lập để đo Cohen's kappa">nhóm kappa</span>` : ""}
      <span class="mono muted">${idx + 1}/${JOBS.length}</span></div>
    ${ind ? `<div class="step"><b>Bước 1/2 · gán độc lập.</b> Tin này thuộc nhóm đo đồng thuận nên nhãn nháp đang bị ẩn. Hãy tự gán mọi kỹ năng bạn thấy, sau đó mới mở bản nháp để duyệt như bình thường.</div>`
         : j.note ? `<div class="step" style="border-color:var(--line)"><b>Ghi chú của người gán nháp:</b> ${esc(j.note)}</div>` : ""}
    <div class="card"><div class="txt" id="txt">${renderText(j, d)}</div>
      <div class="legend">${ind ? `<span class="lg-mine">bạn gán</span>` : `<span class="lg-keep">giữ</span><span class="lg-sug">cần quyết định</span><span class="lg-drop">bỏ</span><span class="lg-mine">bạn thêm</span>`}</div></div>
    <div class="side">${side}</div>`;
}

function render() { renderList(); renderJob(); }

// ---------- sự kiện ----------
function go(id) { S.cur = id; S.sel = null; S.q = ""; try { history.replaceState(null, "", "#" + id); } catch (e) {} render(); window.scrollTo({ top: 0 }); }
document.addEventListener("click", ev => {
  const t = ev.target.closest("button,mark");
  if (!t) return;
  const j = BYID[S.cur], d = docOf(j.id);
  if (t.dataset.id) return go(t.dataset.id);
  if (t.dataset.f) { S.filter = t.dataset.f; document.querySelectorAll(".filters button").forEach(b => b.setAttribute("aria-pressed", b === t)); return renderList(); }
  if (t.dataset.go) return go(JOBS[+t.dataset.go].id);
  if (t.dataset.res) { const si = +t.dataset.res; d.res[si] = d.res[si] === t.dataset.v ? undefined : t.dataset.v; if (!d.res[si]) delete d.res[si]; d.done = false; return touch(j.id); }
  if (t.dataset.rej) { const li = +t.dataset.rej; if (d.rej[li]) delete d.rej[li]; else d.rej[li] = true; d.done = false; return touch(j.id); }
  if (t.dataset.del) { const list = t.dataset.del === "ind" ? d.ind : d.added; list.splice(+t.dataset.i, 1); d.done = false; return touch(j.id); }
  if (t.dataset.add) {
    if (!S.sel) return;
    const tx = TAXBYID[t.dataset.add], a = { n: tx.n, id: tx.id, s: S.sel.s, e: S.sel.e };
    (needsInd(j, d) ? d.ind : d.added).push(a); d.done = false; S.sel = null; S.q = "";
    return touch(j.id);
  }
  if (t.id === "indDone") { d.indDone = true; return touch(j.id); }
  if (t.id === "done") { d.done = !d.done; if (d.done) d.finalCount = finalAnnotations(j, d).length; return touch(j.id); }
  if (t.tagName === "MARK") {
    const row = document.querySelector(`[data-row="${t.dataset.k}"]`);
    if (row) { row.scrollIntoView({ block: "nearest", behavior: "smooth" }); row.classList.add("flash"); setTimeout(() => row.classList.remove("flash"), 900); }
  }
});
document.addEventListener("input", ev => {
  if (ev.target.id === "q") {
    S.q = ev.target.value; const pos = ev.target.selectionStart;
    renderJob(); const q = $("q"); q.focus(); try { q.setSelectionRange(pos, pos); } catch (e) {}
  }
  if (ev.target.id === "note") {
    const d = docOf(S.cur); d.note = ev.target.value;
    clearTimeout(timers.all); timers.all = setTimeout(save, 600);
  }
});
$("jobsel").addEventListener("change", ev => go(ev.target.value));

// chọn đoạn văn bản -> offset trên trường text
function captureSel() {
  const txt = $("txt"), s = window.getSelection();
  if (!txt || !s || s.rangeCount === 0 || s.isCollapsed) return;
  const r = s.getRangeAt(0);
  if (!txt.contains(r.startContainer) || !txt.contains(r.endContainer)) return;
  const pre = document.createRange(); pre.setStart(txt, 0); pre.setEnd(r.startContainer, r.startOffset);
  let st = pre.toString().length, en = st + r.toString().length;
  const x = BYID[S.cur].x;
  while (st < en && /\s/.test(x[st])) st++;
  while (en > st && /\s/.test(x[en - 1])) en--;
  if (en <= st) return;
  const text = x.slice(st, en);
  S.sel = { s: st, e: en, text };
  S.q = text.length <= 40 ? text : "";
  renderJob();
}
document.addEventListener("mouseup", ev => { if (ev.target.closest && ev.target.closest("#txt")) setTimeout(captureSel, 0); });
document.addEventListener("selectionchange", () => {
  const s = window.getSelection(); if (!s || s.isCollapsed) return;
  clearTimeout(captureSel.t); captureSel.t = setTimeout(() => { if (matchMedia("(pointer:coarse)").matches) captureSel(); }, 600);
});

// ---------- xuất / nhập file ----------
function slug(t) { return (t || "nguoi-duyet").normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/đ/g, "d").replace(/Đ/g, "D").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, ""); }
function exportReview() {
  if (!S.myName) { banner("Nhập tên người duyệt ở góc trên trước khi xuất file."); $("reviewer").focus(); return; }
  const data = { format: "gold-review-v1", reviewer: S.myName, exported_at: new Date().toISOString(),
    jobs_done: JOBS.filter(j => status(j) === "done").length, jobs: S.mine };
  const blob = new Blob([JSON.stringify(data, null, 1)], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob); a.download = "gold_review_" + slug(S.myName) + ".json";
  document.body.appendChild(a); a.click(); a.remove();
  banner("Đã xuất " + a.download + ". Chép file vào data/evaluation/reviews/ rồi commit.");
}
function importReview(file) {
  const r = new FileReader();
  r.onload = () => {
    try {
      const d = JSON.parse(r.result);
      if (d.format !== "gold-review-v1" || typeof d.jobs !== "object") throw new Error("sai định dạng");
      S.mine = {}; Object.entries(d.jobs).forEach(([k, v]) => { if (BYID[k]) S.mine[k] = Object.assign(blank(), v); });
      S.myName = d.reviewer || S.myName; $("reviewer").value = S.myName;
      save(); render(); banner("Đã mở kết quả của " + (d.reviewer || "người duyệt") + ".");
    } catch (e) { banner("Không đọc được file: " + e.message); }
  };
  r.readAsText(file);
}
document.addEventListener("click", ev => {
  if (ev.target.id === "export-file") exportReview();
  if (ev.target.id === "import-btn") $("import-file").click();
});
$("import-file").addEventListener("change", ev => { if (ev.target.files[0]) importReview(ev.target.files[0]); ev.target.value = ""; });
$("reviewer").addEventListener("input", ev => { S.myName = ev.target.value.trim(); clearTimeout(timers.all); timers.all = setTimeout(save, 400); });

// ---------- mở lại phiên trước ----------
try {
  const saved = JSON.parse(localStorage.getItem(KEY) || "null");
  if (saved) { S.myName = saved.reviewer || ""; Object.entries(saved.jobs || {}).forEach(([k, v]) => { if (BYID[k]) S.mine[k] = Object.assign(blank(), v); }); }
} catch (e) {}
$("reviewer").value = S.myName;
render(); setSync();
})();
