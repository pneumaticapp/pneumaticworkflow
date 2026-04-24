import { createChecklistTransformer } from '../checklistMarkdown';
import { EExtraFieldType } from '../../../../types/template';

describe('checklistMarkdown', () => {
  describe('createChecklistTransformer', () => {
    it('returns transformer with required MultilineElementTransformer shape', () => {
      const transformer = createChecklistTransformer();
      expect(transformer).toMatchObject({
        type: 'multiline-element',
        dependencies: expect.any(Array),
        regExpStart: expect.any(RegExp),
        regExpEnd: expect.any(RegExp),
      });
      expect(transformer.dependencies).toHaveLength(2);
      expect(typeof transformer.export).toBe('function');
      expect(typeof transformer.replace).toBe('function');
    });

    it('regExpStart matches [clist:listApi|itemApi] pattern', () => {
      const transformer = createChecklistTransformer();
      expect('[clist:my-list|item-1]').toMatch(transformer.regExpStart);
      expect('[clist:list_1|item_2]').toMatch(transformer.regExpStart);
      expect('plain text').not.toMatch(transformer.regExpStart);
    });

    it('regExpEnd matches [/clist]', () => {
      const transformer = createChecklistTransformer();
      const endRe =
        transformer.regExpEnd && typeof transformer.regExpEnd === 'object' && 'regExp' in transformer.regExpEnd
          ? (transformer.regExpEnd as { regExp: RegExp }).regExp
          : (transformer.regExpEnd as RegExp);
      expect(endRe).toBeDefined();
      expect('[/clist]').toMatch(endRe);
    });

    it('accepts optional templateVariables', () => {
      const transformer = createChecklistTransformer([]);
      expect(transformer.regExpStart).toBeDefined();
      const withVars = createChecklistTransformer([
        { apiName: 'v1', title: 'Var 1', subtitle: '', type: EExtraFieldType.Text },
      ]);
      expect(withVars.regExpStart).toBeDefined();
    });
  });
});
