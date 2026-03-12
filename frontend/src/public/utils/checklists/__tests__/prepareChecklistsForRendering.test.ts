import { prepareChecklistsForRendering } from '../prepareChecklistsForRendering';

/**
 * Spec §7.3: prepareChecklistsForRendering prepares markdown for Lexical so that
 * checklist tags [clist:listApiName|itemApiName]...[/clist] are on their own line.
 */
describe('prepareChecklistsForRendering', () => {
  it('returns unchanged string when no checklist pattern', () => {
    expect(prepareChecklistsForRendering('Plain text')).toBe('Plain text');
    expect(prepareChecklistsForRendering('')).toBe('');
  });

  it('adds newline before [clist: when preceded by non-empty line', () => {
    const input = 'Some line[clist:list-1|item-1]Item[/clist]';
    const result = prepareChecklistsForRendering(input);
    expect(result).toBe('Some line\n[clist:list-1|item-1]Item[/clist]');
  });

  it('does not add newline when prevLine is empty/whitespace', () => {
    const input = '\n[clist:list-1|item-1]Item[/clist]';
    const result = prepareChecklistsForRendering(input);
    expect(result).toBe('\n[clist:list-1|item-1]Item[/clist]');
  });

  it('does not add newline when prevLine already contains [/clist]', () => {
    const input = '[/clist][clist:list-2|item-1]Next[/clist]';
    const result = prepareChecklistsForRendering(input);
    expect(result).toBe('[/clist][clist:list-2|item-1]Next[/clist]');
  });

  it('handles multiple checklist openings in one string', () => {
    const input = 'Line1[clist:a|1]A[/clist]\nLine2[clist:b|1]B[/clist]';
    const result = prepareChecklistsForRendering(input);
    expect(result).toContain('Line1\n[clist:a|1]');
    expect(result).toContain('Line2\n[clist:b|1]');
  });

  it('supports apiName and itemApiName with hyphens', () => {
    const input = 'Text[clist:my-list|my-item]Value[/clist]';
    expect(prepareChecklistsForRendering(input)).toBe('Text\n[clist:my-list|my-item]Value[/clist]');
  });
});
