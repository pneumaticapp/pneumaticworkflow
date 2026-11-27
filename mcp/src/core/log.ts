type Level = 'debug' | 'info' | 'warn' | 'error';

const LEVELS: Record<Level | 'off', number> = { debug: 10, info: 20, warn: 30, error: 40, off: 100 };

type Fields = Record<string, string | number | boolean | null | undefined>;

let threshold = LEVELS.info;
let write: (line: string) => void = (line) => {
  process.stderr.write(`${line}\n`);
};

export function configureLog(level: string | undefined, sink?: (line: string) => void) {
  const name = level?.trim().toLowerCase() || 'info';
  if (!Object.hasOwn(LEVELS, name)) {
    throw new Error(`LOG_LEVEL must be one of ${Object.keys(LEVELS).join(', ')}`);
  }
  threshold = LEVELS[name as Level | 'off'];
  if (sink) {
    write = sink;
  }
}

// stdout carries the MCP protocol in stdio mode. Never log arguments, results, API keys or tokens.
export function log(level: Level, event: string, fields: Fields = {}) {
  if (LEVELS[level] < threshold) {
    return;
  }
  write(JSON.stringify({ time: new Date().toISOString(), level, event, ...fields }));
}
