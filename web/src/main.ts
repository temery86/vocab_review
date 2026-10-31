// Screens 1 to 6 of section 5, with the register card and curation answers of sections 12.2 and 12.7.

import { createClient } from "@supabase/supabase-js";
import "./style.css";
import { type Answer, type Api, type Item, SupabaseApi } from "./api";
import macroscopeColour from "./brand/logos/macroscope-colour.png";
import macroscopeWhite from "./brand/logos/macroscope-white.png";
import sshocColour from "./brand/logos/sshoc-nl-colour.png";
import sshocWhite from "./brand/logos/sshoc-nl-white.png";
import { BRIEF, CONTEXT_LABELS, GRADES, PROVENANCE, SITE, SUPPORT, VOCAB_NAME, type Vocab } from "./config";
import { DemoApi } from "./demo";

const URL_ = import.meta.env.VITE_SUPABASE_URL as string | undefined;
const ANON = import.meta.env.VITE_SUPABASE_ANON_KEY as string | undefined;
const wantDemo = new URLSearchParams(location.search).has("demo") || !URL_ || !ANON;
const api: Api = wantDemo ? new DemoApi() : new SupabaseApi(createClient(URL_!, ANON!, { auth: { persistSession: true } }));

const $ = <T extends HTMLElement = HTMLElement>(s: string, r: ParentNode = document) => r.querySelector(s) as T;
const main = $("#main");
const esc = (v: unknown) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]!);
const store = {
  get<T>(k: string, d: T): T { try { const v = localStorage.getItem(k); return v === null ? d : (JSON.parse(v) as T); } catch { return d; } },
  set(k: string, v: unknown) { try { localStorage.setItem(k, JSON.stringify(v)); } catch { /* private window */ } },
};

document.title = SITE.title;
$("#brand").textContent = SITE.title;
{
  const t = store.get<string | null>("vr-theme", null);
  if (t) document.documentElement.dataset.theme = t;
  $("#theme").onclick = () => {
    const r = document.documentElement;
    const dark = r.dataset.theme ? r.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
    r.dataset.theme = dark ? "light" : "dark";
    store.set("vr-theme", r.dataset.theme);
  };
}

// SSHOC-NL first, 32 px apart, colour on light and white on dark (STYLE.md 5).
function logos() {
  const one = (name: string, url: string, colour: string, white: string) => {
    const imgs = `<img class="logo-light" src="${colour}" alt=""><img class="logo-dark" src="${white}" alt="">`;
    return url ? `<a href="${esc(url)}" aria-label="${name}">${imgs}</a>` : `<span role="img" aria-label="${name}">${imgs}</span>`;
  };
  return `<div class="supporters"><p class="line">${esc(SUPPORT.line)}</p><div class="logos">${one("SSHOC-NL", SUPPORT.sshocUrl, sshocColour, sshocWhite)}${one("Macroscope", SUPPORT.macroscopeUrl, macroscopeColour, macroscopeWhite)}</div></div>`;
}

// The footer carries the logos on every page except the review screen, which has no logos (STYLE.md 5), and the sign
// in screen, which shows them below the form.
function render(html: string, title: string, footer = true) {
  const foot = $("#foot");
  foot.hidden = !footer;
  foot.innerHTML = footer ? logos() : "";
  main.classList.remove("fade"); void main.offsetWidth; main.classList.add("fade");
  main.innerHTML = (api.demo ? `<p class="demo" role="note">Demo mode with fictional data. Sign in as alice@example.org or owner@example.org with code 123456.</p>` : "") + html;
  document.title = `${title} · ${SITE.title}`;
  main.focus({ preventScroll: true });
  scrollTo(0, 0);
}

let keyHandler: ((e: KeyboardEvent) => void) | null = null;
addEventListener("keydown", (e) => {
  const t = e.target as HTMLElement;
  if (["INPUT", "TEXTAREA", "SELECT"].includes(t.tagName) || e.metaKey || e.ctrlKey || e.altKey) return;
  keyHandler?.(e);
});

