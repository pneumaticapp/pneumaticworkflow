import { RawDraftContentState } from 'draft-js';

/**
 * Safely parse clipboard JSON for paste. Returns null for empty, whitespace-only
 * or invalid JSON to avoid SyntaxError (e.g. "Unexpected end of JSON input").
 */
export function parsePasteJson(jsonContent: string): RawDraftContentState | null {
  if (!jsonContent || !jsonContent.trim()) {
    return null;
  }
  try {
    return JSON.parse(jsonContent) as RawDraftContentState;
  } catch {
    return null;
  }
}
