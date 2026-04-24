import {
  removeDuplicateClipboardParagraphs,
  nodesContainChecklist,
} from '../checklistPluginUtils';

/**
 * ChecklistPlugin utils tests. Functions that create Lexical nodes ($createParagraphNode,
 * $createChecklistNode, etc.) require an active editor (Lexical error #196), so only
 * empty-array scenarios are tested here. Rest is covered by integration tests with editor.
 */
describe('checklistPluginUtils', () => {
  describe('removeDuplicateClipboardParagraphs', () => {
    it('returns empty array for empty input', () => {
      expect(removeDuplicateClipboardParagraphs([])).toEqual([]);
    });
  });

  describe('nodesContainChecklist', () => {
    it('returns false for empty array', () => {
      expect(nodesContainChecklist([])).toBe(false);
    });
  });
});