// 1. Sign in
function viewSignIn(msg = "") {
  keyHandler = null;
  render(`<section class="narrow">
    <h1>Sign in</h1>
    <p>${esc(SITE.title)} is a small expert review of vocabularies that link ${esc(VOCAB_NAME.scv)} and ${esc(VOCAB_NAME.rvv)} across European data, run by ${esc(SITE.runBy)}.</p>
    <p class="muted">Your answers are used to measure how accurate the vocabularies are and to correct them. <a href="#/privacy">Privacy note</a></p>
    <form id="f1" class="stack">
      <label for="email">Email address</label>
      <input id="email" type="email" autocomplete="email" required>
      <button type="submit">Send me a code</button>
    </form>
    <form id="f2" class="stack" hidden>
      <label for="code">Code from the email</label>
      <input id="code" inputmode="numeric" autocomplete="one-time-code" pattern="[0-9]{6,10}" maxlength="10" required>
      <button type="submit">Sign in</button>
    </form>
    <p id="msg" role="status" class="${msg ? "warn" : "muted"}">${esc(msg)}</p>
    <div class="signin-logos">${logos()}</div></section>`, "Sign in", false);
  const email = $<HTMLInputElement>("#email");
  email.focus();
  $("#f1").onsubmit = async (e) => {
    e.preventDefault();
    await api.start(email.value.trim().toLowerCase()).catch(() => undefined);
    $("#f2").hidden = false;
    $("#msg").textContent = "If this address is registered for the review, a code is on its way. It can take a minute.";
    $<HTMLInputElement>("#code").focus();
  };
  $("#f2").onsubmit = async (e) => {
    e.preventDefault();
    const ok = await api.verify(email.value.trim().toLowerCase(), $<HTMLInputElement>("#code").value.replace(/\s/g, "")).catch(() => false);
    if (ok) location.hash = "#/"; else { $("#msg").textContent = "That code did not work. Check it, or ask for a new one."; $("#msg").className = "warn"; }
    if (ok) route();
  };
}

function viewPrivacy() {
  keyHandler = null;
  render(`<section class="narrow"><h1>Privacy note</h1>
    <p>This review is run by ${esc(SITE.runBy)}, which decides how your data are used.</p>
    <p>It stores your name, email address, affiliation and areas of expertise, the batches you are given, every answer you give with the time it was given, and your comments.</p>
    <p>The data are held by Supabase in the European Union (Frankfurt). They are kept until the review project ends and for at most five years.</p>
    <p>Answers are analysed under a pseudonym. Comments may be quoted without attribution in publications. You are named in acknowledgements only if you agree.</p>
    <p>You can ask for your data to be deleted at any time, and the project removes them by hand.</p>
    <p><a href="#/">Back</a></p></section>`, "Privacy note");
}

// 2. Home
async function viewHome() {
  keyHandler = null;
  let me;
  try { me = await api.me(); }
  catch (e) { return render(`<section class="narrow"><h1>Something is not working</h1><p class="notice">${esc((e as Error).message)} You are signed in, so this is not about your address. Please let the project know.</p></section>`, "Not available"); }
  if (!me) return viewSignIn(await api.signedIn() ? "This address is not registered for the review." : "");
  $("#who").textContent = `${me.name}${me.role === "owner" ? " · owner" : ""}`;
  const bs = await api.batches();
  const open = bs.filter((b) => b.status === "open"), done = bs.filter((b) => b.status === "closed");
  render(`<h1>Your batches</h1>
    ${open.length ? `<ul class="cards">${open.map((b) => `<li class="card row"><div class="grow"><h2 class="h3">${esc(b.description || b.batch_id)}</h2>
      <p class="muted small">${esc(VOCAB_NAME[b.vocabulary])}${b.kind === "curation" ? ", curation" : ""} · ${b.answered} of ${b.items} answered</p>
      <div class="bar" role="progressbar" aria-label="Progress" aria-valuemin="0" aria-valuemax="${b.items}" aria-valuenow="${b.answered}"><span style="width:${b.items ? (100 * b.answered) / b.items : 0}%"></span></div></div>
      <a class="button" href="#/b/${esc(b.batch_id)}">${b.answered ? "Resume" : "Start"}</a></li>`).join("")}</ul>` : `<p class="muted">No open batches at the moment.</p>`}
    ${done.length ? `<h2>Completed</h2><ul class="plain">${done.map((b) => `<li>${esc(b.description || b.batch_id)} <span class="muted small">${b.answered} of ${b.items}</span></li>`).join("")}</ul>` : ""}
    <p class="small">${me.role === "owner" ? `<a href="#/admin">Admin</a> · ` : ""}<a href="#/privacy">Privacy note</a> · <a href="#" id="out">Sign out</a></p>`, "Your batches");
  $("#out").onclick = async (e) => { e.preventDefault(); await api.signOut(); $("#who").textContent = ""; location.hash = "#/"; route(); };
}

