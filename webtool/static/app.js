/* archi-render webtool — single-file UI, no build step, no CDN. */
"use strict";

/* ─────────────────────────── option vocabulary — OFFLINE FALLBACK.
   At boot the UI loads the live schema from GET /api/options (= prompt_compose.py --list-options) and
   rebuilds selects from its `values`/`options`; this constant is only used when that call fails.
   Keep in sync with 20-knowledge/stylepacks/OPTIONS.md. */
const GROUP_LABELS = { shot: "샷·카메라", materials: "재질", lighting: "조명", season: "계절·식생", entourage: "엔투라지 상세", context: "컨텍스트", grading: "그레이딩", other: "무드" };
const KEY_LABELS = { mood: "무드", lighting: "조명", sky: "하늘", interior_lights: "실내등", season_weather: "계절·날씨", vegetation_age: "식생 성숙도", camera: "카메라", tilt: "틸트", materials: "재질 프리셋", people_density: "인물 밀도", people_activity: "인물 동작", car_density: "차량 밀도", car_type: "차량 종류", context: "주변 맥락", material_wear: "재질 마모", tone: "톤", post: "후보정", lens_mm: "렌즈 mm", camera_height_m: "카메라 높이 m" };
const TOGGLE_LABELS = { people: "사람", cars: "차량", vegetation: "식재", furniture: "가구" };
/* collapsible sections: merged_into group → section id; fixed section (keep_fixed/aspect) lives in index.html */
const SECTION_OF = { other: "look", grading: "look", lighting: "light", season: "season", entourage: "people", shot: "camera", context: "context", materials: "context" };
const SECTION_LABELS = { look: "룩", light: "빛·하늘", season: "계절·식생", people: "사람·차", camera: "카메라", context: "맥락·재질", fixed: "고정" };
const SECTION_ORDER = ["look", "light", "season", "people", "camera", "context"];
const FALLBACK_GROUP = { mood: "other", lighting: "lighting", season_weather: "season", camera: "shot", materials: "materials", post: "grading" };
const SEC_STORE = "archi-render.sections";
const OPTIONS = {
  selects: [
    { key: "mood",           label: "무드",       values: ["photoreal", "cinematic", "clay", "watercolor", "diagram"] },
    { key: "lighting",       label: "조명",       values: ["overcast", "midday", "golden_hour", "dusk", "night", "blue_hour"] },
    { key: "season_weather", label: "계절·날씨",  values: ["spring", "summer", "autumn", "winter", "rain", "snow"] },
    { key: "camera",         label: "카메라",     values: ["eye_level", "elevated", "drone", "interior"] },
    { key: "materials",      label: "재질 프리셋", values: ["white_stucco_oak", "board_formed_concrete", "brick_dark_metal", "timber_glass", "clay_massing"] },
    { key: "post",           label: "후보정",     values: ["neutral", "teal_orange", "warm_film", "bw"] },
  ],
  toggles: [
    { key: "people", label: "사람" }, { key: "cars", label: "차량" },
    { key: "vegetation", label: "식재" }, { key: "furniture", label: "가구" },
  ],
  aspect: ["auto", "4:3", "16:9", "1:1", "2:1", "3:2"],
};

/* ─────────────────────────── state */
const S = {
  packs: [], pack: null, capture: null, captureUrl: null,
  revisions: [], current: null, busy: false,
  tool: "brush", brush: 40, undo: [], drawing: false, rectStart: null,
  schema: null, entourageTouched: false,   // schema = normalised option schema (live or fallback)
};
const $ = (id) => document.getElementById(id);
const els = {
  drop: $("dropzone"), file: $("file-input"), capImg: $("capture-preview"), capInfo: $("capture-info"),
  project: $("project"), shot: $("shot"), packGrid: $("pack-grid"), options: $("options"),
  keepFixed: $("keep_fixed"), aspect: $("aspect"), prompt: $("prompt-preview"),
  render: $("btn-render"), savePack: $("btn-save-pack"), renderStatus: $("render-status"),
  tabs: $("rev-tabs"), imgRender: $("img-render"), imgInput: $("img-input"), imgInputSide: $("img-input-side"),
  compareToggle: $("compare-toggle"), compareMode: $("compare-mode"), compareWrap: $("compare-wrap"),
  compareHandle: $("compare-handle"), sideInput: $("side-input"), stage: $("stage"), stageEmpty: $("stage-empty"),
  fixToggle: $("fix-toggle"), fixPanel: $("fix-panel"), canvas: $("mask-canvas"),
  brushSize: $("brush-size"), brushVal: $("brush-size-val"), fixInstr: $("fix-instruction"),
  fix: $("btn-fix"), fixStatus: $("fix-status"), revMeta: $("rev-meta"), toast: $("toast"), status: $("server-status"),
  reset: $("btn-reset"), random: $("btn-random"), promptStats: $("prompt-stats"),
};

