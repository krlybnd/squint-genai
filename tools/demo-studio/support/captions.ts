import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

export type CaptionLines = string[];
export type CaptionLocale = "en" | "hu";
export const CAPTION_LOCALES: CaptionLocale[] = ["en", "hu"];

export type CaptionEntry = {
  en: CaptionLines;
  hu: CaptionLines;
};

/** Copy only. Hold times are Gherkin `{holds}`: `(3, 4)`. */
export type CaptionRow = {
  key: string;
  entries: CaptionEntry[];
};

const captionsDir = path.join(path.dirname(fileURLToPath(import.meta.url)), "..", "captions");
const cuesFile = path.join(captionsDir, "cues.json");

let rows: CaptionRow[] | null = null;
const byKey = new Map<string, CaptionRow>();

export function loadCues(): CaptionRow[] {
  if (rows) return rows;
  const parsed = JSON.parse(fs.readFileSync(cuesFile, "utf8")) as CaptionRow[];
  if (!Array.isArray(parsed) || parsed.length === 0) {
    throw new Error(`captions/cues.json must be a non-empty list`);
  }
  rows = parsed;
  for (const row of parsed) {
    if (!row.key || !row.entries?.length) {
      throw new Error(`Caption "${row.key}" needs entries[]`);
    }
    for (const [i, entry] of row.entries.entries()) {
      if (!entry.en?.length || !entry.hu?.length) {
        throw new Error(`Caption "${row.key}" entry ${i} needs en[] and hu[]`);
      }
    }
    byKey.set(row.key, row);
  }
  return rows;
}

export function cueFor(key: string): CaptionRow {
  loadCues();
  const row = byKey.get(key);
  if (!row) {
    throw new Error(`Missing caption "${key}" in captions/cues.json`);
  }
  return row;
}

export function assertHoldsMatchEntries(key: string, holds: number[]): CaptionEntry[] {
  const { entries } = cueFor(key);
  if (holds.length !== entries.length) {
    throw new Error(
      `Caption "${key}" has ${entries.length} entries but ${holds.length} hold(s): (${holds.join(", ")}).`,
    );
  }
  if (holds.some((n) => !Number.isFinite(n) || n <= 0)) {
    throw new Error(`Caption "${key}" holds must be positive seconds: (${holds.join(", ")}).`);
  }
  return entries;
}

export function linesFor(locale: CaptionLocale, key: string, entryIndex?: number): CaptionLines {
  const { entries } = cueFor(key);
  if (entryIndex == null) {
    return entries.flatMap((entry) => entry[locale]);
  }
  const entry = entries[entryIndex];
  if (!entry) {
    throw new Error(`Caption "${key}" has no entry ${entryIndex}`);
  }
  return entry[locale];
}

function pad2(n: number): string {
  return String(n).padStart(2, "0");
}

function pad3(n: number): string {
  return String(n).padStart(3, "0");
}

/** YouTube-friendly clock: HH:MM:SS,mmm */
export function formatSrtTime(ms: number): string {
  const clamped = Math.max(0, Math.round(ms));
  const hours = Math.floor(clamped / 3_600_000);
  const minutes = Math.floor((clamped % 3_600_000) / 60_000);
  const seconds = Math.floor((clamped % 60_000) / 1000);
  const millis = clamped % 1000;
  return `${pad2(hours)}:${pad2(minutes)}:${pad2(seconds)},${pad3(millis)}`;
}

export function formatVttTime(ms: number): string {
  return formatSrtTime(ms).replace(",", ".");
}

export type CaptionCue = { key: string; startMs: number; endMs: number; entryIndex: number };

function cueBody(locale: CaptionLocale, cue: CaptionCue): string | null {
  const body = linesFor(locale, cue.key, cue.entryIndex).join("\n").trim();
  if (body === "-") return null;
  return body;
}

export function toSrt(cues: CaptionCue[], locale: CaptionLocale): string {
  let n = 0;
  return cues
    .map((cue) => {
      const body = cueBody(locale, cue);
      if (body == null) return "";
      n += 1;
      return `${n}\n${formatSrtTime(cue.startMs)} --> ${formatSrtTime(cue.endMs)}\n${body}\n`;
    })
    .filter(Boolean)
    .join("\n");
}

export function toVtt(cues: CaptionCue[], locale: CaptionLocale): string {
  const blocks = cues
    .map((cue) => {
      const body = cueBody(locale, cue);
      if (body == null) return "";
      return `${formatVttTime(cue.startMs)} --> ${formatVttTime(cue.endMs)}\n${body}\n`;
    })
    .filter(Boolean);
  return `WEBVTT\n\n${blocks.join("\n")}`;
}