// 3. Brief
function viewBrief(batchId: string, vocab: Vocab, kind: string, n: number) {
  keyHandler = (e) => { if (e.key === "Enter") go(); };
  const b = BRIEF[vocab];
  const go = () => { store.set(`vr-brief-${batchId}`, true); location.hash = `#/b/${batchId}/1`; };
  render(`<section class="narrow"><h1>Before you start</h1>
    <h2 class="sub">What a construct is</h2><p>${esc(b.what)}</p>
    <h2 class="sub">What you will see</h2><p>${esc(b.item)}</p>
    ${kind === "curation" ? `<h2 class="sub">What you are asked</h2><p>This is a curation batch. For each variable, say whether it belongs to the construct shown, belongs in one of the neighbouring constructs, or should be rejected. For a note about several members, answer for each member named.</p>` :
      `<h2 class="sub">What you are asked</h2><p>For each item you say whether it belongs to the construct. Where the item has been compared with another item of the same construct, you also say whether the comparison grade is right.</p>
    <h2 class="sub">The grades</h2>
    <dl class="grades">${Object.entries(GRADES[vocab]).map(([g, m]) => `<dt>${g[0].toUpperCase() + g.slice(1)}</dt><dd>${esc(m)} <span class="muted">For example, ${esc(b.examples[g][0].toLowerCase() + b.examples[g].slice(1))}</span></dd>`).join("")}</dl>`}
    <h2 class="sub">Time and answers</h2>
    <p>${n} items, about ${Math.max(5, Math.round((15 * n) / 25))} minutes. Unsure is a valid answer. Every answer is saved as you give it, so you can stop and come back.</p>
    <h2 class="sub">Keys</h2><p class="muted small">Y, N and U answer the question shown, 1 to 5 pick a neighbour, Enter goes on, Backspace goes back.</p>
    <button id="go">Begin</button></section>`, "Before you start");
  $("#go").onclick = go;
}

// 4. Review item
const catList = (cs: Item["response_categories"]) => cs && cs.length ? `<ul class="cats">${cs.slice(0, 40).map((c) => `<li><span class="code">${esc(c.code)}</span> ${esc(c.label)}</li>`).join("")}${cs.length > 40 ? `<li class="muted">${cs.length - 40} more</li>` : ""}</ul>` : "";

function constructCard(i: Item) {
  return `<article class="card" aria-labelledby="ct"><p class="eyebrow">Construct</p><h2 id="ct" class="h3">${esc(i.construct_label)}</h2>
    <p>${esc(i.construct_definition)}</p>${i.construct_exclusions ? `<p class="muted">${esc(i.construct_exclusions)}</p>` : ""}
    ${i.construct_definition_provenance ? `<p class="provenance">${esc(PROVENANCE[i.construct_definition_provenance] ?? i.construct_definition_provenance)}</p>` : ""}</article>`;
}

