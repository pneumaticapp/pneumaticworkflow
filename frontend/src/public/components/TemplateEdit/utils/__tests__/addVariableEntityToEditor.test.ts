import { EditorState } from 'draft-js';
import { addVariableEntityToEditor } from '../addVariableEntityToEditor';

const getPlainText = (editorState: EditorState): string =>
  editorState.getCurrentContent().getPlainText('\u0001');

describe('addVariableEntityToEditor', () => {
  it('inserts empty string when variable.title is undefined', () => {
    const initial = EditorState.createEmpty();
    const result = addVariableEntityToEditor(initial, {
      apiName: 'var-1',
    });
    expect(getPlainText(result)).toBe('');
  });

  it('inserts empty string when variable.title is null', () => {
    const initial = EditorState.createEmpty();
    const result = addVariableEntityToEditor(initial, {
      title: null as unknown as undefined,
      apiName: 'var-1',
    });
    expect(getPlainText(result)).toBe('');
  });

  it('inserts empty string when variable.title is empty string', () => {
    const initial = EditorState.createEmpty();
    const result = addVariableEntityToEditor(initial, {
      title: '',
      apiName: 'var-1',
    });
    expect(getPlainText(result)).toBe('');
  });

  it('inserts variable.title when provided', () => {
    const initial = EditorState.createEmpty();
    const result = addVariableEntityToEditor(initial, {
      title: 'Client name',
      apiName: 'client-name',
    });
    expect(getPlainText(result)).toBe('Client name');
  });

  it('returns new EditorState instance', () => {
    const initial = EditorState.createEmpty();
    const result = addVariableEntityToEditor(initial, {
      title: 'X',
      apiName: 'x',
    });
    expect(result).not.toBe(initial);
    expect(result.getCurrentContent()).not.toBe(initial.getCurrentContent());
  });
});
