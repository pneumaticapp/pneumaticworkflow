import {
  prepareChecklistsForAPI,
  extractChecklistsFromMarkdown,
} from '../prepareChecklistsForAPI';

/**
 * Tests for prepareChecklistsForAPI and extractChecklistsFromMarkdown.
 * Covers parsing of checklist markdown [clist:listApiName|itemApiName]value[/clist]
 * and aggregation into TOutputChecklist for API.
 */
describe('prepareChecklistsForAPI', () => {
  describe('extractChecklistsFromMarkdown', () => {
    it('returns empty array for empty string', () => {
      expect(extractChecklistsFromMarkdown('')).toEqual([]);
    });

    it('returns empty array when text has no checklist tags', () => {
      expect(extractChecklistsFromMarkdown('Plain text\nand another line')).toEqual([]);
    });

    it('extracts one checklist item with empty value', () => {
      const markdown = '[clist:list-1|item-1][/clist]';
      expect(extractChecklistsFromMarkdown(markdown)).toEqual([
        { listApiName: 'list-1', itemApiName: 'item-1', value: '' },
      ]);
    });

    it('extracts single checklist item with value', () => {
      const markdown = '[clist:list-1|item-1]Item one[/clist]';
      expect(extractChecklistsFromMarkdown(markdown)).toEqual([
        { listApiName: 'list-1', itemApiName: 'item-1', value: 'Item one' },
      ]);
    });

    it('extracts multiple items from same list', () => {
      const markdown = [
        '[clist:list-a|item-1]First[/clist]',
        '[clist:list-a|item-2]Second[/clist]',
      ].join('\n');
      expect(extractChecklistsFromMarkdown(markdown)).toEqual([
        { listApiName: 'list-a', itemApiName: 'item-1', value: 'First' },
        { listApiName: 'list-a', itemApiName: 'item-2', value: 'Second' },
      ]);
    });

    it('extracts items from different lists', () => {
      const markdown = [
        '[clist:list-1|sel-1]A[/clist]',
        '[clist:list-2|sel-1]B[/clist]',
      ].join('\n');
      expect(extractChecklistsFromMarkdown(markdown)).toEqual([
        { listApiName: 'list-1', itemApiName: 'sel-1', value: 'A' },
        { listApiName: 'list-2', itemApiName: 'sel-1', value: 'B' },
      ]);
    });

    it('supports apiName with hyphens', () => {
      const markdown = '[clist:my-list-1|my-item-1]Text[/clist]';
      expect(extractChecklistsFromMarkdown(markdown)).toEqual([
        { listApiName: 'my-list-1', itemApiName: 'my-item-1', value: 'Text' },
      ]);
    });

    it('ignores unclosed tag (no regex match)', () => {
      const markdown = '[clist:list-1|item-1]No closing';
      expect(extractChecklistsFromMarkdown(markdown)).toEqual([]);
    });
  });

  describe('prepareChecklistsForAPI', () => {
    it('returns empty array for empty string', () => {
      expect(prepareChecklistsForAPI('')).toEqual([]);
    });

    it('returns one checklist with one selection', () => {
      const markdown = '[clist:list-1|item-1]Item[/clist]';
      expect(prepareChecklistsForAPI(markdown)).toEqual([
        { apiName: 'list-1', selections: [{ apiName: 'item-1', value: 'Item' }] },
      ]);
    });

    it('groups items with same listApiName into one checklist', () => {
      const markdown = [
        '[clist:list-1|item-1]First[/clist]',
        '[clist:list-1|item-2]Second[/clist]',
      ].join('\n');
      expect(prepareChecklistsForAPI(markdown)).toEqual([
        {
          apiName: 'list-1',
          selections: [
            { apiName: 'item-1', value: 'First' },
            { apiName: 'item-2', value: 'Second' },
          ],
        },
      ]);
    });

    it('splits items with different listApiName into separate checklists', () => {
      const markdown = [
        '[clist:list-a|item-1]A1[/clist]',
        '[clist:list-b|item-1]B1[/clist]',
        '[clist:list-a|item-2]A2[/clist]',
      ].join('\n');
      expect(prepareChecklistsForAPI(markdown)).toEqual([
        { apiName: 'list-a', selections: [{ apiName: 'item-1', value: 'A1' }] },
        { apiName: 'list-b', selections: [{ apiName: 'item-1', value: 'B1' }] },
        { apiName: 'list-a', selections: [{ apiName: 'item-2', value: 'A2' }] },
      ]);
    });

    it('preserves empty value in selection', () => {
      const markdown = '[clist:list-1|item-1][/clist]';
      expect(prepareChecklistsForAPI(markdown)).toEqual([
        { apiName: 'list-1', selections: [{ apiName: 'item-1', value: '' }] },
      ]);
    });

    it('handles markdown with text around checklists', () => {
      const markdown = 'Text before\n[clist:list-1|item-1]Item[/clist]\nText after';
      expect(prepareChecklistsForAPI(markdown)).toEqual([
        { apiName: 'list-1', selections: [{ apiName: 'item-1', value: 'Item' }] },
      ]);
    });
  });
});
