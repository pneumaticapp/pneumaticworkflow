import type { LexicalEditor } from 'lexical';
import { applyPlainTextToEditor } from '../convertPlainTextToLexical';

const mockParseTextWithVariables = jest.fn();
const mockGetRoot = jest.fn();
const mockCreateParagraphNode = jest.fn();

jest.mock('lexical', () => {
  const actual = jest.requireActual('lexical');
  return {
    ...actual,
    $getRoot: () => mockGetRoot(),
    $createParagraphNode: () => mockCreateParagraphNode(),
  };
});

const mockRemoveUnknownVariableTokens = jest.fn();

jest.mock('../variableMarkdown', () => ({
  parseTextWithVariables: (
    text: string,
    templateVariables?: unknown,
    options?: { variablesOnly?: boolean },
  ) => mockParseTextWithVariables(text, templateVariables, options),
  removeUnknownVariableTokens: (text: string, templateVariables?: unknown) =>
    mockRemoveUnknownVariableTokens(text, templateVariables),
}));

describe('applyPlainTextToEditor', () => {
  let editor: LexicalEditor;

  beforeEach(() => {
    jest.clearAllMocks();
    mockParseTextWithVariables.mockReturnValue([]);
    mockRemoveUnknownVariableTokens.mockImplementation((text: string) => text);
    mockCreateParagraphNode.mockReturnValue({ append: jest.fn() });
    mockGetRoot.mockReturnValue({ clear: jest.fn(), append: jest.fn() });
    editor = {
      update: jest.fn((callback: () => void) => {
        callback();
      }),
    } as unknown as LexicalEditor;
  });

  it('parses variables only, not markdown syntax', () => {
    applyPlainTextToEditor(editor, '**urgent** {{date}}');

    expect(mockRemoveUnknownVariableTokens).toHaveBeenCalledWith('**urgent** {{date}}', undefined);
    expect(mockParseTextWithVariables).toHaveBeenCalledWith(
      '**urgent** {{date}}',
      undefined,
      { variablesOnly: true },
    );
  });
});
