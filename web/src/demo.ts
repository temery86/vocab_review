// Demo mode. A fictional backend in the browser with the same interface as Supabase, for trying the screens before
// a Supabase project exists (phase 2 on seeded data). Nothing here comes from a vocabulary (section 11).
// Sign in as alice@example.org (reviewer) or owner@example.org (owner) with the code 123456.

import { type Api, type Answer, type Item, groupExports, joinCsv, summarise } from "./api";

const KEY = "vr-demo-state-v1";
const NB = (v: string) => [1, 2, 3, 4, 5].map((k) => ({ pid: `demo:c/${v}${k}`, label: `Fictional ${v === "s" ? "survey" : "register"} construct ${k}` }));

function survey(n: number, gold = false): any {
  const graded = n % 3 !== 0;
  return {
    item_id: `scv:demo:m/aa/${n}:demo:c/s0:demo-0.1`, vocabulary: "scv", export_version: "demo-0.1", queue: null, construct_pid: "demo:c/s0",
    construct_label: "Fictional trust in neighbours", construct_definition: "How far a person trusts the people who live near them, whatever the scale used.",
    construct_exclusions: "Excludes trust in institutions and in people in general.", construct_definition_provenance: n % 2 ? "person_written" : "draft_accepted",
    measure_pid: `demo:m/aa/${n}`, programme: ["Fictional Panel", "Example Survey"][n % 2], waves: "w1 to w4 (2001 to 2007), 4 waves",
    question_text: n % 2 ? `Wie sehr vertrauen Sie Ihren Nachbarn? (Frage ${n})` : `How much do you trust your neighbours? (question ${n})`,
    question_text_en: n % 2 ? `How much do you trust your neighbours? (question ${n})` : null, text_kind: "question",
    response_categories: [{ code: 1, label: "Not at all" }, { code: 2, label: "A little" }, { code: 3, label: "Somewhat" }, { code: 4, label: "Completely" }],
    universe_text: "All respondents aged 16 and over", anchor_measure_pid: graded ? "demo:m/aa/0" : null,
    anchor_question_text: graded ? "Generally speaking, can you trust the people in your neighbourhood?" : null,
    anchor_response_categories: graded ? [{ code: 0, label: "No" }, { code: 1, label: "Yes" }] : null,
    grade: graded ? (n % 2 ? "related" : "equivalent") : null, grade_reasons: graded ? { differs: ["response_format"] } : null,
    method: "poc_full", neighbour_constructs: NB("s"), stratum: { programme: "demo" }, context: {}, curation: null, is_gold: gold,
  };
}

function register(n: number, queue: "placement" | "membership" | null = null): any {
  const base = {
    item_id: `rvv:demo:r/xx/${n}:demo:c/r0:demo-0.1${queue ? ":" + queue : ""}`, vocabulary: "rvv", export_version: "demo-0.1", queue,
    construct_pid: "demo:c/r0", construct_label: "Fictional year of moving home", construct_definition: "The calendar year in which a person last moved to a new home address.",
    construct_exclusions: null, construct_definition_provenance: "draft_generated", measure_pid: `demo:r/xx/${n}`, programme: "xx/demo", waves: "2001 to 2020",
    question_text: "Jahr, in dem die Person zuletzt an eine neue Adresse gezogen ist.", question_text_en: "Year in which the person last moved to a new address.",
    text_kind: "definition", response_categories: null, universe_text: "All residents", anchor_measure_pid: null, anchor_question_text: null,
    anchor_response_categories: null, grade: null, grade_reasons: null, method: "not_graded", neighbour_constructs: NB("r"), stratum: { country: "xx" },
    context: { variable_name: `UMZ_JAHR_${n}`, label: "Jahr des letzten Umzugs", label_en: "Year of last move",
      definition: "Jahr, in dem die Person zuletzt an eine neue Adresse gezogen ist.", definition_kind: "office", register: "Fictional population register",
      body: "demo", country: "xx", years_covered: "2001 to 2020", classification: null, population: "All residents", reference_timing: "event" },
    curation: queue === "placement" ? { reject_reasons: ["technical", "identifier", "business", "aggregate", "other"] } : null, is_gold: false,
  };
  if (queue === "membership") {
    base.curation = { note: "Two members look like dates of moving rather than years. Check whether they belong here.",
      members: [1, 2, 3, 4].map((k) => ({ pid: `demo:r/xx/${100 + k}`, label: `Umzugsjahr ${k}`, label_en: `Year of move ${k}`, country: "xx" })),
      named_members: ["demo:r/xx/102", "demo:r/xx/103"], answers_per_member: ["stay", "move", "reject"],
      reject_reasons: ["technical", "identifier", "other"] } as any;
  }
  return base;
}

