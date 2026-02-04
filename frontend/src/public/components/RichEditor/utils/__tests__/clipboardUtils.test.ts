import { EExtraFieldType } from '../../../../types/template';
import { contentStateFromPastedText, isPastedContentWithVariables } from '../clipboardUtils';

describe('clipboardUtils', () => {
  describe('isPastedContentWithVariables', () => {
    it('returns true when text contains variable syntax', () => {
      expect(isPastedContentWithVariables('Hello {{field-xxx}}')).toBe(true);
      expect(isPastedContentWithVariables('{{var}}')).toBe(true);
      expect(isPastedContentWithVariables('text {{a}} more')).toBe(true);
    });

    it('returns false when text has no variable syntax', () => {
      expect(isPastedContentWithVariables('Hello world')).toBe(false);
      expect(isPastedContentWithVariables('')).toBe(false);
      expect(isPastedContentWithVariables('{not closed')).toBe(false);
    });
  });

  describe('contentStateFromPastedText', () => {
    const templateVariables = [
      { title: 'My Var', apiName: 'field-xxx', type: EExtraFieldType.String },
    ];

    it('returns ContentState when text has variable syntax and variable is in template', () => {
      const result = contentStateFromPastedText('Hello {{field-xxx}}', templateVariables);
      expect(result).not.toBeNull();
      expect(result!.getPlainText()).toContain('My Var');
    });

    it('returns null when text has no variable syntax', () => {
      expect(contentStateFromPastedText('Hello world', templateVariables)).toBeNull();
    });
  });
});
