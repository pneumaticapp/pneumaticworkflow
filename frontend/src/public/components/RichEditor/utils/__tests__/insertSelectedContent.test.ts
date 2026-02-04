import { EditorState, ContentState, SelectionState } from 'draft-js';
import { insertSelectedContent } from '../insertSelectedContent';

describe('insertSelectedContent', () => {
  it('returns editorState when selectedContentState is null', () => {
    const editorState = EditorState.createWithContent(ContentState.createFromText('hello'));
    expect(insertSelectedContent(editorState, null as any)).toBe(editorState);
  });

  it('inserts content at selection and updates editor state', () => {
    const contentState = ContentState.createFromText('hello world');
    const selection = SelectionState.createEmpty(contentState.getFirstBlock().getKey()).merge({
      anchorOffset: 5,
      focusOffset: 5,
    });
    const editorState = EditorState.forceSelection(
      EditorState.createWithContent(contentState),
      selection,
    );
    const fragmentContent = ContentState.createFromText('X');

    const result = insertSelectedContent(editorState, fragmentContent);

    expect(result).not.toBe(editorState);
    expect(result.getCurrentContent().getPlainText()).toContain('X');
  });
});
