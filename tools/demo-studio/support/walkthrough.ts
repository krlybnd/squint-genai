import fs from "node:fs";
import path from "node:path";
import type { Page } from "@playwright/test";
import {
  CAPTION_LOCALES,
  type CaptionCue,
  assertHoldsMatchEntries,
  toSrt,
  toVtt,
} from "./captions";

export function isRecording(): boolean {
  return process.env.DEMO_RECORD === "1";
}

export class Walkthrough {
  originMs = Date.now();
  cues: CaptionCue[] = [];
  private current: { key: string; startMs: number; holds: number[] } | null = null;

  reset(originMs = Date.now()): void {
    this.originMs = originMs;
    this.cues = [];
    this.current = null;
  }

  nowMs(): number {
    return Date.now() - this.originMs;
  }

  /** Time left on the open caption. The next step that calls finishCurrent waits this out. */
  remainingHoldMs(): number {
    if (!this.current) return 0;
    const minMs = this.current.holds.reduce((sum, n) => sum + n, 0) * 1000;
    return Math.max(0, minMs - (this.nowMs() - this.current.startMs));
  }

  async beginCaption(page: Page, key: string, holds: number[]): Promise<void> {
    await this.finishCurrent(page);
    assertHoldsMatchEntries(key, holds);
    this.current = { key, startMs: this.nowMs(), holds };
  }

  async finishCurrent(page: Page): Promise<void> {
    if (!this.current) return;
    const { key, startMs, holds } = this.current;
    const minMs = holds.reduce((sum, n) => sum + n, 0) * 1000;
    const remaining = minMs - (this.nowMs() - startMs);
    if (remaining > 0) {
      await page.waitForTimeout(remaining);
    }
    const endMs = Math.max(startMs + 200, this.nowMs());
    let t = startMs;
    for (const [i, hold] of holds.entries()) {
      const next = i === holds.length - 1 ? endMs : t + hold * 1000;
      this.cues.push({
        key,
        entryIndex: i,
        startMs: t,
        endMs: Math.max(t + 200, next),
      });
      t = next;
    }
    this.current = null;
  }

  writeTranscripts(dir: string): void {
    fs.mkdirSync(dir, { recursive: true });
    for (const locale of CAPTION_LOCALES) {
      fs.writeFileSync(path.join(dir, `video.${locale}.srt`), toSrt(this.cues, locale), "utf8");
      fs.writeFileSync(path.join(dir, `video.${locale}.vtt`), toVtt(this.cues, locale), "utf8");
    }
  }
}

export const walkthrough = new Walkthrough();
