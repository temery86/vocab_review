// Site settings and per vocabulary wording (V-01, section 12.2). Changing the name is a change here only.

export const SITE = {
  title: "Vocabulary review",
  runBy: "an independent research project",
  clientVersion: "0.1.0",
};

export type Vocab = "scv" | "rvv";

export const VOCAB_NAME: Record<Vocab, string> = {
  scv: "survey questions",
  rvv: "register variables",
};

// One line meaning of each grade, worded per vocabulary.
export const GRADES: Record<Vocab, Record<string, string>> = {
  scv: {
    identical: "Same response format, reference period and population. Can be pooled as they are.",
    equivalent: "Differences that a documented recode resolves, for example collapsing categories.",
    related: "Differences in format, period or population that need modelling assumptions before pooling.",
    distinct: "Not the same thing at all. One of them is in this construct by mistake.",
  },
  rvv: {
    identical: "Same definition, population, timing and classification. Can be pooled as they are.",
    equivalent: "Differences that a documented crosswalk resolves, for example between classification versions.",
    related: "Differences in definition, population, timing or classification that need assumptions before pooling.",
    distinct: "Not the same thing at all. One of them is in this construct by mistake.",
  },
};

// Labels for the register card fields held in item.context, in display order (section 12.3).
export const CONTEXT_LABELS: Record<Vocab, [string, string][]> = {
  scv: [],
  rvv: [
    ["variable_name", "Variable"],
    ["label", "Label"],
    ["label_en", "English label"],
    ["definition", "Definition"],
    ["definition_en", "Definition in English"],
    ["definition_kind", "Definition from"],
    ["register", "Register"],
    ["body", "Body"],
    ["country", "Country"],
    ["years_covered", "Years covered"],
    ["classification", "Classification"],
    ["population", "Population"],
    ["reference_timing", "Reference timing"],
  ],
};

export const PROVENANCE: Record<string, string> = {
  person_written: "definition written by a person",
  draft_accepted: "generated draft definition accepted by a person",
  draft_endorsed: "generated draft definition endorsed by a person",
  draft_generated: "generated draft definition, not yet checked by a person",
  pending: "definition pending",
};

export const BRIEF: Record<Vocab, { what: string; item: string; examples: Record<string, string> }> = {
  scv: {
    what: "A construct is what a question measures, defined without reference to any one survey, for example trust in parliament or the number of children in the household.",
    item: "Each item is one survey question, shown against the construct it has been mapped to.",
    examples: {
      identical: "The same five point trust scale asked of all adults in two surveys.",
      equivalent: "Household size asked as a number in one survey and in bands up to 8 or more in another.",
      related: "Smoking now in one survey and smoking in the last year in another.",
      distinct: "A question about trust in the police mapped to trust in parliament.",
    },
  },
  rvv: {
    what: "A construct is what a register variable measures, defined without reference to any one register or country, for example the date of death or receipt of disability benefit.",
    item: "Each item is one register variable as an office documents it, shown against the construct it has been placed in.",
    examples: {
      identical: "Year of birth from two population registers, both for all residents.",
      equivalent: "Industry coded in NACE Rev. 2 in one register and in a national version with a published crosswalk in another.",
      related: "Annual earned income in one register and monthly gross wage in another.",
      distinct: "A municipality of work placed with municipality of residence.",
    },
  },
};
