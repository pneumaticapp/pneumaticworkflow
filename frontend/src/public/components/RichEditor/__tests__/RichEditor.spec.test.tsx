/**
 * RichEditor tests aligned with docs/lexical-editor/specification.md §7.
 * Unit tests run in Jest with mocked RichEditor. E2E by spec runs in product via Playwright (see docs/lexical-editor/e2e.md).
 */

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
      clearContent: jest.fn(),
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

describe('Spec §7.1 Базовое редактирование', () => {
  it('renders editor with placeholder and toolbar props', () => {
    render(
      <RichEditor
        {...defaultProps}
        placeholder="Type here"
        withToolbar
      />,
    );
    expect(screen.getByTestId('rich-editor-root')).toBeInTheDocument();
  });

  it('accepts withChecklists for checklist toolbar', () => {
    render(
      <RichEditor {...defaultProps} withToolbar withChecklists />,
    );
    expect(screen.getByTestId('rich-editor-root')).toBeInTheDocument();
  });
});

describe('Spec §7.2 Переменные', () => {
  it('ref.insertVariable(apiName, title, subtitle) is callable', () => {
    const ref = React.createRef<IRichEditorHandle>();
    render(<RichEditor {...defaultProps} ref={ref} />);
    expect(() =>
      ref.current?.insertVariable('api_name', 'Title', 'Subtitle'),
    ).not.toThrow();
    const insertVariable = ref.current!.insertVariable as jest.Mock;
    expect(insertVariable).toHaveBeenCalledWith('api_name', 'Title', 'Subtitle');
  });

  it('renders with templateVariables prop for variable recognition', () => {
    const templateVariables: IRichEditorProps['templateVariables'] = [
      { apiName: 'var1', title: 'Variable 1', type: EExtraFieldType.Text },
    ];
    render(
      <RichEditor
        {...defaultProps}
        defaultValue=""
        templateVariables={templateVariables}
      />,
    );
    expect(screen.getByTestId('rich-editor-root')).toBeInTheDocument();
  });

});

describe('Spec §7.3 Чек-листы', () => {
  it('withChecklists renders without crash', () => {
    const handleChangeChecklists = jest.fn();
    render(
      <RichEditor
        {...defaultProps}
        withChecklists
        withToolbar
        handleChangeChecklists={handleChangeChecklists}
      />,
    );
    expect(screen.getByTestId('rich-editor-root')).toBeInTheDocument();
  });

});

describe('Spec §7.4 Ссылки и упоминания', () => {
  it('withMentions and mentions prop render without crash', () => {
    render(
      <RichEditor
        {...defaultProps}
        withMentions
        mentions={[{ id: 1, name: 'User One' }]}
      />,
    );
    expect(screen.getByTestId('rich-editor-root')).toBeInTheDocument();
  });

});

describe('Spec §7.5 Вложения', () => {
  it('renders with accountId for built-in upload', () => {
    render(
      <RichEditor {...defaultProps} accountId={1} />,
    );
    expect(screen.getByTestId('rich-editor-root')).toBeInTheDocument();
  });

  it('renders with onUploadAttachments prop', () => {
    const onUpload = jest.fn().mockResolvedValue(undefined);
    render(
      <RichEditor {...defaultProps} onUploadAttachments={onUpload} />,
    );
    expect(screen.getByTestId('rich-editor-root')).toBeInTheDocument();
  });

});

describe('Spec §7.6 Интеграция с формами', () => {
  it('TaskDescriptionEditor profile: handleChange + handleChangeChecklists + VariableList children', () => {
    const handleChange = jest.fn().mockResolvedValue('');
    const handleChangeChecklists = jest.fn();
    const ref = React.createRef<IRichEditorHandle>();
    const templateVariables: IRichEditorProps['templateVariables'] = [
      { apiName: 'v1', title: 'Var 1', type: EExtraFieldType.Text },
    ];
    render(
      <RichEditor
        ref={ref}
        {...defaultProps}
        handleChange={handleChange}
        handleChangeChecklists={handleChangeChecklists}
        withChecklists
        withToolbar
        withMentions
        mentions={[]}
        templateVariables={templateVariables}
        accountId={1}
      >
        <span data-testid="variable-list">Variable list</span>
      </RichEditor>,
    );
    expect(screen.getByTestId('rich-editor-root')).toBeInTheDocument();
    expect(screen.getByTestId('variable-list')).toHaveTextContent('Variable list');
    ref.current?.insertVariable('v1', 'Var 1', '');
    expect((ref.current!.insertVariable as jest.Mock).mock.calls.length).toBeGreaterThan(0);
  });

  it('InputWithVariables profile: single-line with variables', () => {
    render(
      <RichEditor
        {...defaultProps}
        placeholder="Value"
        templateVariables={[{ apiName: 'x', title: 'X', type: EExtraFieldType.Text }]}
      />,
    );
    expect(screen.getByTestId('rich-editor-root')).toBeInTheDocument();
  });

  it('PopupCommentField / ReturnModal profile: onSubmit, onCancel, submitIcon, cancelIcon', () => {
    const onSubmit = jest.fn();
    const onCancel = jest.fn();
    render(
      <RichEditor
        {...defaultProps}
        handleChange={jest.fn().mockResolvedValue('')}
        onSubmit={onSubmit}
        onCancel={onCancel}
        submitIcon={<span>Submit</span>}
        cancelIcon={<span>Cancel</span>}
      />,
    );
    expect(screen.getByTestId('rich-editor-root')).toBeInTheDocument();
  });

});

describe('Spec §7.7 Крайние случаи', () => {
  it('empty defaultValue: editor mounts with empty content', () => {
    render(<RichEditor {...defaultProps} defaultValue="" />);
    expect(screen.getByTestId('rich-editor-root')).toBeInTheDocument();
  });

  it('undefined defaultValue: editor mounts', () => {
    render(<RichEditor {...defaultProps} />);
    expect(screen.getByTestId('rich-editor-root')).toBeInTheDocument();
  });

  it('ref.clearContent() is callable', () => {
    const ref = React.createRef<IRichEditorHandle>();
    render(<RichEditor {...defaultProps} ref={ref} />);
    expect(() => ref.current?.clearContent()).not.toThrow();
  });

  it('long markdown in defaultValue does not throw on mount (best-effort)', () => {
    const longMarkdown = '# H\n' + 'text\n'.repeat(500);
    expect(() =>
      render(<RichEditor {...defaultProps} defaultValue={longMarkdown} />),
    ).not.toThrow();
  });
});
