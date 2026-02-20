import { parsePasteJson } from '../parsePasteJson';

describe('parsePasteJson', () => {
  it('returns null for empty string', () => {
    expect(parsePasteJson('')).toBeNull();
  });

  it('returns null for whitespace-only string', () => {
    expect(parsePasteJson('   ')).toBeNull();
    expect(parsePasteJson('\n\t')).toBeNull();
  });

  it('returns null for invalid JSON', () => {
    expect(parsePasteJson('{')).toBeNull();
    expect(parsePasteJson('not json')).toBeNull();
  });

  it('returns null for truncated JSON (Unexpected end of JSON input)', () => {
    expect(parsePasteJson('{"blocks":')).toBeNull();
    expect(parsePasteJson('{"blocks":[{"text":')).toBeNull();
  });

  it('returns parsed object for valid RawDraftContentState-like JSON', () => {
    const valid = '{"blocks":[{"key":"a","text":"x","type":"unstyled","depth":0,' +
      '"inlineStyleRanges":[],"entityRanges":[]}],"entityMap":{}}';
    const result = parsePasteJson(valid);
    expect(result).not.toBeNull();
    expect(result).toHaveProperty('blocks');
    expect((result as { blocks: unknown[] }).blocks).toHaveLength(1);
  });
});
