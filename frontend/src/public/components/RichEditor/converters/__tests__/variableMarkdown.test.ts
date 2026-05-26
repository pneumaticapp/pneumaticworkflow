import type { TTaskVariable } from '../../../TemplateEdit/types';
import { EExtraFieldType } from '../../../../types/template';
import { createVariableTransformer, getVariablePayload } from '../variableMarkdown';

/**
 * parseTextWithVariables and createVariableTransformer use $createTextNode, $createVariableNode,
 * $createMentionNode from Lexical, which require a registered editor in Jest (Lexical error #196).
 * So only transformer shape and getVariablePayload (variable found/not found) are tested here.
 */
describe('variableMarkdown', () => {
  describe('getVariablePayload (variable not found / found by apiName)', () => {
    it('when variable not in list: uses apiName as both apiName and title', () => {
      expect(getVariablePayload('unknown_var', [])).toEqual({
        apiName: 'unknown_var',
        title: 'unknown_var',
        subtitle: undefined,
      });
      expect(getVariablePayload('x', [{ apiName: 'other', title: 'Other', type: EExtraFieldType.Text }])).toEqual({
        apiName: 'x',
        title: 'x',
        subtitle: undefined,
      });
    });

    it('when templateVariables is undefined: uses apiName as title', () => {
      expect(getVariablePayload('foo')).toEqual({
        apiName: 'foo',
        title: 'foo',
        subtitle: undefined,
      });
    });

    it('when variable found by apiName: uses variable title and subtitle', () => {
      const list: TTaskVariable[] = [
        { apiName: 'var1', title: 'Variable One', subtitle: 'Hint 1', type: EExtraFieldType.Text },
        { apiName: 'var2', title: 'Variable Two', type: EExtraFieldType.String },
      ];
      expect(getVariablePayload('var1', list)).toEqual({
        apiName: 'var1',
        title: 'Variable One',
        subtitle: 'Hint 1',
      });
      expect(getVariablePayload('var2', list)).toEqual({
        apiName: 'var2',
        title: 'Variable Two',
        subtitle: undefined,
      });
    });
  });

  describe('createVariableTransformer', () => {
    it('returns object with type text-match and dependencies array', () => {
      const transformer = createVariableTransformer();
      expect(transformer.type).toBe('text-match');
      expect(transformer.dependencies).toBeDefined();
      expect(Array.isArray(transformer.dependencies)).toBe(true);
    });

    it('has export function', () => {
      const transformer = createVariableTransformer();
      expect(typeof transformer.export).toBe('function');
    });

    it('has importRegExp and regExp', () => {
      const transformer = createVariableTransformer();
      expect(transformer.importRegExp).toBeInstanceOf(RegExp);
      expect(transformer.regExp).toBeInstanceOf(RegExp);
    });
  });
});
