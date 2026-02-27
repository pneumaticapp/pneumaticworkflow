import type { LexicalEditor } from 'lexical';
import { applyMarkdownToEditor } from '../convertMarkdownToLexical';

const mockPrepareChecklistsForRendering = jest.fn();
const mockConvertFromMarkdownString = jest.fn();

jest.mock('../../../../utils/checklists/prepareChecklistsForRendering', () => ({
  prepareChecklistsForRendering: (md: string) => mockPrepareChecklistsForRendering(md),
}));

jest.mock('@lexical/markdown', () => ({
  $convertFromMarkdownString: (prepared: string, _transformers: unknown) =>
    mockConvertFromMarkdownString(prepared),
}));

describe('applyMarkdownToEditor', () => {
  let editor: LexicalEditor;
  const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

  beforeEach(() => {
    jest.clearAllMocks();
    consoleSpy.mockClear();
    mockPrepareChecklistsForRendering.mockImplementation((s: string) => s);
    editor = {
      update: jest.fn((callback: () => void, options: { tag?: string }) => {
        callback();
      }),
    } as unknown as LexicalEditor;
  });

  afterAll(() => {
    consoleSpy.mockRestore();
  });

  it('calls prepareChecklistsForRendering with given markdown', () => {
    applyMarkdownToEditor(editor, '## Heading');
    expect(mockPrepareChecklistsForRendering).toHaveBeenCalledWith('## Heading');
  });

  it('calls editor.update with callback and default tag history-merge', () => {
    applyMarkdownToEditor(editor, 'text');
    expect(editor.update).toHaveBeenCalledTimes(1);
    const [callback, options] = (editor.update as jest.Mock).mock.calls[0];
    expect(typeof callback).toBe('function');
    expect(options).toEqual({ tag: 'history-merge' });
  });

  it('passes options.tag to editor.update', () => {
    applyMarkdownToEditor(editor, 'text', { tag: 'custom-tag' });
    expect((editor.update as jest.Mock).mock.calls[0][1]).toEqual({ tag: 'custom-tag' });
  });

  it('calls $convertFromMarkdownString with prepareChecklistsForRendering result inside update', () => {
    mockPrepareChecklistsForRendering.mockReturnValue('prepared-markdown');
    applyMarkdownToEditor(editor, 'raw');
    expect(mockConvertFromMarkdownString).toHaveBeenCalledWith('prepared-markdown');
  });

  it('on error in try logs to console.error and does not rethrow', () => {
    mockPrepareChecklistsForRendering.mockImplementation(() => {
      throw new Error('Prepare failed');
    });
    expect(() => applyMarkdownToEditor(editor, 'x')).not.toThrow();
    expect(consoleSpy).toHaveBeenCalledWith('❌ Error loading markdown into editor:', expect.any(Error));
  });

  it('on error in update callback logs and does not rethrow', () => {
    mockConvertFromMarkdownString.mockImplementation(() => {
      throw new Error('Convert failed');
    });
    expect(() => applyMarkdownToEditor(editor, 'x')).not.toThrow();
    expect(consoleSpy).toHaveBeenCalledWith('❌ Error loading markdown into editor:', expect.any(Error));
  });

  it('calls update when templateVariables are passed', () => {
    const { EExtraFieldType } = require('../../../../types/template');
    const templateVariables = [
      { apiName: 'var1', title: 'Var 1', subtitle: '', type: EExtraFieldType.Text },
    ];
    applyMarkdownToEditor(editor, '{{var1}}', { templateVariables });
    expect(editor.update).toHaveBeenCalled();
    expect(mockConvertFromMarkdownString).toHaveBeenCalled();
  });

  /**
   * Security: malicious or malformed markdown must not throw; conversion is best-effort.
   * Actual XSS prevention depends on Lexical rendering text as text, not raw HTML.
   */
  describe('security: resilient to malicious-looking input', () => {
    it('does not throw when markdown contains script-like content', () => {
      const malicious = 'text <script>alert(1)</script> more';
      expect(() => applyMarkdownToEditor(editor, malicious)).not.toThrow();
      expect(mockPrepareChecklistsForRendering).toHaveBeenCalledWith(malicious);
    });

    it('does not throw when markdown contains javascript: link', () => {
      const withJsLink = 'see [click](javascript:alert(1))';
      expect(() => applyMarkdownToEditor(editor, withJsLink)).not.toThrow();
    });

    it('does not throw on very long or repeated payload (basic DoS resilience)', () => {
      const long = 'x'.repeat(10000);
      expect(() => applyMarkdownToEditor(editor, long)).not.toThrow();
    });
  });
});
