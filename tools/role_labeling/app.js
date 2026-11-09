// Gán nhãn vai trò, chạy offline. Lưu trong localStorage, xuất/nhập JSON "role-labels-v1".
const KEY = "role-labels-v1";
const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

let st = { name: "", batch: "", labels: {} };
try { st = Object.assign(st, JSON.parse(localStorage.getItem(KEY) || "{}")); } catch (e) { /* trình duyệt chặn lưu: vẫn chạy, nhớ xuất file */ }
const save = () => { try { localStorage.setItem(KEY, JSON.stringify(st)); } catch (e) { /* bỏ qua */ } };

const batches = [...new Set(DATA.jobs.map((j) => j.b))].sort();
let cur = 0;
const view = () => DATA.jobs.filter((j) => !st.batch || j.b === st.batch);
const lab = (id) => st.labels[id] || (st.labels[id] = { p: "", s: "", u: false, n: "" });

function renderList() {
  const v = view();
  $("list").innerHTML = v.map((j, i) => {
    const l = st.labels[j.id] || {};
    const cls = l.p ? (l.u ? "uns" : "done") : "";
    return `<a href="#" data-i="${i}" class="${i === cur ? "cur" : ""}"><span class="dot ${cls}"></span>${j.b} · ${String(i + 1).padStart(2, "0")}${l.p ? " · " + l.p : ""}</a>`;
  }).join("");
  const done = v.filter((j) => (st.labels[j.id] || {}).p).length;
  $("prog").textContent = `Đã gán ${done}/${v.length}`;
}

function renderJob() {
  const v = view();
  if (!v.length) { $("job").innerHTML = `<p class="empty">Không có tin trong lô này.</p>`; return; }
  cur = Math.max(0, Math.min(cur, v.length - 1));
  const j = v[cur], l = lab(j.id);
  $("pos").textContent = `${cur + 1} / ${v.length}`;
  $("job").innerHTML =
    `<h2>Mô tả công việc / trách nhiệm</h2><div class="txt">${esc(j.d) || "<i>(trống)</i>"}</div>` +
    `<h2>Yêu cầu</h2><div class="txt">${esc(j.q) || "<i>(trống)</i>"}</div>`;
  $("primary").innerHTML = DATA.roles.map(([c, n, d], i) =>
    `<button class="role ${l.p === c ? "sel" : ""}" data-p="${c}"><b>${i + 1} · ${c}</b>${esc(n)}<small>${esc(d)}</small></button>`).join("");
  $("secondary").innerHTML = [["", "Không có"], ...DATA.roles.map(([c]) => [c, c])].map(([c, n]) =>
    `<button class="sec ${l.s === c ? "sel" : ""}" data-s="${c}" ${c && c === l.p ? "disabled" : ""}>${esc(n)}</button>`).join("");
  $("unsure").checked = !!l.u;
  $("note").value = l.n || "";
  $("job").scrollTop = 0;
  renderList();
}

function setPrimary(c) {
  const l = lab(view()[cur].id);
  l.p = c; if (l.s === c) l.s = ""; l.t = new Date().toISOString(); save(); renderJob();
}

$("primary").addEventListener("click", (e) => { const b = e.target.closest("[data-p]"); if (b) setPrimary(b.dataset.p); });
$("secondary").addEventListener("click", (e) => {
  const b = e.target.closest("[data-s]"); if (!b) return;
  lab(view()[cur].id).s = b.dataset.s; save(); renderJob();
});
$("unsure").addEventListener("change", (e) => { lab(view()[cur].id).u = e.target.checked; save(); renderList(); });
$("note").addEventListener("input", (e) => { lab(view()[cur].id).n = e.target.value; save(); });
$("list").addEventListener("click", (e) => { const a = e.target.closest("[data-i]"); if (a) { e.preventDefault(); cur = +a.dataset.i; renderJob(); } });
$("prev").onclick = () => { cur--; renderJob(); };
$("next").onclick = () => { cur++; renderJob(); };
$("name").value = st.name;
$("name").addEventListener("input", (e) => { st.name = e.target.value.trim(); save(); });
$("batch").innerHTML = `<option value="">Tất cả</option>` + batches.map((b) => `<option ${b === st.batch ? "selected" : ""}>${b}</option>`).join("");
$("batch").addEventListener("change", (e) => { st.batch = e.target.value; cur = 0; save(); renderJob(); });

document.addEventListener("keydown", (e) => {
  if (["TEXTAREA", "INPUT", "SELECT"].includes(e.target.tagName)) return;
  const n = parseInt(e.key, 10);
  if (n >= 1 && n <= DATA.roles.length) setPrimary(DATA.roles[n - 1][0]);
  else if (e.key === "ArrowRight") { cur++; renderJob(); }
  else if (e.key === "ArrowLeft") { cur--; renderJob(); }
  else if (e.key.toLowerCase() === "u") { const l = lab(view()[cur].id); l.u = !l.u; save(); renderJob(); }
});

$("exp").onclick = () => {
  if (!st.name) { alert("Nhập tên trước khi xuất."); $("name").focus(); return; }
  const bmap = Object.fromEntries(DATA.jobs.map((j) => [j.id, j.b]));
  const labels = Object.entries(st.labels).filter(([, l]) => l.p).map(([id, l]) => ({
    job_id: id, batch: bmap[id] || "", primary: l.p, secondary: l.s || "", unsure: !!l.u, note: l.n || "", labeled_at: l.t || "",
  }));
  const doc = { format: DATA.version, guideline: "v1", labeler: st.name, exported_at: new Date().toISOString(), labels };
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([JSON.stringify(doc, null, 1)], { type: "application/json" }));
  a.download = `role_labels_${st.name.normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^A-Za-z0-9_-]+/g, "_")}.json`;
  a.click();
};
$("imp").onclick = () => $("impf").click();
$("impf").onchange = async (e) => {
  const f = e.target.files[0]; if (!f) return;
  try {
    const doc = JSON.parse(await f.text());
    if (doc.format !== DATA.version) throw new Error("sai định dạng");
    for (const l of doc.labels) st.labels[l.job_id] = { p: l.primary, s: l.secondary, u: l.unsure, n: l.note, t: l.labeled_at };
    if (!st.name) st.name = doc.labeler || "";
    $("name").value = st.name; save(); renderJob();
  } catch (err) { alert("Không đọc được file: " + err.message); }
  e.target.value = "";
};

renderJob();
