import React from 'react';
import { mount } from 'enzyme';
import { RichEditor } from '../lexical';
import type { IRichEditorProps } from '../lexical';

const defaultProps: IRichEditorProps = {
  placeholder: 'Placeholder',
  handleChange: jest.fn().mockResolvedValue(''),
  withToolbar: false,
  withMentions: false,
};

describe('RichEditor', () => {
  it('renders without crashing', () => {
    const wrapper = mount(<RichEditor {...defaultProps} />);
    expect(wrapper.find('.lexical-wrapper').length).toBe(1);
  });

  it('exposes focus, insertVariable, getEditor via ref', () => {
    const ref = React.createRef<any>();
    mount(<RichEditor {...defaultProps} ref={ref} />);
    expect(ref.current).not.toBeNull();
    expect(typeof ref.current.focus).toBe('function');
    expect(typeof ref.current.insertVariable).toBe('function');
    expect(typeof ref.current.getEditor).toBe('function');
  });

  it('renders title when provided', () => {
    const wrapper = mount(<RichEditor {...defaultProps} title="Editor title" />);
    expect(wrapper.text()).toContain('Editor title');
  });
});
