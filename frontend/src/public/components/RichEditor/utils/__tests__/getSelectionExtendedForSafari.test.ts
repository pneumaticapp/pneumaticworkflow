import { EditorState, SelectionState, convertFromRaw } from 'draft-js';
import { RawDraftContentState } from 'draft-js';
import { getSelectionExtendedForSafari } from '../getSelectionExtendedForSafari';
import { ECustomEditorEntities } from '../types';

jest.mock('../isSafari', () => ({
  isSafari: jest.fn(),
}));

const isSafariMock = jest.requireMock('../isSafari').isSafari as jest.Mock;

function createEditorStateWithVariableAtEnd(selectionFocusOffset: number): EditorState {
  const raw: RawDraftContentState = {
    blocks: [
      {
        key: 'block1',
        text: 'Hello x',
        type: 'unstyled',
        depth: 0,
        inlineStyleRanges: [],
        entityRanges: [{ offset: 6, length: 1, key: 0 }],
      },
    ],
    entityMap: {
      '0': {
        type: ECustomEditorEntities.Variable,
        mutability: 'IMMUTABLE' as const,
        data: { apiName: 'v1', title: 'x' },
      },
    },
  };
  const contentState = convertFromRaw(raw);
  const blockKey = contentState.getBlockMap().keySeq().first();
  const selection = new SelectionState({
    anchorKey: blockKey,
    anchorOffset: 0,
    focusKey: blockKey,
    focusOffset: selectionFocusOffset,
    isBackward: false,
    hasFocus: true,
  });
  return EditorState.forceSelection(EditorState.createWithContent(contentState), selection);
}

function createEditorStateWithTextAfterVariable(selectionFocusOffset: number): EditorState {
  const raw: RawDraftContentState = {
    blocks: [
      {
        key: 'block1',
        text: 'Hello x!',
        type: 'unstyled',
        depth: 0,
        inlineStyleRanges: [],
        entityRanges: [{ offset: 6, length: 1, key: 0 }],
      },
    ],
    entityMap: {
      '0': {
        type: ECustomEditorEntities.Variable,
        mutability: 'IMMUTABLE' as const,
        data: { apiName: 'v1', title: 'x' },
      },
    },
  };
  const contentState = convertFromRaw(raw);
  const blockKey = contentState.getBlockMap().keySeq().first();
  const selection = new SelectionState({
    anchorKey: blockKey,
    anchorOffset: 0,
    focusKey: blockKey,
    focusOffset: selectionFocusOffset,
    isBackward: false,
    hasFocus: true,
  });
  return EditorState.forceSelection(EditorState.createWithContent(contentState), selection);
}

describe('getSelectionExtendedForSafari', () => {
  beforeEach(() => {
    isSafariMock.mockReset();
  });

  it('returns same selection when not Safari', () => {
    isSafariMock.mockReturnValue(false);
    const editorState = createEditorStateWithVariableAtEnd(6);
    const result = getSelectionExtendedForSafari(editorState);
    expect(result.getFocusOffset()).toBe(6);
    expect(result.getEndOffset()).toBe(6);
  });

  it('does not extend in Safari when selection is a range (partial copy); only extends when collapsed', () => {
    isSafariMock.mockReturnValue(true);
    const editorState = createEditorStateWithVariableAtEnd(6);
    const result = getSelectionExtendedForSafari(editorState);
    expect(result.getFocusOffset()).toBe(6);
  });

  it('does not extend in Safari when tail contains non-Variable (plain text)', () => {
    isSafariMock.mockReturnValue(true);
    const editorState = createEditorStateWithTextAfterVariable(6);
    const result = getSelectionExtendedForSafari(editorState);
    expect(result.getFocusOffset()).toBe(6);
  });

  it('returns same selection when already at block end', () => {
    isSafariMock.mockReturnValue(true);
    const editorState = createEditorStateWithVariableAtEnd(7);
    const result = getSelectionExtendedForSafari(editorState);
    expect(result.getFocusOffset()).toBe(7);
  });

  it('returns same selection when collapsed at start of block', () => {
    isSafariMock.mockReturnValue(true);
    const raw: RawDraftContentState = {
      blocks: [
        {
          key: 'block1',
          text: 'Hello x',
          type: 'unstyled',
          depth: 0,
          inlineStyleRanges: [],
          entityRanges: [{ offset: 6, length: 1, key: 0 }],
        },
      ],
      entityMap: {
        '0': {
          type: ECustomEditorEntities.Variable,
          mutability: 'IMMUTABLE' as const,
          data: { apiName: 'v1', title: 'x' },
        },
      },
    };
    const contentState = convertFromRaw(raw);
    const blockKey = contentState.getBlockMap().keySeq().first();
    const selection = SelectionState.createEmpty(blockKey!);
    const editorState = EditorState.forceSelection(
      EditorState.createWithContent(contentState),
      selection,
    );
    const result = getSelectionExtendedForSafari(editorState);
    expect(result.getFocusOffset()).toBe(0);
    expect(result.isCollapsed()).toBe(true);
  });

  it('expands collapsed selection to full block in Safari when cursor is at end with variable', () => {
    isSafariMock.mockReturnValue(true);
    const raw: RawDraftContentState = {
      blocks: [
        {
          key: 'block1',
          text: 'Hello x',
          type: 'unstyled',
          depth: 0,
          inlineStyleRanges: [],
          entityRanges: [{ offset: 6, length: 1, key: 0 }],
        },
      ],
      entityMap: {
        '0': {
          type: ECustomEditorEntities.Variable,
          mutability: 'IMMUTABLE' as const,
          data: { apiName: 'v1', title: 'x' },
        },
      },
    };
    const contentState = convertFromRaw(raw);
    const blockKey = contentState.getBlockMap().keySeq().first();
    const selection = new SelectionState({
      anchorKey: blockKey!,
      anchorOffset: 7,
      focusKey: blockKey!,
      focusOffset: 7,
      isBackward: false,
      hasFocus: true,
    });
    const editorState = EditorState.forceSelection(
      EditorState.createWithContent(contentState),
      selection,
    );
    const result = getSelectionExtendedForSafari(editorState);
    expect(result.getAnchorOffset()).toBe(0);
    expect(result.getFocusOffset()).toBe(7);
    expect(result.isCollapsed()).toBe(false);
  });
});
