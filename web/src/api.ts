// The data layer. One interface, two implementations, Supabase (live) and Demo (fictional data in the browser).
// Review content comes from Supabase only after sign in and only for the caller's assignments (section 2).

import type { SupabaseClient } from "@supabase/supabase-js";

export interface Me { email: string; name: string; role: "reviewer" | "owner"; pseudonym: string | null }
export interface BatchInfo { batch_id: string; vocabulary: "scv" | "rvv" | "mixed"; kind: "quality" | "curation"; status: string; description: string | null;
  items: number; answered: number }
export interface Item {
  assignment_id: number; batch_id: string; position: number; batch_kind: string; item_id: string; vocabulary: "scv" | "rvv";
  export_version: string; queue: "placement" | "membership" | null; construct_pid: string; construct_label: string; construct_definition: string;
  construct_exclusions: string | null; construct_definition_provenance: string | null; measure_pid: string; programme: string;
  waves: string | null; question_text: string | null; question_text_en: string | null; text_kind: string | null;
  response_categories: { code: unknown; label: unknown }[] | null; universe_text: string | null; anchor_measure_pid: string | null;
  anchor_question_text: string | null; anchor_response_categories: { code: unknown; label: unknown }[] | null; grade: string | null;
  grade_reasons: Record<string, unknown> | null; method: string | null; neighbour_constructs: { pid: string; label: string }[];
  context: Record<string, unknown>; curation: Record<string, any> | null;
}
export interface Answer {
  assignment_id: number; belongs?: string | null; better_construct_pid?: string | null; better_construct_text?: string | null;
  reject_reason?: string | null; member_answers?: Record<string, { answer: string; target?: string | null; reason?: string | null }> | null;
  grade_ok?: string | null; correct_grade?: string | null; comment?: string | null; seconds_on_item?: number | null;
}
export interface OwnerBatch extends BatchInfo { per_reviewer: { reviewer: string; items: number; answered: number }[]; export_version: string | null }
export interface Api {
  demo: boolean;
  start(email: string): Promise<void>;
  verify(email: string, code: string): Promise<boolean>;
  signedIn(): Promise<string | null>;
  signOut(): Promise<void>;
  me(): Promise<Me | null>;
  batches(): Promise<BatchInfo[]>;
  items(batchId: string): Promise<Item[]>;
  answers(batchId: string): Promise<Map<number, Answer>>;
  save(a: Answer): Promise<void>;
  comment(batchId: string, c: { missing_constructs: string; systematic_issues: string; other: string }): Promise<void>;
  ownerBatches(): Promise<OwnerBatch[]>;
  setStatus(batchId: string, status: "open" | "closed"): Promise<void>;
  exportsAvailable(): Promise<{ export_version: string; queues: string[] }[]>;
  nextBatch(exportVersion: string, size: number): Promise<string>;
  nextQueueBatch(exportVersion: string, queue: string, size: number): Promise<string>;
  ownerCsv(): Promise<{ joined: Record<string, unknown>[]; comments: Record<string, unknown>[] }>;
}

export class SupabaseApi implements Api {
  demo = false;
  constructor(private sb: SupabaseClient) {}
  private db() { return this.sb.schema("review"); }

