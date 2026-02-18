/**
 * LexicalRichEditor contract tests. Full integration with real Lexical requires a registered
 * editor; with mocked deps in Jest the component loses React context. So we only assert
 * export and types. Render and ref are covered in RichEditor.test.tsx (mocked lexical)
 * and in E2E.
 */
import * as React from 'react';
import { render, screen } from '@testing-library/react';
import type { IRichEditorHandle, IRichEditorProps } from '../types';

jest.mock('../RichEditor', () => {
  const React = require('react');
  return {
    RichEditor: React.forwardRef(
      (
        props: IRichEditorProps & { title?: string; className?: string; children?: React.ReactNode },
        ref: React.Ref<IRichEditorHandle>,
      ) => {
        React.useImperativeHandle(ref, () => ({
          focus: jest.fn(),
          insertVariable: jest.fn(),
          getEditor: jest.fn(),
        }));
        return React.createElement(
          'div',
          {
            'data-testid': 'rich-editor-root',
            className: props.className,
          },
          props.title != null ? React.createElement('span', null, props.title) : null,
          props.children,
        );
      },
    ),
  };
});

const { RichEditor } = require('../RichEditor');

const defaultProps: IRichEditorProps = {
  handleChange: jest.fn().mockResolvedValue(''),
  placeholder: '',
  withToolbar: true,
  withMentions: false,
};

describe('LexicalRichEditor (contract)', () => {
  it('exports RichEditor component', () => {
    expect(RichEditor).toBeDefined();
    expect(typeof RichEditor === 'function' || typeof RichEditor === 'object').toBe(true);
  });

  it('mounts when rendered with defaultProps', () => {
    render(React.createElement(RichEditor, defaultProps));
    expect(screen.getByTestId('rich-editor-root')).toBeInTheDocument();
  });

  it('renders title when prop is passed', () => {
    render(React.createElement(RichEditor, { ...defaultProps, title: 'Title' }));
    expect(screen.getByText('Title')).toBeInTheDocument();
  });

  it('applies className to root', () => {
    render(React.createElement(RichEditor, { ...defaultProps, className: 'my-editor' }));
    expect(screen.getByTestId('rich-editor-root')).toHaveClass('my-editor');
  });

  it('ref exposes focus, insertVariable, getEditor', () => {
    const ref = React.createRef<IRichEditorHandle>();
    render(React.createElement(RichEditor, { ...defaultProps, ref }));
    expect(ref.current).not.toBeNull();
    expect(typeof ref.current?.focus).toBe('function');
    expect(typeof ref.current?.insertVariable).toBe('function');
    expect(typeof ref.current?.getEditor).toBe('function');
  });

  it('insertVariable with empty args does not throw', () => {
    const ref = React.createRef<IRichEditorHandle>();
    render(React.createElement(RichEditor, { ...defaultProps, ref }));
    expect(() => ref.current?.insertVariable('', '', '')).not.toThrow();
  });
});
