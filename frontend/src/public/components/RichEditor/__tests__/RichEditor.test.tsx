import * as React from 'react';
import { render, screen } from '@testing-library/react';
import { EExtraFieldType } from '../../../types/template';
import { RichEditor } from '..';
import type { IRichEditorHandle, IRichEditorProps } from '..';

jest.mock('../RichEditor', () => {
  const React = require('react');
  const ForwardRef = React.forwardRef((props: Record<string, unknown>, ref: React.Ref<unknown>) => {
    React.useImperativeHandle(ref, () => ({
      focus: jest.fn(),
      insertVariable: jest.fn(),
      getEditor: jest.fn(),
    }));
    return (
      <div data-testid="rich-editor-root" className={props.className as string}>
        {props.title != null ? <span>{String(props.title)}</span> : null}
        {props.children}
      </div>
    );
  });
  return { RichEditor: ForwardRef };
});

const defaultProps: IRichEditorProps = {
  placeholder: 'Placeholder',
  handleChange: jest.fn().mockResolvedValue(''),
  withToolbar: false,
  withMentions: false,
};

describe('RichEditor', () => {
  it('renders without crashing', () => {
    render(<RichEditor {...defaultProps} />);
    expect(screen.getByTestId('rich-editor-root')).toBeInTheDocument();
  });

  it('exposes focus, insertVariable, getEditor via ref', () => {
    const ref = React.createRef<IRichEditorHandle>();
    render(<RichEditor {...defaultProps} ref={ref} />);
    expect(ref.current).not.toBeNull();
    expect(typeof ref.current!.focus).toBe('function');
    expect(typeof ref.current!.insertVariable).toBe('function');
    expect(typeof ref.current!.getEditor).toBe('function');
  });

  it('renders title when provided', () => {
    render(<RichEditor {...defaultProps} title="Editor title" />);
    expect(screen.getByText('Editor title')).toBeInTheDocument();
  });

  it('applies custom className to root', () => {
    render(
      <RichEditor {...defaultProps} className="custom-editor-class" />,
    );
    const root = screen.getByTestId('rich-editor-root');
    expect(root).toHaveClass('custom-editor-class');
  });

  it('renders children', () => {
    render(
      <RichEditor {...defaultProps}>
        <span data-testid="editor-child">Child</span>
      </RichEditor>,
    );
    expect(screen.getByTestId('editor-child')).toHaveTextContent('Child');
  });

  it('insertVariable with empty strings does not throw', () => {
    const ref = React.createRef<IRichEditorHandle>();
    render(<RichEditor {...defaultProps} ref={ref} />);
    expect(() => {
      ref.current?.insertVariable('', '', '');
    }).not.toThrow();
  });

  it('getEditor is a function', () => {
    const ref = React.createRef<IRichEditorHandle>();
    render(<RichEditor {...defaultProps} ref={ref} />);
    expect(typeof ref.current?.getEditor).toBe('function');
  });

  it('focus can be called without throwing', () => {
    const ref = React.createRef<IRichEditorHandle>();
    render(<RichEditor {...defaultProps} ref={ref} />);
    expect(() => ref.current?.focus()).not.toThrow();
  });

  it('renders with defaultValue prop', () => {
    render(<RichEditor {...defaultProps} defaultValue="Initial text" />);
    expect(screen.getByTestId('rich-editor-root')).toBeInTheDocument();
  });

  it('accepts placeholder and passes it to root', () => {
    render(<RichEditor {...defaultProps} placeholder="Type here" />);
    expect(screen.getByTestId('rich-editor-root')).toBeInTheDocument();
  });

  it('accepts withToolbar and withChecklists props', () => {
    render(
      <RichEditor
        {...defaultProps}
        withToolbar
        withChecklists
      />,
    );
    expect(screen.getByTestId('rich-editor-root')).toBeInTheDocument();
  });

  it('insertVariable with valid args calls ref implementation', () => {
    const ref = React.createRef<IRichEditorHandle>();
    render(<RichEditor {...defaultProps} ref={ref} />);
    const insertVariable = ref.current!.insertVariable as jest.Mock;
    ref.current?.insertVariable('api_name', 'Title', 'Subtitle');
    expect(insertVariable).toHaveBeenCalledWith('api_name', 'Title', 'Subtitle');
  });

  it('does not render title when title is undefined', () => {
    render(<RichEditor {...defaultProps} />);
    expect(screen.queryByText('Editor title')).not.toBeInTheDocument();
  });

  it('renders with multiline prop', () => {
    render(<RichEditor {...defaultProps} multiline />);
    expect(screen.getByTestId('rich-editor-root')).toBeInTheDocument();
  });

  /**
   * Usage profiles from real usage in the project. Ensures all prop combinations
   * used by consumers are accepted and render without crashing.
   */
  describe('usage in project (prop combinations)', () => {
    it('modal: placeholder, handleChange, isModal (ReturnModal)', () => {
      const handleChange = jest.fn().mockResolvedValue('');
      render(
        <RichEditor
          placeholder="Return message"
          handleChange={handleChange}
          isModal
          withToolbar={false}
          withMentions={false}
        />,
      );
      expect(screen.getByTestId('rich-editor-root')).toBeInTheDocument();
    });

    it('field with value and upload: placeholder, defaultValue, handleChange, className, accountId (Field RichText)', () => {
      const handleChange = jest.fn().mockResolvedValue('');
      render(
        <RichEditor
          placeholder="Enter text"
          defaultValue="Initial"
          handleChange={handleChange}
          className="rich-editor"
          accountId={1}
          withToolbar={false}
          withMentions={false}
        />,
      );
      expect(screen.getByTestId('rich-editor-root')).toBeInTheDocument();
      expect(screen.getByTestId('rich-editor-root')).toHaveClass('rich-editor');
    });

    it('comment with submit/cancel: placeholder, defaultValue, handleChange, submitIcon, cancelIcon, onSubmit, onCancel, accountId (WorkflowLogTaskComment)', () => {
      const handleChange = jest.fn();
      const onSubmit = jest.fn();
      const onCancel = jest.fn();
      render(
        <RichEditor
          placeholder="Comment"
          defaultValue=""
          handleChange={handleChange}
          cancelIcon={<span>Cancel</span>}
          submitIcon={<span>Submit</span>}
          onCancel={onCancel}
          onSubmit={onSubmit}
          accountId={42}
          withToolbar={false}
          withMentions={false}
        />,
      );
      expect(screen.getByTestId('rich-editor-root')).toBeInTheDocument();
    });

    it('comment popup with submit: placeholder, handleChange, onSubmit, className, accountId (PopupCommentField)', () => {
      const handleChange = jest.fn();
      const onSubmit = jest.fn();
      render(
        <RichEditor
          placeholder="Add comment"
          handleChange={handleChange}
          onSubmit={onSubmit}
          className="editor"
          accountId={10}
          withToolbar={false}
          withMentions={false}
        />,
      );
      expect(screen.getByTestId('rich-editor-root')).toBeInTheDocument();
    });

    it('task description (full): ref, title, placeholder, defaultValue, handleChange, handleChangeChecklists, withChecklists, withToolbar, withMentions, mentions, templateVariables, accountId, children (TaskDescriptionEditor)', () => {
      const ref = React.createRef<IRichEditorHandle>();
      const handleChange = jest.fn().mockResolvedValue('');
      const handleChangeChecklists = jest.fn();
      const mentions = [{ id: 1, name: 'User One' }];
      const templateVariables: IRichEditorProps['templateVariables'] = [
        { apiName: 'var1', title: 'Variable 1', type: EExtraFieldType.Text },
      ];
      render(
        <RichEditor
          ref={ref}
          title="Task description"
          placeholder="Description placeholder"
          defaultValue=""
          handleChange={handleChange}
          handleChangeChecklists={handleChangeChecklists}
          withChecklists
          withToolbar
          withMentions
          mentions={mentions}
          templateVariables={templateVariables}
          accountId={5}
        >
          <span data-testid="variable-list">Variable list</span>
        </RichEditor>,
      );
      expect(screen.getByTestId('rich-editor-root')).toBeInTheDocument();
      expect(screen.getByText('Task description')).toBeInTheDocument();
      expect(screen.getByTestId('variable-list')).toHaveTextContent('Variable list');
      expect(ref.current).not.toBeNull();
    });
  });
});
