export function unprefix(value: unknown, prefix: string): string | null {
  return typeof value === 'string' && value.startsWith(prefix) ? value.slice(prefix.length) : null;
}

export function asString(value: unknown): string | undefined {
  return typeof value === 'string' && value ? value : undefined;
}
