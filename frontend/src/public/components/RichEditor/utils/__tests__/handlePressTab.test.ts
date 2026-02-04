import { EditorState, ContentState } from 'draft-js';
import { handlePressTab } from '../handlePressTab';

describe('handlePressTab', () => {
  it('does not call handleChange when Tab has no effect on plain text', () => {
    const contentState = ContentState.createFromText('');
    const editorState = EditorState.createWithContent(contentState);
    const handleChange = jest.fn();
    const e = { key: 'Tab', keyCode: 9 } as unknown as React.KeyboardEvent;

    handlePressTab(e, editorState, handleChange);

    expect(handleChange).not.toHaveBeenCalled();
  });

  it('calls handleChange when Tab changes list depth', () => {
    const { RichUtils } = require('draft-js');
    const contentState = ContentState.createFromText('- item');
    let editorState = EditorState.createWithContent(contentState);
    editorState = RichUtils.toggleBlockType(editorState, 'unordered-list-item');
    const handleChange = jest.fn();
    const e = { key: 'Tab', keyCode: 9, preventDefault: jest.fn() } as unknown as React.KeyboardEvent;

    handlePressTab(e, editorState, handleChange);

    expect(handleChange).toHaveBeenCalledTimes(1);
    expect(handleChange.mock.calls[0][0]).not.toBe(editorState);
  });
});