function itemCard(i: Item) {
  if (i.vocabulary === "rvv") {
    const c = i.context || {};
    const rows = CONTEXT_LABELS.rvv.filter(([k]) => c[k] !== null && c[k] !== undefined && c[k] !== "").map(([k, lab]) => {
      const v = Array.isArray(c[k]) ? (c[k] as unknown[]).join(", ") : c[k];
      return `<dt>${esc(lab)}</dt><dd${k === "variable_name" ? ' class="mono"' : ""}>${esc(v)}</dd>`;
    });
    return `<article class="card" aria-labelledby="it"><p class="eyebrow">Register variable</p><h2 id="it" class="h3">${esc(c.label_en || c.label || i.measure_pid)}</h2><dl class="kv">${rows.join("")}</dl>${itemFoot(i)}</article>`;
  }
  return `<article class="card" aria-labelledby="it"><p class="eyebrow">Survey question</p><h2 id="it" class="h3">${esc(i.programme)}</h2>
    <p class="muted small">${esc(i.waves)}</p><p class="q">${esc(i.question_text || "(no question text held)")}</p>
    ${i.question_text_en && i.question_text_en !== i.question_text ? `<p class="muted">${esc(i.question_text_en)}</p>` : ""}
    ${catList(i.response_categories)}${i.universe_text ? `<p class="small"><span class="muted">Asked of</span> ${esc(i.universe_text)}</p>` : ""}${itemFoot(i)}</article>`;
}

function itemFoot(i: Item) {
  return `<p class="provenance"><span class="mono">${esc(i.measure_pid)}</span> · ${esc(i.export_version)}${i.method && i.method !== "not_graded" ? ` · graded by ${esc(i.method.replace(/_/g, " "))}` : ""}</p>`;
}

function anchorCard(i: Item) {
  return `<article class="card compact" aria-labelledby="an"><p class="eyebrow" id="an">Compared with</p><p>${esc(i.anchor_question_text)}</p>${catList(i.anchor_response_categories)}</article>`;
}

function reasonsList(i: Item) {
  const r = (i.grade_reasons || {}) as Record<string, any>;
  const parts: string[] = [];
  if (Array.isArray(r.differs) && r.differs.length) parts.push("Differs in " + r.differs.join(", ").replace(/_/g, " "));
  if (r.reason) parts.push(String(r.reason));
  if (r.recode) parts.push("Recode " + String(r.recode));
  if (r.attributes) parts.push(...Object.entries(r.attributes).map(([k, v]) => `${k} ${v}`));
  return parts.length ? `<ul class="reasons">${parts.map((p) => `<li>${esc(p)}</li>`).join("")}</ul>` : "";
}