/* ─────────────────────────── utilities */
async function api(path, body, method) {
  const opts = { method: method || (body ? "POST" : "GET"), headers: { "Content-Type": "application/json" } };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(path, opts);
  let data = null;
  try { data = await res.json(); } catch (_) { data = { error: `HTTP ${res.status}` }; }
  if (!res.ok) {
    const err = new Error(data.error || `HTTP ${res.status}`);
    err.detail = data; err.status = res.status;
    throw err;
  }
  return data;
}
function toast(msg, isErr) {
  els.toast.textContent = msg; els.toast.hidden = false; els.toast.classList.toggle("err", !!isErr);
  clearTimeout(toast.t); toast.t = setTimeout(() => (els.toast.hidden = true), isErr ? 6000 : 3000);
}
function setStatus(el, text, cls) { el.textContent = text || ""; el.className = "status" + (cls ? " " + cls : ""); }
function errText(e) {
  const d = e.detail || {};
  return [e.message, d.stderr, d.expected_path ? `expected: ${d.expected_path}` : ""].filter(Boolean).join("\n");
}
function debounce(fn, ms) { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; }
function ids() { return { project: els.project.value.trim(), shot: els.shot.value.trim() }; }
function esc(v) { return String(v ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])); }
function bust(url) { return url ? url + (url.includes("?") ? "&" : "?") + "t=" + Date.now() : ""; }

function collectOptions() {
  const o = {};
  for (const s of S.schema.selects) { const v = $("opt-" + s.key).value.trim(); if (v) o[s.key] = v; }
  if (S.entourageTouched)                                         // explicit on/off list, only once the user touched a toggle
    o.entourage = S.schema.toggles.map((t) => `${t.key}:${$("opt-" + t.key).checked ? "on" : "off"}`).join(",");
  const kf = els.keepFixed.value.split(/\r?\n/).map((l) => l.trim()).filter(Boolean);
  if (kf.length) o.keep_fixed = kf.join("; ");                    // prompt_compose: ';'-separated
  return o;
}
function backend() { return document.querySelector("input[name=backend]:checked").value; }

