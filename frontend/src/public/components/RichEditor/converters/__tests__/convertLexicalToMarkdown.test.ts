import type { EditorState } from 'lexical';
import { convertLexicalToMarkdown } from '../convertLexicalToMarkdown';

const mockConvertToMarkdown = jest.fn();
jest.mock('@lexical/markdown', () => ({
  $convertToMarkdownString: (transformers: unknown) => mockConvertToMarkdown(transformers),
}));

describe('convertLexicalToMarkdown', () => {
  const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

  beforeEach(() => {
    jest.clearAllMocks();
    consoleSpy.mockClear();
  });

  afterAll(() => {
    consoleSpy.mockRestore();
  });

  it('calls editorState.read with callback', () => {
    const read = jest.fn((cb: () => void) => cb());
    const editorState = { read } as unknown as EditorState;
    mockConvertToMarkdown.mockReturnValue('# Markdown');
    convertLexicalToMarkdown(editorState);
    expect(read).toHaveBeenCalledTimes(1);
    expect(typeof read.mock.calls[0][0]).toBe('function');
  });

  it('returns result of $convertToMarkdownString', () => {
    const editorState = {
      read: (cb: () => void) => cb(),
    } as unknown as EditorState;
    mockConvertToMarkdown.mockReturnValue('**bold** text');
    expect(convertLexicalToMarkdown(editorState)).toBe('**bold** text');
  });

  it('returns empty string when error is thrown in read', () => {
    const editorState = {
      read: (cb: () => void) => {
        cb();
      },
    } as unknown as EditorState;
    mockConvertToMarkdown.mockImplementation(() => {
      throw new Error('Conversion failed');
    });
    expect(convertLexicalToMarkdown(editorState)).toBe('');
  });

  it('logs error to console.error on exception', () => {
    const editorState = {
      read: (cb: () => void) => cb(),
    } as unknown as EditorState;
    const err = new Error('Conversion failed');
    mockConvertToMarkdown.mockImplementation(() => {
      throw err;
    });
    convertLexicalToMarkdown(editorState);
    expect(consoleSpy).toHaveBeenCalledWith('❌ Error converting lexical to markdown:', err);
  });

  it('returns empty string when read throws', () => {
    const editorState = {
      read: () => {
        throw new Error('Read failed');
      },
    } as unknown as EditorState;
    expect(convertLexicalToMarkdown(editorState)).toBe('');
    expect(consoleSpy).toHaveBeenCalled();
  });
});
