import { VariableNode } from '../VariableNode';

/**
 * VariableNode extends Lexical DecoratorNode; constructing it (new VariableNode(...)) requires
 * a registered editor in Jest (Lexical error #196). So only the static getType() is tested here.
 * Clone, exportJSON, getTextContent, copy/paste/delete behaviour are covered in E2E or integration.
 */
describe('VariableNode', () => {
  describe('getType', () => {
    it('returns "variable"', () => {
      expect(VariableNode.getType()).toBe('variable');
    });
  });
});