/* ─────────────────────────── packs + options UI */
async function loadPacks() {
  try {
    S.packs = await api("/api/packs");
    els.status.textContent = "서버 연결됨"; els.status.className = "pill ok";
  } catch (e) {
    els.status.textContent = "서버 오류"; els.status.className = "pill bad"; S.packs = [];
  }
  els.packGrid.innerHTML = "";
  if (!S.packs.length) {
    els.packGrid.innerHTML = '<div class="muted small">스타일 팩이 없습니다. <code>assets/stylepacks/&lt;id&gt;/pack.json</code>을 추가하면 여기에 나타납니다. 팩 없이도 옵션만으로 프롬프트 미리보기는 되지 않으며, 렌더에는 팩이 필요합니다.</div>';
    return;
  }
  for (const pk of S.packs) {
    const b = document.createElement("button"); b.className = "pack"; b.type = "button"; b.dataset.id = pk.id;
    b.innerHTML = `<div class="thumb">${pk.sample ? `<img src="${esc(pk.sample)}" alt="">` : "샘플 없음"}</div>
      <div class="name">${esc(pk.name)}</div><div class="mood">${esc(pk.mood)}</div>`;
    b.title = pk.id;
    b.addEventListener("click", () => selectPack(pk.id));
    els.packGrid.appendChild(b);
  }
  if (!S.pack) selectPack(S.packs[0].id);
}
function selectPack(id) {
  S.pack = id;
  document.querySelectorAll(".pack").forEach((el) => el.classList.toggle("active", el.dataset.id === id));
  const pk = S.packs.find((p) => p.id === id);
  if (pk) {           // pack slots pre-fill matching option selects
    if (pk.mood && $("opt-mood")) $("opt-mood").value = [...$("opt-mood").options].some((o) => o.value === pk.mood) ? pk.mood : "";
    S.entourageTouched = false;
    for (const [k, v] of Object.entries(pk.slots || {})) {
      if (k === "entourage") { const list = Array.isArray(v) ? v : String(v).split(","); S.schema.toggles.forEach((t) => ($("opt-" + t.key).checked = list.some((x) => String(x).trim().split(":")[0] === t.key))); continue; }
      const el = $("opt-" + k); if (!el) continue;
      if (el.type === "checkbox") el.checked = v === true || v === "on"; else if (el.tagName === "SELECT" && [...el.options].some((o) => o.value === v)) el.value = v;
    }
    applyRequires();
  }
  updateRenderButton(); composePreview();
}
function normaliseSchema(live) {
  if (!live || !live.values) {
    return { selects: OPTIONS.selects.map((x) => ({ ...x, group: FALLBACK_GROUP[x.key] || "other" })), toggles: OPTIONS.toggles, aspect: OPTIONS.aspect, live: false, sentences: null, maxSlots: 7 };
  }
  const meta = live.options || {}, selects = [];
  for (const [key, values] of Object.entries(live.values)) {
    if (key === "entourage" || key === "aspect") continue;
    selects.push({ key, label: KEY_LABELS[key] || key, values, group: (meta[key] || {}).merged_into || (key === "mood" ? "other" : key === "materials" ? "materials" : "other"),
                   requires: (meta[key] || {}).requires || null });
  }
  for (const [key, type] of Object.entries(live.free || {})) {      // numeric free keys become text inputs
    if (type === "int" || type === "float") selects.push({ key, label: KEY_LABELS[key] || key, values: null, group: (meta[key] || {}).merged_into || "other", free: type });
  }
  const order = ["other", ...(live.slots_order || []), "materials"];
  selects.sort((a, b) => order.indexOf(a.group) - order.indexOf(b.group));
  const toggles = ((meta.entourage || {}).values || live.values.entourage || OPTIONS.toggles.map((t) => t.key)).map((k) => ({ key: k, label: TOGGLE_LABELS[k] || k }));
  // sentences (optional, key → value → English sentence) become <option title>; absent = no tooltips
  return { selects, toggles, aspect: live.values.aspect || OPTIONS.aspect, live: true, sentences: live.sentences || null, maxSlots: live.max_slot_sentences || 7 };
}
function buildOptions(schema) {
  S.schema = schema; els.options.innerHTML = "";
  const frag = document.createDocumentFragment(), bodies = {};
  const groupsIn = {}; for (const s of schema.selects) (groupsIn[SECTION_OF[s.group] || "look"] ||= new Set()).add(s.group);
  const section = (id) => {
    if (bodies[id]) return bodies[id];
    const d = document.createElement("details"); d.className = "sec"; d.dataset.sec = id; d.open = true;
    const sm = document.createElement("summary"); sm.textContent = SECTION_LABELS[id] || id; d.appendChild(sm);
    const body = document.createElement("div"); body.className = "sec-body"; d.appendChild(body);
    frag.appendChild(d); return (bodies[id] = body);
  };
  for (const id of SECTION_ORDER) if (groupsIn[id]) section(id);            // fixed order regardless of schema order
  let group = null;
  for (const s of schema.selects) {
    const sec = SECTION_OF[s.group] || "look", body = section(sec);
    if (s.group !== group && schema.live && groupsIn[sec].size > 1) { const gt = document.createElement("div"); gt.className = "group-title"; gt.textContent = GROUP_LABELS[s.group] || s.group; body.appendChild(gt); }
    group = s.group;
    const l = document.createElement("label"); l.textContent = s.label; l.dataset.key = s.key;
    let ctl;
    if (s.free) { ctl = document.createElement("input"); ctl.type = "text"; ctl.placeholder = "(팩 기본값)"; ctl.inputMode = "decimal"; }
    else {
      const sent = (schema.sentences || {})[s.key] || {};
      ctl = document.createElement("select");
      ctl.innerHTML = `<option value="">(팩 기본값)</option>` + s.values.map((v) => `<option value="${esc(v)}"${sent[v] ? ` title="${esc(sent[v])}"` : ""}>${esc(v)}</option>`).join("");
    }
    ctl.id = "opt-" + s.key; l.appendChild(ctl); body.appendChild(l);
  }
  const tgBody = section("people");
  const gt = document.createElement("div"); gt.className = "group-title"; gt.textContent = "엔투라지 토글"; tgBody.appendChild(gt);
  const tg = document.createElement("div"); tg.className = "toggles";
  for (const t of schema.toggles) {
    const l = document.createElement("label"), cb = document.createElement("input"); cb.type = "checkbox"; cb.id = "opt-" + t.key;
    cb.addEventListener("change", () => { S.entourageTouched = true; applyRequires(); });
    l.appendChild(cb); l.appendChild(document.createTextNode(" " + t.label)); tg.appendChild(l);
  }
  tgBody.appendChild(tg); els.options.appendChild(frag);
  els.aspect.innerHTML = schema.aspect.map((a) => `<option value="${esc(a)}">${esc(a)}</option>`).join("");
  if (!els.aspect.value) els.aspect.value = "auto";
  applyRequires(); bindSections();
}
/* collapsible sections: restore open/closed from localStorage and persist on toggle */
function bindSections() {
  const saved = S.sections || (S.sections = (() => { try { return JSON.parse(localStorage.getItem(SEC_STORE) || "{}"); } catch (_) { return {}; } })());
  document.querySelectorAll("details.sec[data-sec]").forEach((d) => {
    if (d.dataset.sec in saved) d.open = !!saved[d.dataset.sec];
    if (d.dataset.bound) return; d.dataset.bound = "1";
    d.addEventListener("toggle", () => { saved[d.dataset.sec] = d.open; try { localStorage.setItem(SEC_STORE, JSON.stringify(saved)); } catch (_) {} });
  });
}
/* presets */
function resetOptions() {
  for (const s of S.schema.selects) $("opt-" + s.key).value = "";
  els.keepFixed.value = "";
  if (S.pack) selectPack(S.pack); else { S.entourageTouched = false; applyRequires(); }   // selectPack re-applies pack defaults + previews
  toast("팩 기본값으로 초기화");
}
function randomizeOptions() {
  const pick = (arr) => arr[Math.floor(Math.random() * arr.length)];
  for (const s of S.schema.selects) {
    if (s.free || !s.values || s.group === "shot" || s.key === "camera") continue;     // camera axes, aspect, keep_fixed untouched
    $("opt-" + s.key).value = pick(s.values);
    const m = s.requires && /^entourage\.(\w+)=on$/.exec(s.requires);
    if (m && $("opt-" + m[1]) && !$("opt-" + m[1]).checked) { $("opt-" + m[1]).checked = true; S.entourageTouched = true; }
  }
  applyRequires(); composePreview();
}
/* requires: "entourage.people=on" → disable the control while that toggle is off (composer ignores it anyway) */
function applyRequires() {
  for (const s of S.schema.selects) {
    if (!s.requires) continue;
    const m = /^entourage\.(\w+)=on$/.exec(s.requires); if (!m) continue;
    const on = $("opt-" + m[1])?.checked; const ctl = $("opt-" + s.key); ctl.disabled = !on; ctl.closest("label").style.opacity = on ? "" : ".45";
  }
}
async function loadOptionsSchema() {
  try { return normaliseSchema(await api("/api/options")); }
  catch (e) { toast("옵션 스키마를 서버에서 못 받아 내장 어휘로 동작합니다 (" + e.message + ")", true); return normaliseSchema(null); }
}
const composePreview = debounce(async () => {
  if (!S.pack) return;
  els.prompt.classList.add("stale");
  try {
    const r = await api("/api/compose", { pack: S.pack, options: collectOptions() });
    els.prompt.textContent = r.prompt || "(빈 프롬프트)";
    els.promptStats.textContent = promptStats(r);
  } catch (e) {
    els.prompt.textContent = (e.status === 503 ? "프롬프트 스크립트가 아직 없습니다.\n" : "프롬프트 생성 실패\n") + errText(e);
    els.promptStats.textContent = "";
  }
  els.prompt.classList.remove("stale");
}, 350);
/* "잠금 1 + 슬롯 N/7": from --json parts when /api/compose returns them (lock/slots arrays), else a client-side
   sentence count — split on ". ", drop the lock/negative/aspect sentences, treat the rest as slot sentences (≈). */
