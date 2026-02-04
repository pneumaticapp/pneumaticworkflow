import { ContentState, convertFromRaw } from 'draft-js';
import { convertTextToDraft } from './converters/convertTextToDraft';
import { normalizeDraftRaw } from './converters/normalizeDraftRaw';
import { TTaskVariable } from '../../TemplateEdit/types';

/**
 * Detects our variable syntax in pasted text (e.g. "Hello {{field-xxx}}").
 * Safari (and some other contexts) don't expose application/json on paste,
 * so we fall back to parsing text/plain when it contains this format.
 */
const PASTED_VARIABLE_FORMAT = /\{\{[^}]+\}\}/;

export function isPastedContentWithVariables(text: string): boolean {
  return PASTED_VARIABLE_FORMAT.test(text);
}

/**
 * Parses pasted text/plain that contains our variable syntax into Draft ContentState.
 * Used when application/json is not available on paste (e.g. Safari).
 * Markdown (bold, italic, etc.) and variables/mentions are parsed together when both are present.
 */
export function contentStateFromPastedText(
  plainText: string,
  templateVariables: TTaskVariable[],
  isMarkdownEnabled = true,
): ContentState | null {
  if (!isPastedContentWithVariables(plainText)) {
    return null;
  }
  try {
    const raw = convertTextToDraft(plainText, templateVariables, isMarkdownEnabled);
    const normalizedRaw = normalizeDraftRaw(raw);
    return convertFromRaw(normalizedRaw);
  } catch {
    return null;
  }
}
