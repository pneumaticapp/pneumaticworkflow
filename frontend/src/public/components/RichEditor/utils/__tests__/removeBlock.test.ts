import { EditorState, ContentState } from 'draft-js';
import { removeBlock } from '../removeBlock';

describe('removeBlock', () => {
  it('removes the only block and leaves empty unstyled block', () => {
    const contentState = ContentState.createFromText('x');
    const editorState = EditorState.createWithContent(contentState);
    const blockKey = contentState.getFirstBlock().getKey();

    const result = removeBlock(editorState, blockKey);

    expect(result.getCurrentContent().getPlainText()).toBe('');
    expect(result.getCurrentContent().getBlockMap().size).toBe(1);
    expect(result.getCurrentContent().getFirstBlock().getType()).toBe('unstyled');
  });

  it('removes second block and leaves one block', () => {
    const contentState = ContentState.createFromText('first\nsecond');
    const editorState = EditorState.createWithContent(contentState);
    const blockMap = contentState.getBlockMap();
    const secondBlockKey = blockMap.keySeq().skip(1).first()!;

    const result = removeBlock(editorState, secondBlockKey);

    expect(result.getCurrentContent().getBlockMap().size).toBe(1);
    expect(result.getCurrentContent().getPlainText()).toContain('first');
  });
});
