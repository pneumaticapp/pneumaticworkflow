const PROTOCOL_REGEX = /^[a-zA-Z][a-zA-Z0-9+.-]*:\/\//i;

export function normalizeUrl(input: string): string {
  const trimmed = input.trim();
  if (!trimmed) return trimmed;
  if (PROTOCOL_REGEX.test(trimmed)) return trimmed;
  return `https://${trimmed}`;
}

export function isUrl(input: string): boolean {
  const normalized = normalizeUrl(input);
  try {
    const url = new URL(normalized);
    return Boolean(url);
  } catch {
    return false;
  }
}

const urlUtils = {
  normalizeUrl,
  isUrl,
};

export default urlUtils;