function seed() {
  const items = [...[1, 2, 3, 4, 5, 6].map((n) => survey(n, n === 4)), ...[1, 2, 3].map((n) => register(n)), register(10, "placement"),
    register(11, "placement"), register(20, "membership"), ...[7, 8, 9].map((n) => survey(n))];
  const batches = [
    { batch_id: "b-demo-01", vocabulary: "scv", kind: "quality", status: "open", description: "Fictional survey batch", sampling_spec: { export: "demo-0.1" } },
    { batch_id: "b-demo-02", vocabulary: "rvv", kind: "quality", status: "open", description: "Fictional register batch", sampling_spec: { export: "demo-0.1" } },
    { batch_id: "b-demo-03", vocabulary: "rvv", kind: "curation", status: "open", description: "Fictional curation batch", sampling_spec: { export: "demo-0.1", queue: "placement" } },
    { batch_id: "b-demo-04", vocabulary: "scv", kind: "quality", status: "closed", description: "Fictional completed batch", sampling_spec: { export: "demo-0.1" } },
  ];
  let id = 1;
  const a = (batch_id: string, item_id: string, email: string, position: number) => ({ assignment_id: id++, batch_id, item_id, reviewer_email: email, position, is_overlap: false });
  const assignments: any[] = [];
  for (const email of ["alice@example.org", "owner@example.org"]) {
    items.filter((i) => i.vocabulary === "scv" && !i.item_id.match(/\/(7|8|9):/)).forEach((i, k) => assignments.push(a("b-demo-01", i.item_id, email, k + 1)));
    items.filter((i) => i.vocabulary === "rvv" && !i.queue).forEach((i, k) => assignments.push(a("b-demo-02", i.item_id, email, k + 1)));
    items.filter((i) => i.queue).forEach((i, k) => assignments.push(a("b-demo-03", i.item_id, email, k + 1)));
    items.filter((i) => i.item_id.match(/\/(7|8|9):/)).forEach((i, k) => assignments.push(a("b-demo-04", i.item_id, email, k + 1)));
  }
  const responses = assignments.filter((x) => x.batch_id === "b-demo-04").map((x, k) => ({ response_id: k + 1, assignment_id: x.assignment_id, belongs: "yes", submitted_at: new Date().toISOString() }));
  return { items, batches, assignments, responses, comments: [] as any[], user: null as string | null };
}

const PEOPLE: Record<string, { name: string; role: "reviewer" | "owner"; pseudonym: string }> = {
  "alice@example.org": { name: "Alice Example", role: "reviewer", pseudonym: "r01" },
  "owner@example.org": { name: "Demo Owner", role: "owner", pseudonym: "r00" },
};

