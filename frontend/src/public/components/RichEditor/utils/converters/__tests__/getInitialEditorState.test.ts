import { EditorState } from 'draft-js';
import { getInitialEditorState } from '../convertTextToDraft';
import { EExtraFieldType } from '../../../../../types/template';

describe('getInitialEditorState', () => {
  it('returns editor state for empty string', () => {
    const state = getInitialEditorState('', []);
    expect(state).toBeInstanceOf(EditorState);
    expect(state.getCurrentContent().getPlainText()).toBe('');
  });

  it('returns editor state with text', () => {
    const state = getInitialEditorState('Hello', []);
    expect(state.getCurrentContent().getPlainText()).toBe('Hello');
  });

  it('accepts variables and creates valid editor state', () => {
    const variables = [
      {
        title: 'Var',
        subtitle: 'Sub',
        richSubtitle: '',
        apiName: 'my-var',
        type: EExtraFieldType.String,
      },
    ];
    const state = getInitialEditorState('Text {{my-var}}', variables);
    expect(state).toBeInstanceOf(EditorState);
    expect(state.getCurrentContent().getPlainText()).toContain('Var');
  });
});
