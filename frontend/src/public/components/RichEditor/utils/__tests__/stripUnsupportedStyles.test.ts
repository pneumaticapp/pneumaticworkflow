import { EditorState, ContentState } from 'draft-js';
import { stripUnsupportedStyles } from '../stripUnsupportedStyles';

describe('stripUnsupportedStyles', () => {
  it('returns nextState when content unchanged', () => {
    const contentState = ContentState.createFromText('same');
    const editorState = EditorState.createWithContent(contentState);
    const nextState = EditorState.createWithContent(contentState);

    const result = stripUnsupportedStyles(nextState, editorState);

    expect(result).toBe(nextState);
  });

  it('returns nextState when last change type is not insert-fragment', () => {
    const currentContent = ContentState.createFromText('a');
    const nextContent = ContentState.createFromText('ab');
    const currentState = EditorState.createWithContent(currentContent);
    const nextState = EditorState.createWithContent(nextContent);

    const result = stripUnsupportedStyles(nextState, currentState);

    expect(result.getCurrentContent().getPlainText()).toBe('ab');
  });
});