async function viewItem(batchId: string, pos: number) {
  const items = await api.items(batchId);
  if (!items.length) return viewHome();
  const i = items.find((x) => x.position === pos) ?? items[0];
  const idx = items.indexOf(i);
  const answers = await api.answers(batchId);
  const a: Answer = { ...(answers.get(i.assignment_id) ?? {}), assignment_id: i.assignment_id };
  const shownAt = Date.now();
  const vocab = i.vocabulary as Vocab;
  const curation = i.queue;
  const graded = !curation && !!i.grade && !!i.anchor_measure_pid && i.anchor_measure_pid !== i.measure_pid;
  const save = async (patch: Partial<Answer>) => {
    Object.assign(a, patch, { seconds_on_item: Math.round((Date.now() - shownAt) / 1000) });
    const clean: Answer = { assignment_id: a.assignment_id };
    for (const k of ["belongs", "better_construct_pid", "better_construct_text", "reject_reason", "member_answers", "grade_ok", "correct_grade", "comment", "seconds_on_item"] as const)
      if (a[k] !== undefined) (clean as any)[k] = a[k];
    $("#saved").textContent = "Saving";
    try { await api.save(clean); $("#saved").textContent = "Saved"; $("#saved").classList.remove("warn"); }
    catch { $("#saved").textContent = "Not saved. Check your connection and answer again."; $("#saved").classList.add("warn"); }
    draw();
  };
  const next = () => { if (idx + 1 < items.length) location.hash = `#/b/${batchId}/${items[idx + 1].position}`; else location.hash = `#/b/${batchId}/end`; };
  const back = () => { if (idx > 0) location.hash = `#/b/${batchId}/${items[idx - 1].position}`; };

  render(`<div class="progress"><span>Item ${idx + 1} of ${items.length}</span><div class="bar" role="progressbar" aria-label="Position in batch" aria-valuemin="1" aria-valuemax="${items.length}" aria-valuenow="${idx + 1}"><span style="width:${(100 * (idx + 1)) / items.length}%"></span></div><span id="saved" class="saved" aria-live="polite"></span></div>
    <div class="pair">${curation === "membership" ? "" : itemCard(i)}${constructCard(i)}</div>
    ${graded ? anchorCard(i) : ""}<div id="qs"></div>
    <details class="comment"><summary>Add a comment</summary><label for="cm" class="sr">Comment</label><textarea id="cm" rows="3">${esc(a.comment)}</textarea></details>
    <nav class="row nav" aria-label="Items"><button class="ghost" id="back" ${idx === 0 ? "disabled" : ""}>Back</button><span class="grow"></span><button id="next">${idx + 1 < items.length ? "Next item" : "Finish"}</button></nav>`,
    `Item ${idx + 1}`, false);
  $("#back").onclick = back;
  $("#next").onclick = next;
  $<HTMLTextAreaElement>("#cm").onchange = (e) => save({ comment: (e.target as HTMLTextAreaElement).value });

  function btn(name: string, val: string, cur: unknown, label: string, key?: string) {
    return `<button type="button" class="choice${cur === val ? " on" : ""}" data-q="${name}" data-v="${esc(val)}" aria-pressed="${cur === val}">${key ? `<kbd>${key}</kbd> ` : ""}${esc(label)}</button>`;
  }
  function neighbours(cur: string | null | undefined) {
    return `<fieldset class="nb"><legend>Which construct does it belong to instead?</legend>${i.neighbour_constructs.map((n, k) =>
      btn("nb", n.pid, cur, n.label, String(k + 1))).join("")}
      <label for="none" class="small">None of these. What is it?</label><input id="none" value="${esc(a.better_construct_text)}"></fieldset>`;
  }

  function draw() {
    const q = $("#qs");
    if (curation === "membership") {
      const c = i.curation || {};
      const ma = (a.member_answers || {}) as Record<string, any>;
      const named = new Set<string>(c.named_members || []);
      const members: any[] = c.members || [];
      const ask = members.filter((m) => named.size === 0 || named.has(m.pid));
      const rest = members.filter((m) => named.size && !named.has(m.pid));
      q.innerHTML = `<article class="card"><p class="eyebrow">Note</p><p>${esc(c.note)}</p></article>
        <h2 class="h3">${named.size ? "Members named in the note" : "Members"}</h2>
        <ul class="members">${ask.map((m) => `<li><div><span class="mono small">${esc(m.pid)}</span> ${esc(m.label_en || m.label)} <span class="muted small">${esc(m.country)}</span></div>
          <div class="row wrap">${["stay", "move", "reject"].map((v) => `<button type="button" class="choice${ma[m.pid]?.answer === v ? " on" : ""}" data-m="${esc(m.pid)}" data-v="${v}" aria-pressed="${ma[m.pid]?.answer === v}">${v}</button>`).join("")}
          ${ma[m.pid]?.answer === "move" ? `<label class="sr" for="t-${esc(m.pid)}">Move to</label><select id="t-${esc(m.pid)}" data-t="${esc(m.pid)}"><option value="">Move to</option>${i.neighbour_constructs.map((n) => `<option value="${esc(n.pid)}" ${ma[m.pid]?.target === n.pid ? "selected" : ""}>${esc(n.label)}</option>`).join("")}</select>` : ""}
          ${ma[m.pid]?.answer === "reject" ? `<label class="sr" for="r-${esc(m.pid)}">Reason</label><select id="r-${esc(m.pid)}" data-r="${esc(m.pid)}"><option value="">Reason</option>${(c.reject_reasons || []).map((x: string) => `<option ${ma[m.pid]?.reason === x ? "selected" : ""}>${esc(x)}</option>`).join("")}</select>` : ""}</div></li>`).join("")}</ul>
        ${rest.length ? `<details><summary>${rest.length} other members</summary><ul class="plain small">${rest.map((m) => `<li><span class="mono">${esc(m.pid)}</span> ${esc(m.label_en || m.label)}</li>`).join("")}</ul></details>` : ""}`;
      const setM = (pid: string, patch: any) => save({ member_answers: { ...ma, [pid]: { ...(ma[pid] || {}), ...patch } } });
      q.querySelectorAll<HTMLButtonElement>("[data-m]").forEach((b) => (b.onclick = () => setM(b.dataset.m!, { answer: b.dataset.v })));
      q.querySelectorAll<HTMLSelectElement>("[data-t]").forEach((s) => (s.onchange = () => setM(s.dataset.t!, { target: s.value })));
      q.querySelectorAll<HTMLSelectElement>("[data-r]").forEach((s) => (s.onchange = () => setM(s.dataset.r!, { reason: s.value })));
      return;
    }
    const q1 = curation === "placement"
      ? `<fieldset><legend>Does this variable belong to this construct?</legend><div class="row wrap">${btn("b", "yes", a.belongs, "Yes", "Y")}${btn("b", "neighbour", a.belongs, "In a neighbour", "N")}${btn("b", "reject", a.belongs, "Reject")}${btn("b", "unsure", a.belongs, "Unsure", "U")}</div></fieldset>
         ${a.belongs === "neighbour" || a.belongs === "no" ? neighbours(a.better_construct_pid) : ""}
         ${a.belongs === "reject" ? `<label for="rr">Reason</label><select id="rr"><option value="">Choose a reason</option>${(i.curation?.reject_reasons || []).map((x: string) => `<option ${a.reject_reason === x ? "selected" : ""}>${esc(x)}</option>`).join("")}</select>` : ""}`
      : `<fieldset><legend>Does this ${vocab === "rvv" ? "variable" : "item"} measure this construct?</legend><div class="row wrap">${btn("b", "yes", a.belongs, "Yes", "Y")}${btn("b", "no", a.belongs, "No", "N")}${btn("b", "unsure", a.belongs, "Unsure", "U")}</div></fieldset>
         ${a.belongs === "no" ? neighbours(a.better_construct_pid) : ""}`;
    const q2 = graded && a.belongs && a.belongs !== "no" ? `<fieldset><legend>Is the grade right?</legend>
        <p class="explain">${vocab === "rvv"
          ? "This variable has been compared with the one under Compared with. The grade says how closely the two match, and whether data from both can be combined as they are, after a simple recode, or only with extra assumptions."
          : "This question has been compared with the one under Compared with. The grade says how closely the two match, and whether answers to both can be combined as they are, after a simple recode, or only with extra assumptions."}</p>
        <p><span class="chip g-${esc(i.grade)}">${esc(i.grade)}</span> ${esc(GRADES[vocab][i.grade!] ?? "")}</p>${reasonsList(i)}
        <div class="row wrap">${btn("g", "yes", a.grade_ok, "Yes", "Y")}${btn("g", "no", a.grade_ok, "No", "N")}${btn("g", "unsure", a.grade_ok, "Unsure", "U")}</div>
        ${a.grade_ok === "no" ? `<div class="row wrap" role="group" aria-label="Correct grade">${Object.keys(GRADES[vocab]).map((g) => btn("cg", g, a.correct_grade, g)).join("")}</div>` : ""}</fieldset>` : "";
    q.innerHTML = q1 + q2;
    q.querySelectorAll<HTMLButtonElement>("[data-q]").forEach((b) => (b.onclick = () => {
      const v = b.dataset.v!;
      if (b.dataset.q === "b") save({ belongs: v, ...(v === "yes" || v === "unsure" ? { better_construct_pid: null, reject_reason: null } : {}) });
      if (b.dataset.q === "nb") save({ better_construct_pid: v, better_construct_text: null, belongs: curation === "placement" ? "neighbour" : "no" });
      if (b.dataset.q === "g") save({ grade_ok: v, ...(v !== "no" ? { correct_grade: null } : {}) });
      if (b.dataset.q === "cg") save({ correct_grade: v });
    }));
    const none = $<HTMLInputElement>("#none");
    if (none) none.onchange = () => save({ better_construct_text: none.value, better_construct_pid: null, belongs: "no" });
    const rr = $<HTMLSelectElement>("#rr");
    if (rr) rr.onchange = () => save({ reject_reason: rr.value });
  }
  draw();
  keyHandler = (e) => {
    const k = e.key.toLowerCase();
    const q1Done = !!a.belongs;
    if (e.key === "Enter") { e.preventDefault(); next(); return; }
    if (e.key === "Backspace") { e.preventDefault(); back(); return; }
    if (curation === "membership") return;
    if (/^[1-5]$/.test(k) && (a.belongs === "no" || a.belongs === "neighbour")) {
      const n = i.neighbour_constructs[Number(k) - 1];
      if (n) save({ better_construct_pid: n.pid, better_construct_text: null, belongs: curation === "placement" ? "neighbour" : "no" });
      return;
    }
    const map: Record<string, string> = curation === "placement" ? { y: "yes", n: "neighbour", u: "unsure" } : { y: "yes", n: "no", u: "unsure" };
    if (!map[k]) return;
    // Y, N and U answer the visible question, which is question 2 once question 1 has an answer other than no.
    if (graded && q1Done && a.belongs !== "no") save({ grade_ok: map[k] === "neighbour" ? "no" : map[k] });
    else save({ belongs: map[k] });
  };
}

