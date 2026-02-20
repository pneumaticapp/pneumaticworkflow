import React from 'react';
import classnames from 'classnames';
import * as Sentry from '@sentry/react';

import { TTaskVariable } from '../types';

import { variablesDecorator } from '../utils/variablesDecorator';
import { addVariableEntityToEditor } from '../utils/addVariableEntityToEditor';
import { escapeMarkdown } from '../../../utils/escapeMarkdown';
import { VariableList } from '../VariableList';
import { getInitialEditorState } from '../../RichEditor/utils/converters';
import { RichEditor, RichEditorContainer } from '../../RichEditor';

import styles from './InputWithVariables.css';

export interface IEditorWithVariablesProps {
  placeholder?: string;
  listVariables: TTaskVariable[];
  templateVariables: TTaskVariable[];
  value?: string;
  title?: string;
  className?: string;
  toolipText: string;
  foregroundColor?: React.ComponentProps<typeof RichEditor>['foregroundColor'];
  size?: 'xl' | 'lg';
  onChange: React.ComponentProps<typeof RichEditor>['handleChange'];
}
export const InputWithVariables: React.FC<IEditorWithVariablesProps> = ({
  placeholder,
  listVariables,
  templateVariables,
  value,
  className,
  title,
  toolipText,
  foregroundColor,
  size = 'lg',
  onChange,
}) => {
  const editor = React.useRef<RichEditor>(null);
  const formattedValue = escapeMarkdown(value);

  const handleInsertVariable = (apiName?: string) => (e: React.MouseEvent) => {
    e.stopPropagation();

    if (!editor.current) {
      return;
    }

    const newVariable = listVariables?.find((v) => v.apiName === apiName);
    if (!newVariable) {
      return;
    }

    try {
      editor.current.onChange(
        addVariableEntityToEditor(editor.current.state.editorState, {
          title: newVariable.title,
          subtitle: newVariable.subtitle,
          apiName: newVariable.apiName,
        }),
      );
    } catch (err) {
      Sentry.captureException(err, {
        tags: { feature: 'InputWithVariables.insertVariable' },
        extra: { apiName },
      });
    }
  };

  return (
    <RichEditorContainer
      ref={editor}
      title={title}
      placeholder={placeholder}
      initialState={getInitialEditorState(formattedValue, templateVariables)}
      handleChange={onChange}
      decorators={[variablesDecorator]}
      withToolbar={false}
      multiline={false}
      className={classnames(size === 'xl' ? styles['editor_xl'] : styles['editor_lg'], className)}
      foregroundColor={foregroundColor}
      stripPastedFormatting
    >
      <VariableList
        variables={listVariables}
        onVariableClick={handleInsertVariable}
        className={styles['variables']}
        tooltipText={toolipText}
        focusEditor={() => editor.current?.focus()}
      />
    </RichEditorContainer>
  );
};