function promptStats(r) {
  const max = S.schema?.maxSlots || 7;
  if (Array.isArray(r.slots)) return `잠금 1 + 슬롯 ${r.slots.length}/${max}`;
  const sents = String(r.prompt || "").split(/\.\s+(?=[A-Z])/).map((x) => x.trim()).filter(Boolean);
  const slots = sents.filter((x) => !/^(Use the attached|Keep the |Do not add|Avoid:|Aspect ratio)/.test(x)).length;
  return `잠금 1 + 슬롯 ≈${slots}/${max}`;
}

/* ─────────────────────────── capture upload */
function bindDropzone() {
  els.drop.addEventListener("click", () => els.file.click());
  els.drop.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") els.file.click(); });
  els.file.addEventListener("change", () => els.file.files[0] && uploadCapture(els.file.files[0]));
  ["dragenter", "dragover"].forEach((ev) => els.drop.addEventListener(ev, (e) => { e.preventDefault(); els.drop.classList.add("over"); }));
  ["dragleave", "drop"].forEach((ev) => els.drop.addEventListener(ev, (e) => { e.preventDefault(); els.drop.classList.remove("over"); }));
  els.drop.addEventListener("drop", (e) => { const f = e.dataTransfer.files[0]; if (f) uploadCapture(f); });
  [els.project, els.shot].forEach((el) => el.addEventListener("change", () => { loadRevisions(); }));
}
async function uploadCapture(file) {
  const { project, shot } = ids();
  if (!project || !shot) return toast("프로젝트/샷을 먼저 입력하세요", true);
  if (!/^image\/(png|jpeg|webp)$/.test(file.type)) return toast("PNG · JPG · WebP만 지원합니다", true);
  const dataUrl = await new Promise((res, rej) => { const r = new FileReader(); r.onload = () => res(r.result); r.onerror = rej; r.readAsDataURL(file); });
  els.capImg.src = dataUrl; els.capImg.hidden = false; els.drop.classList.add("has-image");
  try {
    const r = await api("/api/upload", { project, shot, data: dataUrl, ext: file.name.split(".").pop().toLowerCase() });
    S.capture = r.path; S.captureUrl = r.url;
    els.capInfo.textContent = `${r.path} · ${(r.size / 1024).toFixed(0)} KB`;
    toast("캡처 저장됨"); updateRenderButton(); loadRevisions();
  } catch (e) { toast("업로드 실패: " + errText(e), true); }
}
function updateRenderButton() { els.render.disabled = !(S.pack && S.capture) || S.busy; }