// 5. End of batch
async function viewEnd(batchId: string) {
  keyHandler = null;
  const me = await api.me();
  const owner = me?.role === "owner";
  const box = (id: string, label: string) => `<label for="${id}">${label}</label><textarea id="${id}" rows="3"></textarea>`;
  const boxes = box("mc", "Constructs you expected and did not see") + box("si", "Systematic problems you noticed") + box("ot", "Anything else");
  render(`<section class="narrow"><h1>That is the batch</h1><p>Thank you. Your answers are saved.</p>
    <form id="f" class="stack">${owner ? `<details><summary>Comments (optional)</summary>${boxes}</details>` : `<p class="muted">Three optional questions.</p>${boxes}`}
    <button type="submit">Done</button></form></section>`, "End of batch");
  $("#f").onsubmit = async (e) => {
    e.preventDefault();
    const c = { missing_constructs: $<HTMLTextAreaElement>("#mc").value, systematic_issues: $<HTMLTextAreaElement>("#si").value, other: $<HTMLTextAreaElement>("#ot").value };
    if (c.missing_constructs || c.systematic_issues || c.other) await api.comment(batchId, c);
    location.hash = "#/";
  };
}

// 6. Admin
function csv(rows: Record<string, unknown>[]) {
  const cols = [...new Set(rows.flatMap((r) => Object.keys(r)))];
  const cell = (v: unknown) => { const s = v === null || v === undefined ? "" : typeof v === "object" ? JSON.stringify(v) : String(v); return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s; };
  return [cols.join(","), ...rows.map((r) => cols.map((c) => cell(r[c])).join(","))].join("\n");
}
function download(name: string, text: string) {
  const u = URL.createObjectURL(new Blob([text], { type: "text/csv" }));
  const a = Object.assign(document.createElement("a"), { href: u, download: name });
  document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(u);
}

