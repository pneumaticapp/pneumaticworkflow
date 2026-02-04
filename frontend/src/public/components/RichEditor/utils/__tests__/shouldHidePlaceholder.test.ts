import { EditorState, ContentState, convertFromRaw } from 'draft-js';
import { RawDraftContentState } from 'draft-js';
import { shouldHidePlaceholder } from '../shouldHidePlaceholder';

describe('shouldHidePlaceholder', () => {
  it('returns false when content is empty and first block is unstyled', () => {
    const contentState = ContentState.createFromText('');
    const editorState = EditorState.createWithContent(contentState);
    expect(shouldHidePlaceholder(editorState)).toBe(false);
  });

  it('returns true when content has text', () => {
    const contentState = ContentState.createFromText('Hello');
    const editorState = EditorState.createWithContent(contentState);
    expect(shouldHidePlaceholder(editorState)).toBe(true);
  });

  it('returns true when first block is not unstyled', () => {
    const raw: RawDraftContentState = {
      blocks: [{ key: 'a', text: '', type: 'header-one', depth: 0, inlineStyleRanges: [], entityRanges: [] }],
      entityMap: {},
    };
    const contentState = convertFromRaw(raw);
    const editorState = EditorState.createWithContent(contentState);
    expect(shouldHidePlaceholder(editorState)).toBe(true);
  });
});
