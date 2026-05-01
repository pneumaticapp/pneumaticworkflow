import React from 'react';

import classnames from 'classnames';
import { TTaskVariable } from '../types';
import { escapeMarkdown } from '../../../utils/escapeMarkdown';
import { VariableList } from '../VariableList';
import { RichEditor, type IRichEditorHandle, type IRichEditorProps } from '../../RichEditor';

import styles from './InputWithVariables.css';



export interface IEditorWithVariablesProps {
  placeholder?: string;
  listVariables: TTaskVariable[];
  templateVariables: TTaskVariable[];
  value?: string;
  title?: string;
  className?: string;
  toolipText: string;
  foregroundColor?: IRichEditorProps['foregroundColor'];
  onChange: IRichEditorProps['handleChange'];
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
  onChange,
}) => {
  const editorRef = React.useRef<IRichEditorHandle>(null);
  const lastEmittedValue = React.useRef<string | undefined>(value);

  const handleChange: IRichEditorProps['handleChange'] = React.useCallback(
    (markdown: string) => {
      lastEmittedValue.current = markdown;

      return onChange(markdown);
    },
    [onChange],
  );

  React.useEffect(() => {
    if (value !== lastEmittedValue.current) {
      lastEmittedValue.current = value;
      const formattedValue = escapeMarkdown(value);
      editorRef.current?.replaceContent(formattedValue ?? '');
    }
  }, [value]);

  const handleInsertVariable = (apiName?: string) => (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!editorRef.current || apiName == null) return;
    const newVariable = listVariables?.find((variable) => variable.apiName === apiName);
    editorRef.current.insertVariable(
      apiName,
      newVariable?.title ?? '',
      newVariable?.subtitle ?? '',
    );
  };

  return (
    <RichEditor
      ref={editorRef}
      title={title}
      placeholder={placeholder ?? ''}
      defaultValue={escapeMarkdown(value)}
      handleChange={handleChange}
      withToolbar={false}
      withMentions={false}
      multiline={false}
      className={classnames(className, styles['input-with-variables'])}
      foregroundColor={foregroundColor}
      stripPastedFormatting
      templateVariables={templateVariables}
    >
      <VariableList
        variables={listVariables}
        onVariableClick={handleInsertVariable}
        className={styles['variables']}
        tooltipText={toolipText}
        focusEditor={() => editorRef.current?.focus()}
      />
    </RichEditor>
  );
};