/* ─────────────────────────── render + revisions */
async function doRender() {
  const { project, shot } = ids();
  S.busy = true; updateRenderButton();
  const t0 = Date.now();
  setStatus(els.renderStatus, `렌더 중… (${backend()}) 보통 30초~2분, 최대 10분`, "busy");
  const tick = setInterval(() => (els.renderStatus.textContent = `렌더 중… (${backend()}) ${Math.round((Date.now() - t0) / 1000)}s`), 1000);
  try {
    const r = await api("/api/render", { project, shot, pack: S.pack, options: collectOptions(), backend: backend(), aspect: els.aspect.value });
    setStatus(els.renderStatus, `${r.revision} 완료 · ${r.elapsed_s}s · ${r.backend}`, "ok");
    await loadRevisions(r.revision);
  } catch (e) { setStatus(els.renderStatus, "렌더 실패: " + errText(e), "err"); }
  clearInterval(tick); S.busy = false; updateRenderButton();
}
async function loadRevisions(select) {
  const { project, shot } = ids(); if (!project || !shot) return;
  try {
    const r = await api(`/api/revisions?project=${encodeURIComponent(project)}&shot=${encodeURIComponent(shot)}`);
    S.revisions = r.revisions;
    if (r.capture && !S.captureUrl) { S.captureUrl = r.capture; S.capture = r.capture.slice(1); els.capImg.src = r.capture; els.capImg.hidden = false; els.drop.classList.add("has-image"); els.capInfo.textContent = r.capture.slice(1); updateRenderButton(); }
    renderTabs();
    const want = select || (S.revisions.some((x) => x.revision === S.current) ? S.current : S.revisions.at(-1)?.revision);
    showRevision(want || null);
  } catch (e) { toast("리비전 조회 실패: " + errText(e), true); }
}
function renderTabs() {
  els.tabs.innerHTML = S.revisions.length ? "" : '<span class="muted small">리비전 없음</span>';
  for (const rv of S.revisions) {
    const b = document.createElement("button"); b.className = "tab" + (rv.revision === S.current ? " active" : "");
    b.innerHTML = rv.revision + (rv.meta?.mode === "fix" || rv.meta?.base ? '<span class="fixmark">fix</span>' : "");
    b.addEventListener("click", () => showRevision(rv.revision)); els.tabs.appendChild(b);
  }
}
function showRevision(rev) {
  S.current = rev; const rv = S.revisions.find((x) => x.revision === rev);
  document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("active", t.textContent.startsWith(rev || "")));
  els.stageEmpty.hidden = !!rv;
  if (!rv) { els.imgRender.removeAttribute("src"); els.imgRender.style.display = "none"; els.revMeta.textContent = ""; return; }
  els.imgRender.style.display = ""; els.imgRender.src = bust(rv.url);
  const m = rv.meta || {};
  els.revMeta.innerHTML = [`<span>${rv.revision}</span>`, m.backend && `<span>backend ${esc(m.backend)}</span>`, m.elapsed_s && `<span>${m.elapsed_s}s</span>`,
    m.base && `<span>base ${esc(m.base)}</span>`, m.created && `<span>${esc(m.created)}</span>`, rv.masks?.length && `<span>masks ${rv.masks.length}</span>`,
    m.prompt && `<span class="prompt-line">${esc(String(m.prompt).slice(0, 600))}</span>`].filter(Boolean).join("");
  els.imgRender.onload = () => { layoutCompare(); if (!els.fixToggle.checked) return; resetMask(); layoutCanvas(); };
  if (S.captureUrl) { els.imgInput.src = bust(S.captureUrl); els.imgInputSide.src = bust(S.captureUrl); }
}

