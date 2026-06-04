// ---- Hevy AI webapp (vanilla) ----
const USER = "demo-user";
const CID = "web-" + Math.random().toString(36).slice(2, 10);
const api = (p, opts) => fetch("/api" + p, opts).then((r) => r.json());

// ---------- Navigation ----------
const loaders = {}; // screen -> loader (chạy 1 lần)
function showScreen(name) {
  document.querySelectorAll(".screen").forEach((s) =>
    s.classList.toggle("active", s.dataset.screen === name)
  );
  document.querySelectorAll(".tab").forEach((t) =>
    t.classList.toggle("active", t.dataset.go === name)
  );
  const titles = { home: "Trang chủ", history: "Lịch sử", coach: "Coach AI", routines: "Routines", profile: "Hồ sơ" };
  document.getElementById("appbar-title").textContent = titles[name] || "";
  if (loaders[name]) { loaders[name](); }
  if (name === "coach") setTimeout(() => document.getElementById("chat-input")?.focus(), 50);
}
document.querySelectorAll(".tab").forEach((t) =>
  t.addEventListener("click", () => showScreen(t.dataset.go))
);

function goCoachWith(q) {
  showScreen("coach");
  if (q) setTimeout(() => sendQuick(q), 150);
}

// ---------- tiny markdown ----------
function md(text) {
  const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  return esc(text)
    .replace(/\*\*(.+?)\*\*/g, "<b>$1</b>")
    .replace(/\n/g, "<br>");
}

// ---------- HOME ----------
loaders.home = async function () {
  const d = await api(`/home/${USER}`);
  document.getElementById("st-sessions").textContent = d.week_sessions;
  document.getElementById("st-volume").textContent = (d.week_volume || 0).toLocaleString();
  document.getElementById("st-ex").textContent = d.tracked_exercises;

  const card = document.getElementById("insight-card");
  document.getElementById("insight-text").textContent = d.insight || "Cứ tiếp tục — log thêm vài buổi để Coach phân tích sâu hơn.";
  card.dataset.q = d.insight && d.insight.includes("bỏ bê")
    ? "Nhóm cơ nào tôi đang bỏ bê?"
    : "Bài nào của tôi đang tiến bộ tốt nhất?";

  const vols = d.muscle_volume || {};
  const max = Math.max(1, ...Object.values(vols));
  document.getElementById("muscle-bars").innerHTML = Object.entries(vols)
    .sort((a, b) => b[1] - a[1])
    .map(([g, v]) => {
      const pct = Math.round((v / max) * 100);
      const low = pct < 40 ? "low" : "";
      return `<div class="mbar"><div class="mbar-name">${g}</div>
        <div class="mbar-track"><div class="mbar-fill ${low}" style="width:${pct}%"></div></div></div>`;
    }).join("");
};

// ---------- HISTORY ----------
loaders.history = async function () {
  const items = await api(`/history/${USER}`);
  document.getElementById("history-list").innerHTML = items.map((w) => `
    <div class="card">
      <div class="card-head">
        <span class="card-title">${w.title}</span>
        <span class="card-sub">${(w.volume_kg || 0).toLocaleString()} kg</span>
      </div>
      ${w.exercises.map((e) => `<div class="ex-row"><span>${e.name} · ${e.sets} sets</span><span class="meta">${e.top_set}</span></div>`).join("")}
    </div>`).join("") || `<p class="muted">Chưa có buổi tập nào.</p>`;
};

// ---------- ROUTINES ----------
loaders.routines = async function () {
  const items = await api(`/routines/${USER}`);
  document.getElementById("routines-list").innerHTML = items.map((r) => `
    <div class="card">
      <div class="card-head"><span class="card-title">${r.name}</span>
        <span class="card-sub">${r.exercises.length} bài</span></div>
      ${r.exercises.map((e) => `<div class="ex-row"><span>${e.name}</span><span class="meta">${e.sets}×${e.reps}</span></div>`).join("")}
    </div>`).join("") || `<p class="muted">Chưa có routine. Tạo với AI nhé!</p>`;
};

// ---------- PROFILE ----------
loaders.profile = async function () {
  const d = await api(`/profile/${USER}`);
  document.getElementById("pf-name").textContent = d.name;
  document.getElementById("pf-avatar").textContent = (d.name || "A")[0];
  document.getElementById("pf-id").textContent = d.user_id;
  document.getElementById("pf-sessions").textContent = d.total_sessions;
  document.getElementById("pf-ex").textContent = d.tracked_exercises;
  document.getElementById("pf-routines").textContent = d.routines;
  document.getElementById("home-name").textContent = d.name.split(" ")[0];
};

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
function typing() {
  return addBubble("assistant", "<span></span><span></span><span></span>", "typing");
}

function renderReply(out) {
  if (out.status === "awaiting_confirm") return renderRoutine(out.routine);
  // tách disclaimer (sau dòng trống cuối) thành dòng nhỏ
  const parts = (out.reply || "").split(/\n\n(?=⚠️)/);
  addBubble("assistant", md(parts[0]));
  if (parts[1]) addBubble("assistant", md(parts[1]), "warn");
}

function renderRoutine(routine) {
  const rows = routine.exercises.map((e) =>
    `<div class="ex-row"><span>${e.name}</span><span class="meta">${e.sets}×${e.reps} · ${e.rest_sec}s</span></div>`
  ).join("");
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
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ conversation_id: CID, approved }),
  });
  t.remove();
  renderReply(out);
  if (approved) loaders.routines && (loaders._routinesDirty = true);
}

async function send(text) {
  addBubble("user", md(text));
  const t = typing();
  let out;
  try {
    out = await api("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: USER, conversation_id: CID, message: text }),
    });
  } catch (e) {
    out = { status: "ok", reply: "Lỗi kết nối tới server 😕" };
  }
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
  showScreen("coach");
  send(text);
}

// ---------- init ----------
function tick() {
  const d = new Date();
  document.getElementById("clock").textContent =
    `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
}
tick(); setInterval(tick, 30000);
loaders.profile();   // set tên cho home + profile
showScreen("home");
