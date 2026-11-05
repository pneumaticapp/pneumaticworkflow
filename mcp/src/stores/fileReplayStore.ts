import { randomBytes } from 'node:crypto';
import { closeSync, fsyncSync, openSync, readFileSync, renameSync, rmSync, writeFileSync } from 'node:fs';
import { open } from 'node:fs/promises';
import { dirname } from 'node:path';

import type { ReplayKind, ReplayStore } from '../core/ports.js';
import { nowSeconds } from '../core/time.js';

const HEADER = 'pneumatic-replay-v1\n';
const COMPACT_AFTER = 10_000;

type ReplayEntry = [string, number];

function isReplayEntry(entry: unknown): entry is ReplayEntry {
  return (
    Array.isArray(entry) &&
    entry.length === 2 &&
    typeof entry[0] === 'string' &&
    typeof entry[1] === 'number' &&
    Number.isFinite(entry[1])
  );
}

function readEntries(path: string): {
  entries: Map<string, number>;
  records: number;
  isLegacy: boolean;
  isTorn: boolean;
} {
  const content = readFileSync(path, 'utf8');
  if (!content) {
    return { entries: new Map(), records: 0, isLegacy: true, isTorn: false };
  }

  const isLegacy = !content.startsWith(HEADER);
  // An unfinished last line was never synced, so its token was never issued and the line can be dropped.
  const complete = isLegacy ? content : content.slice(HEADER.length, content.lastIndexOf('\n') + 1);
  const parsed: unknown = isLegacy
    ? JSON.parse(complete)
    : complete
        .split('\n')
        .filter(Boolean)
        .map((line) => JSON.parse(line));
  if (!Array.isArray(parsed) || !parsed.every(isReplayEntry)) {
    throw new Error(`Invalid OAuth replay store: ${path}`);
  }
  return {
    entries: new Map(parsed),
    records: parsed.length,
    isLegacy,
    isTorn: !isLegacy && complete.length < content.length - HEADER.length,
  };
}

function rewriteLedger(path: string, entries: Map<string, number>) {
  const temporary = `${path}.${randomBytes(8).toString('hex')}.tmp`;
  try {
    const file = openSync(temporary, 'wx', 0o600);
    try {
      writeFileSync(file, HEADER + [...entries].map((entry) => `${JSON.stringify(entry)}\n`).join(''));
      fsyncSync(file);
    } finally {
      closeSync(file);
    }
    renameSync(temporary, path);
    const directory = openSync(dirname(path), 'r');
    try {
      fsyncSync(directory);
    } finally {
      closeSync(directory);
    }
  } finally {
    rmSync(temporary, { force: true });
  }
}

// One process only: the in-memory index and the append-only file are not shared between replicas.
export function createFileReplayStore(path: string): ReplayStore {
  const saved = readEntries(path);
  let entries = new Map([...saved.entries].filter(([, expiry]) => expiry >= nowSeconds()));
  let records = saved.records;
  // Rewriting also removes a torn tail, which the next append would otherwise glue onto.
  if (saved.isLegacy || saved.isTorn || entries.size !== records) {
    rewriteLedger(path, entries);
    records = entries.size;
  }

  const liveCount = () => {
    const now = nowSeconds();
    let live = 0;
    for (const expiry of entries.values()) {
      if (expiry >= now) {
        live += 1;
      }
    }
    return live;
  };

  let queue = Promise.resolve();
  let failed: unknown;

  return {
    async isHealthy() {
      return failed === undefined;
    },
    async isUsed(kind: ReplayKind, id: string) {
      return (entries.get(`${kind}:${id}`) ?? 0) >= nowSeconds();
    },
    markUsed(kind: ReplayKind, id: string, exp: number) {
      const result = queue.then(async () => {
        if (failed) {
          // A failed append was never acknowledged, so rewriting the file from memory restores a consistent ledger.
          rewriteLedger(path, entries);
          failed = undefined;
        }
        const now = nowSeconds();
        const key = `${kind}:${id}`;
        if (exp < now || (entries.get(key) ?? 0) >= now) return false;

        const file = await open(path, 'a');
        try {
          await file.writeFile(`${JSON.stringify([key, exp])}\n`);
          await file.sync();
        } finally {
          await file.close();
        }
        entries.set(key, exp);
        records++;

        // Compact only when expired entries dominate; otherwise a large live ledger would be rewritten on every call.
        if (records >= COMPACT_AFTER && records >= 2 * liveCount()) {
          const current = new Map([...entries].filter(([, expiry]) => expiry >= nowSeconds()));
          rewriteLedger(path, current);
          entries = current;
          records = current.size;
        }
        return true;
      });
      queue = result.then(
        () => undefined,
        (error: unknown) => {
          failed = error;
        },
      );
      return result;
    },
  };
}