/* ─────────────────────────── compare */
function bindCompare() {
  els.compareToggle.addEventListener("change", applyCompare);
  els.compareMode.addEventListener("change", applyCompare);
  let drag = false;
  els.stage.addEventListener("pointerdown", (e) => { if (els.compareToggle.checked && els.compareMode.value === "slider" && !els.fixToggle.checked) { drag = true; moveSlider(e); } });
  window.addEventListener("pointermove", (e) => drag && moveSlider(e));
  window.addEventListener("pointerup", () => (drag = false));
  window.addEventListener("resize", () => { layoutCompare(); layoutCanvas(); });
}
function applyCompare() {
  const on = els.compareToggle.checked, mode = els.compareMode.value;
  els.compareMode.disabled = !on;
  els.compareWrap.hidden = !(on && mode === "slider");
  els.sideInput.hidden = !(on && mode === "side");
  if (on && els.fixToggle.checked && mode === "slider") { els.fixToggle.checked = false; applyFixMode(); }
  layoutCompare();
}
function layoutCompare() {
  if (els.compareWrap.hidden) return;
  const r = els.imgRender.getBoundingClientRect(), s = els.stage.getBoundingClientRect();
  Object.assign(els.compareWrap.style, { left: r.left - s.left + "px", top: r.top - s.top + "px", height: r.height + "px" });
  Object.assign(els.imgInput.style, { width: r.width + "px", height: r.height + "px" });
  if (!els.compareWrap.dataset.w) els.compareWrap.style.width = r.width / 2 + "px";
}
function moveSlider(e) {
  const r = els.imgRender.getBoundingClientRect();
  const w = Math.max(0, Math.min(r.width, e.clientX - r.left));
  els.compareWrap.style.width = w + "px"; els.compareWrap.dataset.w = "1";
}