async function viewAdmin() {
  keyHandler = null;
  const me = await api.me();
  if (me?.role !== "owner") return viewHome();
  const [bs, ex] = await Promise.all([api.ownerBatches(), api.exportsAvailable()]);
  render(`<h1>Admin</h1>
    <h2>New owner batch</h2><form id="nb" class="row wrap">
      <label for="ex">Export</label><select id="ex">${ex.map((e) => `<option>${esc(e.export_version)}</option>`).join("")}</select>
      <label for="qu">From</label><select id="qu"><option value="">quality sample</option></select>
      <label for="sz">Items</label><input id="sz" type="number" min="1" max="100" value="25" style="width:6rem">
      <button type="submit">Build and open</button></form><p id="nbm" role="status" class="small"></p>
    <h2>Batches</h2><div class="scroll"><table><thead><tr><th scope="col">Batch</th><th scope="col">Vocabulary</th><th scope="col">Kind</th><th scope="col">Status</th><th scope="col">Completion per reviewer</th><th scope="col"><span class="sr">Action</span></th></tr></thead><tbody>
    ${bs.map((b) => `<tr><td class="mono small">${esc(b.batch_id)}<div class="muted tiny">${esc(b.description)}</div></td><td>${esc(b.vocabulary)}</td><td>${esc(b.kind)}</td><td>${esc(b.status)}</td>
      <td class="small">${b.per_reviewer.map((p) => `${esc(p.reviewer)} ${p.answered} of ${p.items}`).join("<br>")}</td>
      <td>${b.status === "open" ? `<button class="ghost" data-s="${esc(b.batch_id)}" data-v="closed">Close</button>` : `<button class="ghost" data-s="${esc(b.batch_id)}" data-v="open">Open</button>`}</td></tr>`).join("")}
    </tbody></table></div>
    <h2>Export</h2><p class="small muted">A quick look only. tools/export_reviews.py is the record (section 7).</p>
    <div class="row wrap"><button id="xj">Download joined answers</button><button id="xc" class="ghost">Download comments</button></div>`, "Admin");
  const fillQ = () => { const e = ex.find((x) => x.export_version === $<HTMLSelectElement>("#ex").value); $("#qu").innerHTML = `<option value="">quality sample</option>` + (e?.queues ?? []).map((q) => `<option>${esc(q)}</option>`).join(""); };
  fillQ();
  $<HTMLSelectElement>("#ex").onchange = fillQ;
  $("#nb").onsubmit = async (e) => {
    e.preventDefault();
    const exv = $<HTMLSelectElement>("#ex").value, q = $<HTMLSelectElement>("#qu").value, n = Number($<HTMLInputElement>("#sz").value);
    try { const id = q ? await api.nextQueueBatch(exv, q, n) : await api.nextBatch(exv, n); $("#nbm").textContent = `Batch ${id} built and open.`; setTimeout(viewAdmin, 600); }
    catch (err) { $("#nbm").textContent = `Not built. ${(err as Error).message}`; }
  };
  main.querySelectorAll<HTMLButtonElement>("[data-s]").forEach((b) => (b.onclick = async () => { await api.setStatus(b.dataset.s!, b.dataset.v as "open" | "closed"); viewAdmin(); }));
  $("#xj").onclick = async () => { const { joined } = await api.ownerCsv(); download("reviews_joined.csv", csv(joined)); };
  $("#xc").onclick = async () => { const { comments } = await api.ownerCsv(); download("batch_comments.csv", csv(comments)); };
}

