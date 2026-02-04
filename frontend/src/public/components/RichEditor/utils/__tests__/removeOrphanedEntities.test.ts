import { EditorState, ContentState, convertFromRaw } from 'draft-js';
import { RawDraftContentState } from 'draft-js';
import { removeOrphanedEntities } from '../removeOrphanedEntities';

describe('removeOrphanedEntities', () => {
  it('returns same editorState when block type is not unstyled', () => {
    const raw: RawDraftContentState = {
      blocks: [{ key: 'a', text: '', type: 'header-one', depth: 0, inlineStyleRanges: [], entityRanges: [] }],
      entityMap: {},
    };
    const contentState = convertFromRaw(raw);
    const editorState = EditorState.createWithContent(contentState);

    const result = removeOrphanedEntities(editorState);

    expect(result).toBe(editorState);
  });

  it('returns same editorState for plain text without atomic entities', () => {
    const contentState = ContentState.createFromText('hello');
    const editorState = EditorState.createWithContent(contentState);

    const result = removeOrphanedEntities(editorState);

    expect(result).toBe(editorState);
  });
});
