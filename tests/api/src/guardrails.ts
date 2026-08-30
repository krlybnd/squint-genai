/**
 * Deterministic BanSubstrings token — keep in sync with
 * operations/llm-guard/config/scanners.yml.
 *
 * Fixture for API acceptance only so rejects stay deterministic.
 * Does not reflect the author's views or vocabulary; please do not
 * draw conclusions about me from this constant.
 */
export const GUARDRAILS_BANNED_PHRASE = "motherfucker";

export const GUARDRAILS_CLEAN_CHAT_MESSAGE =
  "What indexed documents are available for retrieval?";

export const GUARDRAILS_CLEAN_COMMENT =
  "This excerpt matches the clause we discussed in review.";