/* ─────────────────────────── fix mode: mask canvas (native-resolution source of truth) */
const mask = { off: document.createElement("canvas"), ctx: null };  // offscreen, natural size, white strokes on transparent
function resetMask() {
  const img = els.imgRender;
  mask.off.width = img.naturalWidth || 1; mask.off.height = img.naturalHeight || 1;
  mask.ctx = mask.off.getContext("2d"); mask.ctx.clearRect(0, 0, mask.off.width, mask.off.height);
  S.undo = []; paintDisplay();
}
function layoutCanvas() {
  if (els.canvas.hidden) return;
  const r = els.imgRender.getBoundingClientRect(), s = els.stage.getBoundingClientRect();
  els.canvas.width = Math.round(r.width); els.canvas.height = Math.round(r.height);
  Object.assign(els.canvas.style, { left: r.left - s.left + "px", top: r.top - s.top + "px", width: r.width + "px", height: r.height + "px" });
  paintDisplay();
}
function paintDisplay(previewRect) {
  const c = els.canvas.getContext("2d"); c.clearRect(0, 0, els.canvas.width, els.canvas.height);
  c.globalAlpha = 0.5; c.drawImage(mask.off, 0, 0, els.canvas.width, els.canvas.height); c.globalAlpha = 1;
  // tint: multiply white strokes to accent
  c.globalCompositeOperation = "source-in"; c.fillStyle = "#e0a458"; c.fillRect(0, 0, els.canvas.width, els.canvas.height);
  c.globalCompositeOperation = "source-over";
  if (previewRect) { c.strokeStyle = "#e0a458"; c.setLineDash([6, 4]); c.lineWidth = 1.5; c.strokeRect(...previewRect); c.setLineDash([]); }
}
function toNative(e) {
  const r = els.canvas.getBoundingClientRect();
  return [(e.clientX - r.left) * (mask.off.width / r.width), (e.clientY - r.top) * (mask.off.height / r.height)];
}
function pushUndo() { S.undo.push(mask.ctx.getImageData(0, 0, mask.off.width, mask.off.height)); if (S.undo.length > 25) S.undo.shift(); }
function undo() { const im = S.undo.pop(); if (im) { mask.ctx.putImageData(im, 0, 0); paintDisplay(); } }
function strokeTo(x, y, fromX, fromY) {
  const ctx = mask.ctx, scale = mask.off.width / els.canvas.getBoundingClientRect().width;
  ctx.globalCompositeOperation = S.tool === "eraser" ? "destination-out" : "source-over";
  ctx.strokeStyle = ctx.fillStyle = "#fff"; ctx.lineCap = ctx.lineJoin = "round"; ctx.lineWidth = S.brush * scale;
  ctx.beginPath(); ctx.moveTo(fromX, fromY); ctx.lineTo(x, y); ctx.stroke();
  ctx.globalCompositeOperation = "source-over";
}
function bindCanvas() {
  let last = null;
  els.canvas.addEventListener("pointerdown", (e) => {
    e.preventDefault(); els.canvas.setPointerCapture(e.pointerId); pushUndo(); S.drawing = true;
    const [x, y] = toNative(e); last = [x, y];
    if (S.tool === "rect") S.rectStart = [e.clientX, e.clientY, x, y]; else { strokeTo(x, y, x, y); paintDisplay(); }
  });
  els.canvas.addEventListener("pointermove", (e) => {
    if (!S.drawing) return;
    const [x, y] = toNative(e);
    if (S.tool === "rect") {
      const r = els.canvas.getBoundingClientRect(), [sx, sy] = S.rectStart;
      paintDisplay([sx - r.left, sy - r.top, e.clientX - sx, e.clientY - sy]);
    } else { strokeTo(x, y, last[0], last[1]); last = [x, y]; paintDisplay(); }
  });
  const end = (e) => {
    if (!S.drawing) return; S.drawing = false;
    if (S.tool === "rect" && S.rectStart) {
      const [, , x0, y0] = S.rectStart, [x1, y1] = toNative(e);
      mask.ctx.fillStyle = "#fff"; mask.ctx.fillRect(Math.min(x0, x1), Math.min(y0, y1), Math.abs(x1 - x0), Math.abs(y1 - y0));
      S.rectStart = null; paintDisplay();
    }
  };
  els.canvas.addEventListener("pointerup", end); els.canvas.addEventListener("pointercancel", end);
  document.querySelectorAll(".tool").forEach((b) => b.addEventListener("click", () => setTool(b.dataset.tool)));
  els.brushSize.addEventListener("input", () => { S.brush = +els.brushSize.value; els.brushVal.textContent = S.brush; });
  $("btn-undo").addEventListener("click", undo);
  $("btn-clear").addEventListener("click", () => { pushUndo(); mask.ctx.clearRect(0, 0, mask.off.width, mask.off.height); paintDisplay(); });
  els.fixToggle.addEventListener("change", applyFixMode);
  els.fix.addEventListener("click", doFix);
  window.addEventListener("keydown", (e) => {
    if (e.target.matches("input:not([type=checkbox]):not([type=radio]):not([type=range]), textarea, select") || e.metaKey || e.ctrlKey) return;
    const k = e.key.toLowerCase();
    if (k === "b") setTool("brush"); else if (k === "e") setTool("eraser"); else if (k === "z") undo();
  });
}
function setTool(t) {
  S.tool = t; document.querySelectorAll(".tool").forEach((b) => b.classList.toggle("active", b.dataset.tool === t));
  els.canvas.className = "mask-canvas " + t;
}
function applyFixMode() {
  const on = els.fixToggle.checked && !!S.current;
  if (els.fixToggle.checked && !S.current) { els.fixToggle.checked = false; return toast("먼저 렌더 결과가 있어야 Fix 모드를 켤 수 있습니다", true); }
  els.fixPanel.hidden = !on; els.canvas.hidden = !on;
  if (on) { if (els.compareToggle.checked && els.compareMode.value === "slider") { els.compareToggle.checked = false; applyCompare(); } resetMask(); layoutCanvas(); }
}
/* Export: grayscale PNG at native render resolution; 255 = editable region, 0 = keep. Alpha is thresholded to hard 0/255. */
function exportMaskPNG() {
  const w = mask.off.width, h = mask.off.height, out = document.createElement("canvas"); out.width = w; out.height = h;
  const c = out.getContext("2d"); c.fillStyle = "#000"; c.fillRect(0, 0, w, h); c.drawImage(mask.off, 0, 0);
  const im = c.getImageData(0, 0, w, h), d = im.data; let count = 0;
  for (let i = 0; i < d.length; i += 4) { const v = d[i] > 127 ? 255 : 0; d[i] = d[i + 1] = d[i + 2] = v; d[i + 3] = 255; if (v) count++; }
  c.putImageData(im, 0, 0);
  return { dataUrl: out.toDataURL("image/png"), coverage: count / (w * h), w, h };
}
async function doFix() {
  const instr = els.fixInstr.value.trim();
  if (!instr) return toast("수정 지시문을 입력하세요", true);
  const m = exportMaskPNG();
  if (m.coverage === 0) return toast("수정 영역을 먼저 칠하세요", true);
  const { project, shot } = ids(); S.busy = true; els.fix.disabled = true;
  setStatus(els.fixStatus, `영역 수정 중… 마스크 ${m.w}×${m.h}, 영역 ${(m.coverage * 100).toFixed(1)}% (grok)`, "busy");
  try {
    const r = await api("/api/fix", { project, shot, base: S.current, mask_png_base64: m.dataUrl, instruction: instr, backend: "grok" });
    setStatus(els.fixStatus, `${r.revision} 생성 · ${r.elapsed_s}s · 마스크 ${r.mask}`, "ok");
    await loadRevisions(r.revision);
  } catch (e) { setStatus(els.fixStatus, "수정 실패: " + errText(e), "err"); }
  S.busy = false; els.fix.disabled = false;
}