async function route() {
  const h = location.hash.replace(/^#\/?/, "");
  if (h === "privacy") return viewPrivacy();
  if (!(await api.signedIn())) return viewSignIn();
  const parts = h.split("/");
  if (parts[0] === "admin") return viewAdmin();
  if (parts[0] === "b" && parts[1]) {
    const b = (await api.batches()).find((x) => x.batch_id === parts[1]);
    if (!b || b.status !== "open") return viewHome();
    if (parts[2] === "end") return viewEnd(b.batch_id);
    if (!parts[2]) {
      if (!store.get(`vr-brief-${b.batch_id}`, false)) return viewBrief(b.batch_id, b.vocabulary, b.kind, b.items);
      const items = await api.items(b.batch_id), ans = await api.answers(b.batch_id);
      const first = items.find((i) => !ans.has(i.assignment_id)) ?? items[0];
      location.hash = `#/b/${b.batch_id}/${first?.position ?? 1}`;
      return;
    }
    return viewItem(b.batch_id, Number(parts[2]));
  }
  return viewHome();
}
// A sign in link returns with the session (or an error) in the address hash, which would clash with the page routes.
// supabase-js reads it while it starts, then the hash is cleared and the routes take over.
async function start() {
  const h = location.hash;
  if (/access_token=|error_description=|[?&]code=/.test(h + location.search)) {
    await api.signedIn();
    const err = new URLSearchParams(h.replace(/^#/, "")).get("error_description");
    history.replaceState(null, "", location.pathname + (api.demo ? "?demo" : "") + "#/");
    if (err) return viewSignIn(`That link did not work (${err}). Ask for a new code.`);
  }
  addEventListener("hashchange", route);
  route();
}
start();
(window as any).__demoReset = () => { (api as any).reset?.(); route(); };
