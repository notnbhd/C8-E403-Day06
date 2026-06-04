// ---- Hevy AI webapp (vanilla) ----
const USER = "demo-user";
const CID = "web-" + Math.random().toString(36).slice(2, 10);
const api = (p, opts) => fetch("/api" + p, opts).then((r) => r.json());

const state = { name: "Athlete", screen: "home", returnTo: "home", routines: [] };

// ---------- Icons ----------
const ICON = {
  edit:  `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 20h4L19 9l-4-4L4 16v4Z"/><path d="M14 6l4 4"/></svg>`,
  share: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 15V4"/><path d="M8 8l4-4 4 4"/><path d="M5 13v6h14v-6"/></svg>`,
  gear:  `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M5 5l2 2M17 17l2 2M19 5l-2 2M7 17l-2 2"/></svg>`,
  more:  `<svg viewBox="0 0 24 24" fill="currentColor"><circle cx="5" cy="12" r="2"/><circle cx="12" cy="12" r="2"/><circle cx="19" cy="12" r="2"/></svg>`,
  like:  `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><path d="M7 10v10H4V10h3Zm0 0 4-7c1.3 0 2 .9 2 2l-.6 3.5H19a2 2 0 0 1 2 2.3l-1.2 6A2 2 0 0 1 17.8 20H7"/></svg>`,
  comment: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><path d="M21 11.5a8 8 0 0 1-11.6 7.1L3 20l1.4-5.4A8 8 0 1 1 21 11.5Z"/></svg>`,
};

// ---------- Top bar ----------
function setTopbar({ title, back = false, headline = false, actions = [] }) {
  const bar = document.getElementById("topbar");
  bar.classList.toggle("headline", headline);
  document.getElementById("tb-title").textContent = title;
  document.getElementById("tb-back").hidden = !back;
  document.getElementById("tb-actions").innerHTML = actions
    .map((a) => `<button class="tb-btn" aria-label="${a.label}">${a.svg}</button>`)
    .join("");
}
function applyTopbar(name) {
  switch (name) {
    case "home":     return setTopbar({ title: "Home", headline: true });
    case "workout":  return setTopbar({ title: "Workout", headline: true });
    case "profile":  return setTopbar({ title: state.name, headline: true,
        actions: [{ label: "Edit", svg: ICON.edit }, { label: "Share", svg: ICON.share }, { label: "Settings", svg: ICON.gear }] });
    case "workout-detail": return setTopbar({ title: "Workout Detail", back: true, actions: [{ label: "More", svg: ICON.more }] });
    case "routine-detail": return setTopbar({ title: "Routine", back: true,
        actions: [{ label: "Share", svg: ICON.share }, { label: "More", svg: ICON.more }] });
    case "coach":    return setTopbar({ title: "AI Coach", back: true });
  }
}
document.getElementById("tb-back").addEventListener("click", () => showScreen(state.returnTo || "home"));

// ---------- Navigation ----------
const SCREEN_TAB = { home: "home", workout: "workout", profile: "profile",
  "workout-detail": "profile", "routine-detail": "workout" };
const loaders = {};

function showScreen(name) {
  state.screen = name;
  document.querySelectorAll(".screen").forEach((s) =>
    s.classList.toggle("active", s.dataset.screen === name));
  const tab = SCREEN_TAB[name];
  if (tab) document.querySelectorAll(".tab").forEach((t) =>
    t.classList.toggle("active", t.dataset.go === tab));
  applyTopbar(name);
  document.querySelector(".screen.active")?.scrollTo(0, 0);
  if (loaders[name]) loaders[name]();
  if (name === "coach") setTimeout(() => document.getElementById("chat-input")?.focus(), 50);
}
document.querySelectorAll(".tab").forEach((t) =>
  t.addEventListener("click", () => showScreen(t.dataset.go)));

function goCoachWith(q) {
  state.returnTo = SCREEN_TAB[state.screen] ? state.screen : "home";
  showScreen("coach");
  if (q) setTimeout(() => sendQuick(q), 150);
}

// ---------- Format helpers ----------
function initials(name) { return (name || "A").trim()[0]?.toUpperCase() || "A"; }
function fmtDur(min) {
  min = Math.round(min || 0);
  const h = Math.floor(min / 60), m = min % 60;
  return h && m ? `${h}h ${m}min` : h ? `${h}h` : `${m}min`;
}
function fmtDate(iso) {
  const d = new Date(iso + "T00:00:00");
  return d.toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric", year: "numeric" });
}
function num(n) { return (n || 0).toLocaleString(); }
function md(text) {
  return (text || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/\*\*(.+?)\*\*/g, "<b>$1</b>").replace(/\n/g, "<br>");
}

// ---------- Charts (inline SVG) ----------
const metricVal = (d, m) => m === "volume" ? d.volume_kg : m === "reps" ? d.reps : d.duration_min;

function xLabels(series) {
  const n = series.length;
  if (n <= 6) return series.map((_, i) => i);
  const step = Math.ceil(n / 6);
  const idx = [];
  for (let i = 0; i < n; i += step) idx.push(i);
  return idx;
}

function barChart(series, metric) {
  if (!series.length) return `<svg viewBox="0 0 320 150"></svg>`;
  const W = 320, H = 150, pl = 4, pr = 4, pt = 10, pb = 20;
  const vals = series.map((d) => metricVal(d, metric));
  const max = Math.max(1, ...vals);
  const n = series.length;
  const slot = (W - pl - pr) / n, bw = Math.min(slot * 0.62, 22);
  const ch = H - pt - pb;
  let g = "";
  for (let i = 0; i <= 3; i++) {
    const y = pt + (ch * i) / 3;
    g += `<line class="gridline" x1="${pl}" y1="${y}" x2="${W - pr}" y2="${y}"/>`;
  }
  const bars = vals.map((v, i) => {
    const h = (v / max) * ch;
    const x = pl + slot * i + (slot - bw) / 2;
    return `<rect class="bar" x="${x.toFixed(1)}" y="${(pt + ch - h).toFixed(1)}" width="${bw.toFixed(1)}" height="${Math.max(2, h).toFixed(1)}" rx="3"/>`;
  }).join("");
  const labels = xLabels(series).map((i) => {
    const x = pl + slot * i + slot / 2;
    return `<text class="axis" x="${x.toFixed(1)}" y="${H - 5}" text-anchor="middle">${series[i].label}</text>`;
  }).join("");
  return `<svg viewBox="0 0 ${W} ${H}">${g}${bars}${labels}</svg>`;
}

function lineChart(series, metric) {
  if (!series.length) return `<svg viewBox="0 0 320 150"></svg>`;
  const W = 320, H = 150, pl = 4, pr = 8, pt = 12, pb = 20;
  const vals = series.map((d) => metricVal(d, metric));
  const max = Math.max(1, ...vals), min = Math.min(...vals);
  const span = max - min || 1;
  const n = series.length;
  const cw = W - pl - pr, ch = H - pt - pb;
  const X = (i) => n === 1 ? pl + cw / 2 : pl + (cw * i) / (n - 1);
  const Y = (v) => pt + ch - ((v - min) / span) * ch;
  let g = "";
  for (let i = 0; i <= 3; i++) {
    const y = pt + (ch * i) / 3;
    g += `<line class="gridline" x1="${pl}" y1="${y}" x2="${W - pr}" y2="${y}"/>`;
  }
  const pts = vals.map((v, i) => `${X(i).toFixed(1)},${Y(v).toFixed(1)}`).join(" ");
  const dots = vals.map((v, i) => `<circle class="dot" cx="${X(i).toFixed(1)}" cy="${Y(v).toFixed(1)}" r="3"/>`).join("");
  const labels = xLabels(series).map((i) =>
    `<text class="axis" x="${X(i).toFixed(1)}" y="${H - 5}" text-anchor="middle">${series[i].label}</text>`).join("");
  return `<svg viewBox="0 0 ${W} ${H}"><polyline class="line" points="${pts}"/>${dots}${g ? "" : ""}${dots}${labels}${g}`
    .replace(`<svg viewBox="0 0 ${W} ${H}">`, `<svg viewBox="0 0 ${W} ${H}">${g}`) // gridlines under line
    + `</svg>`;
}

// ---------- Set tables / blocks ----------
function exBlock2col(e) {
  const rows = e.sets.map((s, i) =>
    `<div class="trow"><span class="sn">${i + 1}</span><span class="v">${(+s.weight_kg).toLocaleString()} kg × ${s.reps}</span></div>`).join("");
  return `<div class="ex-block">
    <div class="ex-head"><div class="avatar sm">${initials(e.name)}</div><span class="name">${e.name}</span></div>
    <div class="set-table cols2">
      <div class="thead"><span>Set</span><span>Weight &amp; Reps</span></div>${rows}
    </div></div>`;
}
function exBlock3col(e) {
  const rows = e.sets.map((s, i) =>
    `<div class="trow"><span class="sn">${i + 1}</span><span class="v">${s.kg != null ? (+s.kg).toLocaleString() : "—"}</span><span class="v">${s.reps}</span></div>`).join("");
  return `<div class="ex-block">
    <div class="ex-head"><div class="avatar sm">${initials(e.name)}</div><span class="name">${e.name}</span></div>
    <div class="set-table cols3">
      <div class="thead"><span>Set</span><span>Kg</span><span>Reps</span></div>${rows}
    </div></div>`;
}
function splitRow(s) {
  return `<div class="split-row">
    <div class="split-top"><span>${s.group}</span><span class="split-pct">${s.pct}%</span></div>
    <div class="mbar-track"><div class="mbar-fill" style="width:${s.pct}%"></div></div></div>`;
}

// ---------- HOME ----------
loaders.home = async function () {
  const d = await api(`/home/${USER}`);
  setName(d.name);
  document.getElementById("st-sessions").textContent = d.week_sessions;
  document.getElementById("st-volume").textContent = num(d.week_volume);
  document.getElementById("st-ex").textContent = d.tracked_exercises;

  const card = document.getElementById("insight-card");
  document.getElementById("insight-text").textContent = d.insight || "Log a few sessions and I'll analyse your training.";
  card.dataset.q = d.insight && d.insight.includes("bỏ bê")
    ? "Nhóm cơ nào tôi đang bỏ bê?" : "Bài nào của tôi đang tiến bộ tốt nhất?";

  const vols = d.muscle_volume || {};
  const max = Math.max(1, ...Object.values(vols));
  document.getElementById("muscle-bars").innerHTML = Object.entries(vols)
    .sort((a, b) => b[1] - a[1])
    .map(([g, v]) => {
      const pct = Math.round((v / max) * 100);
      const low = pct < 40 ? "low" : "";
      return `<div><div class="mbar-top"><span>${g}</span><span class="pct">${pct}%</span></div>
        <div class="mbar-track"><div class="mbar-fill ${low}" style="width:${pct}%"></div></div></div>`;
    }).join("") || `<p class="muted">Chưa có dữ liệu.</p>`;
};

// ---------- WORKOUT (routines) ----------
loaders.workout = async function () {
  const items = await api(`/routines/${USER}`);
  state.routines = items;
  const list = document.getElementById("routines-list");
  list.innerHTML = items.map((r) => `
    <button class="rt-card" onclick="openRoutine(${r.index})">
      <h3>${r.name}</h3>
      <div class="rt-sub">${r.exercises.length} exercises · ${r.created_by}</div>
      <div class="rt-ex">${r.exercises.map((e) => e.name).join(", ")}</div>
    </button>`).join("") || `<p class="muted">Chưa có routine. Tạo với AI nhé!</p>`;
};

// ---------- PROFILE ----------
let _pfSeries = [];
loaders.profile = async function () {
  const d = await api(`/profile/${USER}`);
  setName(d.name);
  document.getElementById("pf-avatar").textContent = initials(d.name);
  document.getElementById("pf-name").textContent = d.name;
  document.getElementById("pf-workouts").textContent = d.workouts_count;
  document.getElementById("pf-followers").textContent = d.followers;
  document.getElementById("pf-following").textContent = d.following;
  document.getElementById("pf-pct").textContent = d.profile_pct;

  _pfSeries = d.series || [];
  drawProfileChart("duration");
  document.querySelectorAll("#pf-toggle .pill").forEach((p) =>
    p.onclick = () => {
      document.querySelectorAll("#pf-toggle .pill").forEach((x) => x.classList.remove("active"));
      p.classList.add("active");
      drawProfileChart(p.dataset.metric);
    });

  document.getElementById("profile-workouts").innerHTML = (d.recent_workouts || []).map((w) => `
    <button class="wk-card" onclick="openWorkout('${w.id}')">
      <div class="wk-author"><div class="avatar sm">${initials(d.name)}</div>
        <div><div class="n">${d.name}</div><div class="d">${fmtDate(w.date)}</div></div>
        <span class="more">${ICON.more}</span></div>
      <h3>${w.title}</h3>
      <div class="wk-kpis">
        <div><div class="kpi-lbl">Time</div><div class="kpi-val">${fmtDur(w.duration_min)}</div></div>
        <div><div class="kpi-lbl">Volume</div><div class="kpi-val">${num(w.volume_kg)} kg</div></div>
        <div><div class="kpi-lbl">Sets</div><div class="kpi-val">${w.total_sets}</div></div>
      </div>
    </button>`).join("") || `<p class="muted">Chưa có buổi tập nào.</p>`;
};

function drawProfileChart(metric) {
  const last = _pfSeries[_pfSeries.length - 1];
  const totalMin = last ? last.duration_min : 0;
  document.getElementById("chart-total").textContent = `${(totalMin / 60).toFixed(totalMin % 60 ? 1 : 0)} hours`;
  document.getElementById("pf-chart").innerHTML = barChart(_pfSeries, metric);
}

// ---------- WORKOUT DETAIL ----------
async function openWorkout(id) {
  state.returnTo = state.screen === "profile" ? "profile" : "home";
  const w = await api(`/workout/${USER}/${id}`);
  const split = w.muscle_split || [];
  const shown = split.slice(0, 3);
  document.getElementById("wd-body").innerHTML = `
    <div class="wd-author"><div class="avatar md">${initials(w.athlete)}</div>
      <div><div class="name">${w.athlete}</div><div class="date">${fmtDate(w.date)}</div></div></div>
    <div class="wd-h1">${w.title}</div>
    <div class="kpi-row">
      <div><div class="kpi-lbl">Time</div><div class="kpi-val">${fmtDur(w.duration_min)}</div></div>
      <div><div class="kpi-lbl">Volume</div><div class="kpi-val">${num(w.volume_kg)} kg</div></div>
      <div><div class="kpi-lbl">Sets</div><div class="kpi-val">${w.total_sets}</div></div>
    </div>
    <div class="social-row">${ICON.like}${ICON.comment}${ICON.share}</div>
    <div class="split-title">Muscle Split</div>
    ${shown.map(splitRow).join("")}
    ${split.length > 3 ? `<button class="split-more">Show ${split.length - 3} more</button>` : ""}
    <div class="ex-section-head"><span class="t">Workout</span><button class="link">Edit Workout</button></div>
    ${w.exercises.map(exBlock2col).join("")}`;
  showScreen("workout-detail");
}

// ---------- ROUTINE DETAIL ----------
async function openRoutine(index) {
  state.returnTo = "workout";
  const r = await api(`/routine/${USER}/${index}`);
  const series = r.series || [];
  const last = series[series.length - 1];
  renderRoutineChart(r, "volume");
  showScreen("routine-detail");
}

function renderRoutineChart(r, metric) {
  const series = r.series || [];
  const last = series[series.length - 1];
  const unit = metric === "volume" ? "kg" : metric === "reps" ? "reps" : "min";
  const head = last ? `${num(metricVal(last, metric))} ${unit} · ${last.label}` : "";
  document.getElementById("rd-body").innerHTML = `
    <div class="wd-h1">${r.name}</div>
    <div class="muted" style="margin:-8px 0 16px">Created by ${r.created_by}</div>
    <button class="btn-primary" onclick="goCoachWith('Lên kế hoạch cho buổi ${r.name} hôm nay')">Start Routine</button>
    <div class="chart-head" style="margin-top:18px"><div><b>${head}</b></div>
      <button class="range-pill">Last 3 months ▾</button></div>
    <div class="chart-box">${lineChart(series, metric)}</div>
    <div class="toggle-pills" id="rd-toggle">
      <button class="pill ${metric === "volume" ? "active" : ""}" data-metric="volume">Volume</button>
      <button class="pill ${metric === "reps" ? "active" : ""}" data-metric="reps">Reps</button>
      <button class="pill ${metric === "duration" ? "active" : ""}" data-metric="duration">Duration</button>
    </div>
    <div class="ex-section-head"><span class="t">Exercises</span><button class="link">Edit Routine</button></div>
    ${r.exercises.map(exBlock3col).join("")}`;
  document.querySelectorAll("#rd-toggle .pill").forEach((p) =>
    p.onclick = () => renderRoutineChart(r, p.dataset.metric));
}

// ---------- shared ----------
function setName(name) {
  if (!name) return;
  state.name = name;
  document.getElementById("home-name").textContent = name.split(" ")[0];
  if (state.screen === "profile") document.getElementById("tb-title").textContent = name;
}

// ---------- COACH (chat) ----------
const stream = document.getElementById("chat-stream");
function addBubble(role, html, cls = "") {
  const wrap = document.createElement("div");
  wrap.className = `msg ${role} ${cls}`;
  wrap.innerHTML = `<div class="bubble">${html}</div>`;
  stream.appendChild(wrap);
  stream.scrollTop = stream.scrollHeight;
  return wrap;
}
function typing() { return addBubble("assistant", "<span></span><span></span><span></span>", "typing"); }

function renderReply(out) {
  if (out.status === "awaiting_confirm") return renderRoutine(out.routine);
  const parts = (out.reply || "").split(/\n\n(?=⚠️)/);
  addBubble("assistant", md(parts[0]));
  if (parts[1]) addBubble("assistant", md(parts[1]), "warn");
}

function renderRoutine(routine) {
  const rows = routine.exercises.map((e) =>
    `<div class="r-ex"><span>${e.name}</span><span class="meta">${e.sets}×${e.reps} · ${e.rest_sec}s</span></div>`).join("");
  const wrap = document.createElement("div");
  wrap.className = "msg assistant";
  wrap.innerHTML = `<div class="routine-card">
      <h4>📋 ${routine.name}</h4>${rows}
      <div class="routine-actions">
        <button class="btn-cancel">Huỷ</button>
        <button class="btn-confirm">Lưu vào app</button>
      </div></div>`;
  stream.appendChild(wrap);
  stream.scrollTop = stream.scrollHeight;
  wrap.querySelector(".btn-confirm").onclick = () => resolveRoutine(wrap, true);
  wrap.querySelector(".btn-cancel").onclick = () => resolveRoutine(wrap, false);
}

async function resolveRoutine(wrap, approved) {
  wrap.querySelectorAll("button").forEach((b) => (b.disabled = true));
  const t = typing();
  const out = await api("/chat/resume", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ conversation_id: CID, approved }),
  });
  t.remove();
  renderReply(out);
}

async function send(text) {
  addBubble("user", md(text));
  const t = typing();
  let out;
  try {
    out = await api("/chat", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: USER, conversation_id: CID, message: text }),
    });
  } catch (e) { out = { status: "ok", reply: "Lỗi kết nối tới server 😕" }; }
  t.remove();
  renderReply(out);
}

function onSend(ev) {
  ev.preventDefault();
  const input = document.getElementById("chat-input");
  const text = input.value.trim();
  if (!text) return false;
  input.value = "";
  send(text);
  return false;
}
function sendQuick(text) {
  if (state.screen !== "coach") goCoachWith("");
  send(text);
}

// ---------- init ----------
function tick() {
  const d = new Date();
  document.getElementById("clock").textContent =
    `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
}
tick(); setInterval(tick, 30000);
loaders.profile();        // nạp tên cho home + profile
showScreen("home");