export class DemoApi implements Api {
  demo = true;
  private s: ReturnType<typeof seed>;
  constructor() {
    let s = null;
    try { s = JSON.parse(localStorage.getItem(KEY) || "null"); } catch { s = null; }
    this.s = s ?? seed();
  }
  private persist() { try { localStorage.setItem(KEY, JSON.stringify(this.s)); } catch { /* private window */ } }
  reset() { this.s = seed(); this.persist(); }
  async start() { /* no mail in demo mode */ }
  async verify(email: string, code: string) {
    const e = email.trim().toLowerCase();
    if (code !== "123456" || !PEOPLE[e]) return false;
    this.s.user = e;
    this.persist();
    return true;
  }
  async signedIn() { return this.s.user; }
  async signOut() { this.s.user = null; this.persist(); }
  async me() { return this.s.user ? { email: this.s.user, ...PEOPLE[this.s.user] } : null; }
  private mine() { return this.s.assignments.filter((a) => a.reviewer_email === this.s.user); }
  async batches() {
    const answered = new Set(this.s.responses.map((r) => r.assignment_id));
    const mine = this.mine();
    return this.s.batches.filter((b) => mine.some((a) => a.batch_id === b.batch_id)).map((b: any) => {
      const as = mine.filter((a) => a.batch_id === b.batch_id);
      return { ...b, items: as.length, answered: as.filter((a) => answered.has(a.assignment_id)).length };
    });
  }
  async items(batchId: string): Promise<Item[]> {
    const b = this.s.batches.find((x) => x.batch_id === batchId);
    if (!b || b.status !== "open") return [];
    return this.mine().filter((a) => a.batch_id === batchId).sort((x, y) => x.position - y.position).map((a) => {
      const { is_gold: _g, stratum: _s, ...i } = this.s.items.find((x) => x.item_id === a.item_id);
      return { ...i, assignment_id: a.assignment_id, batch_id: a.batch_id, position: a.position, is_overlap: a.is_overlap, batch_kind: b.kind } as Item;
    });
  }
  async answers(batchId: string) {
    const ids = new Set(this.mine().filter((a) => a.batch_id === batchId).map((a) => a.assignment_id));
    const out = new Map<number, Answer>();
    for (const r of this.s.responses) if (ids.has(r.assignment_id)) out.set(r.assignment_id, r as Answer);
    return out;
  }
  async save(a: Answer) {
    if (!this.mine().some((x) => x.assignment_id === a.assignment_id)) throw new Error("not your assignment");
    this.s.responses.push({ ...a, response_id: this.s.responses.length + 1, submitted_at: new Date().toISOString() } as any);
    this.persist();
  }
  async comment(batchId: string, c: { missing_constructs: string; systematic_issues: string; other: string }) {
    this.s.comments.push({ comment_id: this.s.comments.length + 1, batch_id: batchId, reviewer_email: this.s.user, ...c, submitted_at: new Date().toISOString() });
    this.persist();
  }
  private owner() { if (this.s.user !== "owner@example.org") throw new Error("owner only"); }
  async ownerBatches() {
    this.owner();
    return summarise(this.s.batches, this.s.assignments, this.s.responses, Object.entries(PEOPLE).map(([email, p]) => ({ email, ...p })));
  }
  async setStatus(batchId: string, status: "open" | "closed") {
    this.owner();
    const b = this.s.batches.find((x) => x.batch_id === batchId);
    if (b) b.status = status;
    this.persist();
  }
  async exportsAvailable() { this.owner(); return groupExports(this.s.items); }
  async nextBatch(exportVersion: string, size: number) {
    this.owner();
    const have = new Set(this.mine().map((a) => a.item_id));
    const pick = this.s.items.filter((i) => i.export_version === exportVersion && !i.queue && !have.has(i.item_id)).slice(0, size);
    if (!pick.length) throw new Error("nothing left to draw");
    return this.addBatch(pick, "quality", pick[0].vocabulary);
  }
  async nextQueueBatch(exportVersion: string, queue: string, size: number) {
    this.owner();
    const taken = new Set(this.s.assignments.map((a) => a.item_id));
    const pick = this.s.items.filter((i) => i.export_version === exportVersion && i.queue === queue && !taken.has(i.item_id)).slice(0, size);
    if (!pick.length) throw new Error("nothing left in the queue");
    return this.addBatch(pick, "curation", pick[0].vocabulary);
  }
  private addBatch(pick: any[], kind: string, vocabulary: string) {
    const id = `b-demo-${String(this.s.batches.length + 1).padStart(2, "0")}`;
    this.s.batches.push({ batch_id: id, vocabulary, kind, status: "open", description: `Fictional ${kind} batch built on request`, sampling_spec: { export: "demo-0.1" } });
    let next = Math.max(...this.s.assignments.map((a) => a.assignment_id)) + 1;
    pick.forEach((i, k) => this.s.assignments.push({ assignment_id: next++, batch_id: id, item_id: i.item_id, reviewer_email: this.s.user, position: k + 1, is_overlap: false }));
    this.persist();
    return id;
  }
  async ownerCsv() {
    this.owner();
    return joinCsv(this.s.assignments, this.s.responses, Object.entries(PEOPLE).map(([email, p]) => ({ email, ...p })), this.s.items, this.s.comments);
  }
}