  async start(email: string) {
    // shouldCreateUser false. Unknown addresses get the same neutral message as known ones (section 3).
    // The email carries a six digit code ({{ .Token }} in the Supabase template). If the template still sends a link,
    // the link comes back to this page and is accepted too (main.ts).
    await this.sb.auth.signInWithOtp({ email, options: { shouldCreateUser: false, emailRedirectTo: location.origin + location.pathname } });
  }
  async verify(email: string, code: string) {
    const { error } = await this.sb.auth.verifyOtp({ email, token: code, type: "email" });
    return !error;
  }
  async signedIn() { return (await this.sb.auth.getSession()).data.session?.user.email ?? null; }
  async signOut() { await this.sb.auth.signOut(); }
  async me() {
    const email = await this.signedIn();
    if (!email) return null;
    const { data, error } = await this.db().from("reviewer").select("email,name,role,pseudonym").eq("email", email.toLowerCase()).maybeSingle();
    if (error) throw new Error(`The review data could not be reached (${error.code ?? "error"}).`);   // for example PGRST106, schema not exposed
    return (data as Me) ?? null;
  }
  async batches() {
    const [{ data: b }, { data: p }] = await Promise.all([
      this.db().from("batch").select("batch_id,vocabulary,kind,status,description").order("batch_id"),
      this.db().from("my_progress").select("batch_id,items,answered"),
    ]);
    const prog = new Map((p ?? []).map((x: any) => [x.batch_id, x]));
    return (b ?? []).map((x: any) => ({ ...x, items: prog.get(x.batch_id)?.items ?? 0, answered: prog.get(x.batch_id)?.answered ?? 0 }));
  }
  async items(batchId: string) {
    const { data, error } = await this.db().from("item_reviewer").select("*").eq("batch_id", batchId).order("position");
    if (error) throw error;
    return data as Item[];
  }
  async answers(batchId: string) {
    const items = await this.items(batchId);
    const ids = items.map((i) => i.assignment_id);
    const out = new Map<number, Answer>();
    for (let k = 0; k < ids.length; k += 200) {
      const { data } = await this.db().from("response").select("*").in("assignment_id", ids.slice(k, k + 200)).order("submitted_at");
      for (const r of data ?? []) out.set(r.assignment_id, r as Answer);
    }
    return out;
  }
  async save(a: Answer) {
    const { error } = await this.db().from("response").insert({ ...a, client_version: "web" });
    if (error) throw error;
  }
  async comment(batchId: string, c: { missing_constructs: string; systematic_issues: string; other: string }) {
    const email = await this.signedIn();
    const { error } = await this.db().from("batch_comment").insert({ batch_id: batchId, reviewer_email: email?.toLowerCase(), ...c });
    if (error) throw error;
  }
  async ownerBatches() {
    const [{ data: b }, { data: s }, { data: r }, { data: who }] = await Promise.all([
      this.db().from("batch").select("*").order("batch_id"),
      this.db().from("assignment").select("assignment_id,batch_id,reviewer_email,item_id"),
      this.db().from("response").select("assignment_id"),
      this.db().from("reviewer").select("email,pseudonym"),
    ]);
    return summarise(b ?? [], s ?? [], r ?? [], who ?? []);
  }
  async setStatus(batchId: string, status: "open" | "closed") {
    const { error } = await this.db().from("batch").update({ status }).eq("batch_id", batchId);
    if (error) throw error;
  }
  async exportsAvailable() {
    const { data } = await this.db().from("item").select("export_version,queue").limit(100000);
    return groupExports(data ?? []);
  }
  async nextBatch(exportVersion: string, size: number) {
    const { data, error } = await this.db().rpc("owner_next_batch", { p_export: exportVersion, p_size: size });
    if (error) throw error;
    return data as string;
  }
  async nextQueueBatch(exportVersion: string, queue: string, size: number) {
    const { data, error } = await this.db().rpc("owner_next_queue_batch", { p_export: exportVersion, p_queue: queue, p_size: size });
    if (error) throw error;
    return data as string;
  }
  async ownerCsv() {
    const [{ data: s }, { data: r }, { data: who }, { data: c }] = await Promise.all([
      this.db().from("assignment").select("*"), this.db().from("response").select("*").order("submitted_at"),
      this.db().from("reviewer").select("email,pseudonym,role"), this.db().from("batch_comment").select("*"),
    ]);
    const itemIds = [...new Set((s ?? []).map((x: any) => x.item_id))];
    const items: any[] = [];
    for (let k = 0; k < itemIds.length; k += 200) {
      const { data } = await this.db().from("item").select("*").in("item_id", itemIds.slice(k, k + 200));
      items.push(...(data ?? []));
    }
    return joinCsv(s ?? [], r ?? [], who ?? [], items, c ?? []);
  }
}

// Shared by both implementations.
export function summarise(b: any[], s: any[], r: any[], who: any[]): OwnerBatch[] {
  const answered = new Set(r.map((x) => x.assignment_id));
  const ps = new Map(who.map((w) => [w.email, w.pseudonym ?? w.email]));
  return b.map((x) => {
    const mine = s.filter((a) => a.batch_id === x.batch_id);
    const per = new Map<string, { reviewer: string; items: number; answered: number }>();
    for (const a of mine) {
      const k = ps.get(a.reviewer_email) ?? "unknown";
      const v = per.get(k) ?? { reviewer: k, items: 0, answered: 0 };
      v.items++;
      if (answered.has(a.assignment_id)) v.answered++;
      per.set(k, v);
    }
    return { batch_id: x.batch_id, vocabulary: x.vocabulary, kind: x.kind, status: x.status, description: x.description,
      items: mine.length, answered: mine.filter((a) => answered.has(a.assignment_id)).length, per_reviewer: [...per.values()],
      export_version: x.sampling_spec?.export ?? null };
  });
}

export function groupExports(rows: { export_version: string; queue: string | null }[]) {
  const m = new Map<string, Set<string>>();
  for (const r of rows) {
    if (!m.has(r.export_version)) m.set(r.export_version, new Set());
    if (r.queue) m.get(r.export_version)!.add(r.queue);
  }
  return [...m].map(([export_version, q]) => ({ export_version, queues: [...q].sort() }));
}

export function joinCsv(s: any[], r: any[], who: any[], items: any[], comments: any[]) {
  const ps = new Map(who.map((w) => [w.email, w.pseudonym ?? "unknown"]));
  const role = new Map(who.map((w) => [w.pseudonym, w.role]));
  const byItem = new Map(items.map((i) => [i.item_id, i]));
  const current = new Map<number, any>();
  for (const x of r) current.set(x.assignment_id, x);
  const joined = s.filter((a) => current.has(a.assignment_id)).map((a) => {
    const resp = current.get(a.assignment_id);
    const pseud = ps.get(a.reviewer_email) ?? "unknown";
    return { ...resp, batch_id: a.batch_id, position: a.position, is_overlap: a.is_overlap, reviewer: pseud, reviewer_role: role.get(pseud) ?? "",
      ...byItem.get(a.item_id) };
  });
  const cm = comments.map((c) => { const { reviewer_email, ...rest } = c; return { ...rest, reviewer: ps.get(reviewer_email) ?? "unknown" }; });
  return { joined, comments: cm };
}
