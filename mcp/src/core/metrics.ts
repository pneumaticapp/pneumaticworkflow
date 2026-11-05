type Labels = Record<string, string>;

interface Series {
  labels: Labels;
  value: number;
}

const counters = new Map<string, { help: string; series: Map<string, Series> }>();
const MAX_SERIES = 2000;

const key = (labels: Labels) =>
  Object.entries(labels)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([name, value]) => `${name}=${value}`)
    .join(',');

export function count(name: string, help: string, labels: Labels = {}, amount = 1) {
  let metric = counters.get(name);
  if (!metric) {
    metric = { help, series: new Map() };
    counters.set(name, metric);
  }
  const id = key(labels);
  const series = metric.series.get(id);
  if (series) {
    series.value += amount;
  } else if (metric.series.size < MAX_SERIES) {
    metric.series.set(id, { labels, value: amount });
  }
}

const escape = (value: string) => value.replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/\n/g, '\\n');

export function renderMetrics(): string {
  const lines: string[] = [];
  for (const [name, { help, series }] of counters) {
    lines.push(`# HELP ${name} ${help}`, `# TYPE ${name} counter`);
    for (const { labels, value } of series.values()) {
      const rendered = Object.entries(labels)
        .sort(([a], [b]) => a.localeCompare(b))
        .map(([label, text]) => `${label}="${escape(text)}"`)
        .join(',');
      lines.push(`${name}${rendered ? `{${rendered}}` : ''} ${value}`);
    }
  }
  return `${lines.join('\n')}\n`;
}

export function resetMetrics() {
  counters.clear();
}