/* ─────────────────────────── save as pack */
async function savePack() {
  const id = prompt("팩 ID (영문·숫자·-·_ · 'custom-' 접두는 자동)");
  if (!id) return;
  if (!/^[A-Za-z0-9_-]{1,40}$/.test(id)) return toast("ID 형식이 올바르지 않습니다", true);
  const name = prompt("팩 표시 이름", id) || id;
  try {
    const r = await api("/api/pack/save", { id, name, options: collectOptions() });
    toast(`저장됨: ${r.path}`); await loadPacks(); selectPack(r.id);
  } catch (e) { toast("팩 저장 실패: " + errText(e), true); }
}

/* ─────────────────────────── boot */
bindDropzone(); bindCompare(); bindCanvas();
els.render.addEventListener("click", doRender);
els.savePack.addEventListener("click", savePack);
els.options.addEventListener("change", composePreview); els.options.addEventListener("input", debounce(composePreview, 300));
els.keepFixed.addEventListener("input", composePreview);
els.reset.addEventListener("click", resetOptions); els.random.addEventListener("click", randomizeOptions);
els.options.addEventListener("change", (e) => { if (e.target.tagName === "SELECT") e.target.title = e.target.selectedOptions[0]?.title || ""; });  // hover help on the closed select
bindSections();
loadOptionsSchema().then((schema) => { buildOptions(schema); return loadPacks(); }).then(loadRevisions);
