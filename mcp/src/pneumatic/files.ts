import { ConnectorError } from '../core/errors.js';

const UNSAFE_CHARACTER = /[/\\?#%\p{C}\p{Zl}\p{Zp}]/u;

// File IDs are storage identities, not display names: keep their exact spelling and reject path ambiguity.
export function isSafeFileId(value: string): boolean {
  return (
    value.length >= 1 &&
    value.length <= 512 &&
    value.trim() !== '' &&
    value !== '.' &&
    value !== '..' &&
    !UNSAFE_CHARACTER.test(value)
  );
}

export function fileIdSegment(value: string): string {
  if (!isSafeFileId(value)) {
    throw new ConnectorError('invalid_arguments', 'Expected a flat file ID without path or control characters');
  }
  return encodeURIComponent(value);
}
