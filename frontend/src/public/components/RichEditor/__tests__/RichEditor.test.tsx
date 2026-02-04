/* eslint-disable */
import * as React from 'react';
import { mount } from 'enzyme';
import { act } from 'react-dom/test-utils';
import { EditorState, ContentState } from 'draft-js';
import { RichEditor } from '../RichEditor';
import { IRichEditorProps } from '../RichEditor.props';

jest.mock('@draft-js-plugins/editor', () => {
  const React = require('react');
  const domOnlyProps = ['className', 'placeholder', 'spellCheck', 'tabIndex', 'ariaLabel', 'data-testid'];
  return {
    __esModule: true,
    default: React.forwardRef((props: any, ref: any) => {
      const safeProps: any = {};
      domOnlyProps.forEach((k) => { if (props[k] !== undefined) safeProps[k] = props[k]; });
      return <div ref={ref} data-testid="draft-editor" {...safeProps} />;
    }),
    composeDecorators: (x: any) => x,
  };
});

jest.mock('@draft-js-plugins/linkify', () => ({ __esModule: true, default: () => ({}) }));
jest.mock('draft-js-mention-plugin', () => ({
  __esModule: true,
  default: () => ({ MentionSuggestions: () => null }),
}));
jest.mock('@draft-js-plugins/focus', () => ({ __esModule: true, default: () => ({ decorator: () => () => null }) }));
jest.mock('@draft-js-plugins/static-toolbar', () => ({
  __esModule: true,
  default: () => ({ Toolbar: ({ children }: any) => <div data-testid="toolbar">{typeof children === 'function' ? children({ theme: {} }) : null}</div> }),
}));
jest.mock('../utils/linksPlugin', () => ({
  __esModule: true,
  default: () => ({ LinkButton: () => null, AddLinkForm: () => null }),
}));
jest.mock('../utils/checklistsPlugin', () => ({ __esModule: true, default: () => ({ ChecklistButton: () => null }) }));
jest.mock('../utils/AttachmentsPlugin', () => ({
  __esModule: true,
  default: () => ({ addAttachment: () => {}, decorator: () => () => null }),
}));
jest.mock('../../media', () => ({
  Desktop: ({ children }: any) => <div data-testid="desktop">{children}</div>,
  Mobile: ({ children }: any) => <div data-testid="mobile">{children}</div>,
}));

const defaultProps: IRichEditorProps = {
  accountId: 1,
  mentions: [],
  placeholder: 'Placeholder',
  handleChange: jest.fn().mockResolvedValue(''),
  withToolbar: false,
  withMentions: false,
};

describe('RichEditor', () => {
  it('renders without crashing', () => {
    const wrapper = mount(<RichEditor {...defaultProps} />);
    expect(wrapper.find('[data-testid="draft-editor"]').length).toBe(1);
  });

  it('exposes focus, getEditorState, onChange via ref', () => {
    const ref = React.createRef<any>();
    mount(<RichEditor {...defaultProps} ref={ref} />);
    expect(ref.current).not.toBeNull();
    expect(typeof ref.current.focus).toBe('function');
    expect(typeof ref.current.getEditorState).toBe('function');
    expect(typeof ref.current.onChange).toBe('function');
  });

  it('getEditorState returns current editor state', () => {
    const ref = React.createRef<any>();
    mount(<RichEditor {...defaultProps} ref={ref} />);
    const state = ref.current.getEditorState();
    expect(state).toBeInstanceOf(EditorState);
    expect(state.getCurrentContent().getPlainText()).toBe('');
  });

  it('onChange updates state and calls handleChange', async () => {
    const handleChange = jest.fn().mockResolvedValue('');
    const ref = React.createRef<any>();
    mount(<RichEditor {...defaultProps} ref={ref} handleChange={handleChange} />);
    const newContent = ContentState.createFromText('hello');
    const newState = EditorState.createWithContent(newContent);
    await act(async () => {
      await ref.current.onChange(newState);
    });
    expect(handleChange).toHaveBeenCalled();
  });

  it('renders title when provided', () => {
    const wrapper = mount(<RichEditor {...defaultProps} title="Editor title" />);
    expect(wrapper.text()).toContain('Editor title');
  });
});
