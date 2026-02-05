import { getInitialLexicalState } from '../convertMarkdownToLexical';

describe('getInitialLexicalState', () => {
  it('returns string as-is when no checklist tokens', () => {
    expect(getInitialLexicalState('Hello')).toBe('Hello');
    expect(getInitialLexicalState('**bold** and *italic*')).toBe(
      '**bold** and *italic*',
    );
  });

  it('normalizes checklist tokens for rendering (prepareChecklistsForRendering)', () => {
    const withChecklist = 'Line one\n[clist:ListApi|ItemApi]';
    const result = getInitialLexicalState(withChecklist);
    expect(result).toContain('[clist:ListApi|ItemApi]');
  });

  it('adds newline before checklist opening when previous line has content', () => {
    const text = 'Some text[clist:list|item]';
    const result = getInitialLexicalState(text);
    expect(result).toBe('Some text\n[clist:list|item]');
  });
});
