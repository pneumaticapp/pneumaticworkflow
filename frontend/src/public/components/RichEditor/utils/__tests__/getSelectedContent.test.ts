import { EditorState, SelectionState, convertFromRaw } from 'draft-js';
import { RawDraftContentState } from 'draft-js';
import { getSelectedContent } from '../getSelectedContent';
import { ECustomEditorEntities } from '../types';

describe('getSelectedContent', () => {
  it('expands selection to include full variable when only part of variable is selected', () => {
    const raw: RawDraftContentState = {
      blocks: [
        {
          key: 'block1',
          text: 'Hello xy',
          type: 'unstyled',
          depth: 0,
          inlineStyleRanges: [],
          entityRanges: [{ offset: 6, length: 2, key: 0 }],
        },
      ],
      entityMap: {
        '0': {
          type: ECustomEditorEntities.Variable,
          mutability: 'IMMUTABLE' as const,
          data: { apiName: 'v1', title: 'xy' },
        },
      },
    };
    const contentState = convertFromRaw(raw);
    const blockKey = contentState.getBlockMap().keySeq().first()!;
    const selection = new SelectionState({
      anchorKey: blockKey,
      anchorOffset: 6,
      focusKey: blockKey,
      focusOffset: 7,
      isBackward: false,
      hasFocus: true,
    });
    const editorState = EditorState.forceSelection(
      EditorState.createWithContent(contentState),
      selection,
    );

    const result = getSelectedContent(editorState);
    expect(result).not.toBeNull();
    expect(result!.getPlainText()).toBe('xy');
    expect(result!.getBlockMap().first()!.getCharacterList().size).toBe(2);
  });

  it('expands selection when selection starts in the middle of a variable', () => {
    const raw: RawDraftContentState = {
      blocks: [
        {
          key: 'block1',
          text: 'abVar',
          type: 'unstyled',
          depth: 0,
          inlineStyleRanges: [],
          entityRanges: [{ offset: 2, length: 3, key: 0 }],
        },
      ],
      entityMap: {
        '0': {
          type: ECustomEditorEntities.Variable,
          mutability: 'IMMUTABLE' as const,
          data: { apiName: 'v1', title: 'Var' },
        },
      },
    };
    const contentState = convertFromRaw(raw);
    const blockKey = contentState.getBlockMap().keySeq().first()!;
    const selection = new SelectionState({
      anchorKey: blockKey,
      anchorOffset: 3,
      focusKey: blockKey,
      focusOffset: 5,
      isBackward: false,
      hasFocus: true,
    });
    const editorState = EditorState.forceSelection(
      EditorState.createWithContent(contentState),
      selection,
    );

    const result = getSelectedContent(editorState);
    expect(result).not.toBeNull();
    expect(result!.getPlainText()).toBe('Var');
  });

  it('returns null when selection is collapsed', () => {
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
    const blockKey = contentState.getBlockMap().keySeq().first()!;
    const selection = SelectionState.createEmpty(blockKey);
    const editorState = EditorState.forceSelection(
      EditorState.createWithContent(contentState),
      selection,
    );

    const result = getSelectedContent(editorState);
    expect(result).toBeNull();
  });
});
